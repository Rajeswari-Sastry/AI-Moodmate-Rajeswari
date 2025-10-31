import streamlit as st
import cv2
import tempfile
from deepface import DeepFace
from moodmate_recommender import sp
import random
import pandas as pd

# -----------------------
# Streamlit Web App
# -----------------------
st.set_page_config(page_title="MoodMate", page_icon="🎵", layout="centered")
st.title("🎵 MoodMate - Emotion-Based Music Recommender")
st.write("Detect your mood and get personalized Spotify playlist suggestions instantly!")

# -----------------------
# Session State for Mood Tracker
# -----------------------
if "mood_counts" not in st.session_state:
    st.session_state.mood_counts = {
        "happy": 0, "sad": 0, "angry": 0, "neutral": 0,
        "fear": 0, "disgust": 0, "surprise": 0
    }

# Mood summary dictionary
mood_summary = {
    "happy": "You look cheerful and full of energy! Enjoy something upbeat 🎉",
    "sad": "You seem low today. Let’s lift your mood with gentle tunes 💙",
    "angry": "You appear a bit tense. Calm melodies might help you unwind 🌿",
    "neutral": "Balanced and relaxed — perfect time for smooth background music ☕",
    "fear": "A little anxious? Let’s find some calming tracks 🕊️",
    "disgust": "Reset your mood with positive energy 🌈",
    "surprise": "Something unexpected! Let’s keep the good vibes going ✨"
}

# -----------------------
# Spotify Recommendation Function for Streamlit
# -----------------------
def recommend_songs_streamlit(emotion):
    emotion_to_query = {
        "happy": "Happy Hits",
        "sad": "Sad Songs",
        "angry": "Calm Down",
        "fear": "Confidence Boost",
        "disgust": "Mood Booster",
        "neutral": "Chill Vibes",
        "surprise": "Sunny Day"
    }

    query = emotion_to_query.get(emotion.lower(), "Mood Booster")

    try:
        results = sp.search(q=query, type="playlist", limit=1)
        playlists = results.get("playlists", {}).get("items", [])

        if playlists:
            playlist = playlists[0]
            tracks = sp.playlist_items(playlist["id"], limit=5)
            track_list = [
                f"{t['track']['name']} by {t['track']['artists'][0]['name']}" 
                for t in tracks["items"]
            ]

            st.write(f"🎵 Suggested Playlist: {playlist['name']} (by {playlist['owner']['display_name']})")

            # Open in browser
            st.markdown(f"🔗 [Open in Browser]({playlist['external_urls']['spotify']})")

            # Open in Spotify desktop app (URI)
            st.markdown(f"🎧 [Open in Spotify App](spotify:playlist:{playlist['id']})")

            st.write("Sample Tracks:")
            for track in track_list:
                st.write(f"- {track}")
        else:
            st.warning("⚠️ No playlists found for this emotion.")
    except Exception as e:
        st.error(f"❌ Spotify API error: {e}")

# -----------------------
# Helper: update mood tracker
# -----------------------
def update_mood_tracker(emotion):
    if emotion.lower() in st.session_state.mood_counts:
        st.session_state.mood_counts[emotion.lower()] += 1
    else:
        st.session_state.mood_counts[emotion.lower()] = 1

# -----------------------
# Input options
# -----------------------
option = st.radio(
    "Choose input method:", 
    ["📸 Webcam", "📁 Upload Image", "✏️ Type Mood Manually"],
    key="input_method_radio"
)

# -----------------------
# Webcam Option
# -----------------------
if option == "📸 Webcam":
    st.info("Click 'Capture Emotion' to detect your mood via webcam.")
    if st.button("Capture Emotion", key="webcam_button"):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            st.error("Could not access webcam.")
        else:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(result, list):
                result = result[0]
            emotion = result['dominant_emotion']

            st.image(frame, channels="BGR", caption=f"Detected Emotion: {emotion}")
            st.success(f"Detected Emotion: {emotion.capitalize()}")
            st.info(mood_summary.get(emotion.lower(), "Here’s a playlist to match your current mood 🎧"))
            st.write("🎧 Spotify Recommendation:")
            recommend_songs_streamlit(emotion)
            update_mood_tracker(emotion)

# -----------------------
# Upload Image Option
# -----------------------
elif option == "📁 Upload Image":
    uploaded_file = st.file_uploader("Upload a face image", type=["jpg", "jpeg", "png"], key="upload_image")
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        image = cv2.imread(tmp_path)
        result = DeepFace.analyze(image, actions=['emotion'], enforce_detection=False)
        if isinstance(result, list):
            result = result[0]
        emotion = result['dominant_emotion']

        st.image(image, channels="BGR", caption=f"Detected Emotion: {emotion}")
        st.success(f"Detected Emotion: {emotion.capitalize()}")
        st.info(mood_summary.get(emotion.lower(), "Here’s a playlist to match your current mood 🎧"))
        st.write("🎧 Spotify Recommendation:")
        recommend_songs_streamlit(emotion)
        update_mood_tracker(emotion)

# -----------------------
# Manual Input Option
# -----------------------
# -----------------------
# Manual Input Option (NLP-style Text Detection)
# -----------------------
elif option == "✏️ Type Mood Manually":
    user_text = st.text_area("Describe how you feel (e.g., 'I had a great day!' or 'Feeling so tired...')", key="manual_input")

    if st.button("Detect Emotion & Get Playlist", key="manual_button"):
        if user_text.strip():
            # Simple NLP-style emotion detection using keywords
            emotion_keywords = {
                "happy": ["happy", "joy", "excited", "good", "great", "awesome", "love", "fun"],
                "sad": ["sad", "tired", "down", "depressed", "unhappy", "lonely"],
                "angry": ["angry", "mad", "furious", "irritated", "frustrated"],
                "fear": ["scared", "afraid", "worried", "nervous", "anxious"],
                "surprise": ["surprised", "amazed", "shocked", "wow"],
                "neutral": ["okay", "fine", "normal", "alright", "meh"]
            }

            detected_emotion = "neutral"
            for emotion, words in emotion_keywords.items():
                if any(word in user_text.lower() for word in words):
                    detected_emotion = emotion
                    break

            st.success(f"Detected Emotion: {detected_emotion.capitalize()}")
            st.info(mood_summary.get(detected_emotion, "Here’s a playlist to match your current mood 🎧"))
            st.write("🎧 Spotify Recommendation:")
            recommend_songs_streamlit(detected_emotion)
            update_mood_tracker(detected_emotion)

        else:
            st.warning("Please type something about how you feel!")

# -----------------------
# Mood Summary Tracker Chart
# -----------------------
st.markdown("---")
st.subheader("📊 Mood Summary Tracker")

mood_df = pd.DataFrame.from_dict(st.session_state.mood_counts, orient="index", columns=["Count"])
st.bar_chart(mood_df)

# Footer
st.caption("Developed with ❤️ By Rajeswari")
