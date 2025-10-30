#!/usr/bin/env python
# coding: utf-8

# # Spotify Music Genre Classification
# 
# This notebook performs Music Genre Classification using Spotify data.
# We use numerical audio features like danceability, energy, tempo, loudness, etc.
# The target is the music genre. We will:
# 
# 1. Load and preprocess data
# 2. Perform exploratory data analysis (EDA)
# 3. Build a Neural Network using Keras + TensorFlow
# 4. Train and evaluate the model
# 5. Save model and predictions
# 

# In[3]:


#import libraries

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D, MaxPooling2D, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix


import pandas as pd
import numpy as np
import tensorflow as tf
print(pd.__version__, np.__version__, tf.__version__)


# In[4]:


#load dataset
df = pd.read_csv(r'C:\Users\Admin\Downloads\Spotify_Project\data\spotify_data.csv')

# Show first 5 rows
df.head()


# In[5]:


#Cleaning

# Dataset summary
df.info()

# Check missing values
print(df.isnull().sum())


# In[6]:


#Data PreProcessing

# Keeping only numeric features for model
numeric_features = df.select_dtypes(include=np.number).columns.tolist()
print("Numeric features:", numeric_features)

X = df[numeric_features]
y = df['genre']

# Encode target labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
y_categorical = to_categorical(y_encoded)

# Feature scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_categorical, test_size=0.2, random_state=42
)


# In[7]:


#Exploratory Data Analysis (EDA)

# Plot number of songs per genre
plt.figure(figsize=(10,5))
sns.countplot(x='genre', data=df, order=df['genre'].value_counts().index)
plt.title('Number of Songs per Genre')
plt.xticks(rotation=45)
plt.show()

# Correlation heatmap of numeric features
plt.figure(figsize=(12,8))
sns.heatmap(df[numeric_features].corr(), annot=True, cmap='coolwarm')
plt.title('Correlation Between Numeric Features')
plt.show()



# In[8]:


#Building Neural Network
model = Sequential()

# Input layer
model.add(Dense(128, input_dim=X_train.shape[1], activation='relu'))
model.add(Dropout(0.3))

# Hidden layers
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.3))
model.add(Dense(32, activation='relu'))

# Output layer
model.add(Dense(y_categorical.shape[1], activation='softmax'))

# Compile model
model.compile(
    loss='categorical_crossentropy',
    optimizer=Adam(learning_rate=0.001),
    metrics=['accuracy']
)

model.summary()


# In[ ]:


#Training Model

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)



# In[ ]:


#Evaluate Model
loss, accuracy = model.evaluate(X_test, y_test)
print(f'Test Accuracy: {accuracy*100:.2f}%')

# Plot training history
plt.figure(figsize=(12,5))

# Accuracy
plt.subplot(1,2,1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# Loss
plt.subplot(1,2,2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

plt.show()


# In[ ]:


#Predictions & Metrics
y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true_classes = np.argmax(y_test, axis=1)

# Confusion Matrix
cm = confusion_matrix(y_true_classes, y_pred_classes)
print("Confusion Matrix:\n", cm)

# Classification Report
print("\nClassification Report:\n")
print(classification_report(y_true_classes, y_pred_classes, target_names=le.classes_))


# In[ ]:


#Save Trained Model
model.save('outputs/spotify_genre_model.h5')
print("Model saved successfully!")


# In[ ]:


import os

# Make sure outputs folder exists
os.makedirs('outputs', exist_ok=True)

predictions_df = pd.DataFrame({
    'Actual_Genre': le.inverse_transform(np.argmax(y_test, axis=1)),
    'Predicted_Genre': le.inverse_transform(np.argmax(y_pred, axis=1))
})

# Save predictions to CSV
predictions_df.to_csv('outputs/spotify_genre_predictions.csv', index=False)
print("Predictions saved successfully!")


# In[ ]:


import os
print(os.getcwd())


# In[ ]:


import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

print("TensorFlow version:", tf.__version__)


# In[ ]:


#Example Predictions
# Take first 5 songs from test set
example_songs = X_test[:5]

# Predict genres
example_preds = model.predict(example_songs)
example_pred_classes = np.argmax(example_preds, axis=1)

# Map back to genre names
predicted_genres = le.inverse_transform(example_pred_classes)
actual_genres = le.inverse_transform(np.argmax(y_test[:5], axis=1))

print("Example Predictions:")
for i in range(len(example_songs)):
    print(f"Song {i+1}: Actual Genre = {actual_genres[i]}, Predicted Genre = {predicted_genres[i]}")


# In[ ]:


import joblib, json, os

os.makedirs("outputs", exist_ok=True)

# save scaler, label encoder and feature list
joblib.dump(scaler, "outputs/scaler.pkl")
joblib.dump(le, "outputs/label_encoder.pkl")
with open("outputs/features.json", "w") as f:
    json.dump(numeric_features, f)

# also save your trained model
model.save("outputs/spotify_genre_model.h5")


# # Conclusion
# 
# The model successfully classifies Spotify music genres with good accuracy.
# We have visualized model performance, evaluated predictions, and saved the model
# for future use. Further improvements can be made with feature engineering
# and hyperparameter tuning.
# 
