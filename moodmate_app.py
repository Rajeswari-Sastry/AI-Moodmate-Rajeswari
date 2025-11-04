import streamlit as st
import cv2
import tempfile
from deepface import DeepFace
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials

# -----------------------
# Streamlit Setup
# -----------------------
st.set_page_config(page_title="MoodMate", page_icon="🎵", layout="centered")
st.markdown("<h1 style='text-align:center;'>🎵 MoodMate - Emotion-Based Music Recommender</h1>", unsafe_allow_html=True)
st.write("Detect your mood and get personalized Spotify playlist suggestions instantly!")

# -----------------------
# Spotify Credentials (Direct Access)
# -----------------------
CLIENT_ID = "5e0ac81611ed495aa3ce82ef99784eb1"
CLIENT_SECRET = "d8a7865568ed41dcac9415f2962cb8c9"

# Create Spotify client silently (no login or redirect)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# -----------------------
# Session State for Mood Tracker
# -----------------------
if "mood_counts" not in st.session_state:
    st.session_state.mood_counts = {
        "happy": 0, "sad": 0, "angry": 0, "neutral": 0,
        "fear": 0, "disgust": 0, "surprise": 0
    }

# -----------------------
# Mood Summary Messages
# -----------------------
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
# Spotify Playlist Recommender (with fallback)
# -----------------------
def recommend_songs_streamlit(emotion):
    emotion_to_query = {
        "happy": ["Happy Hits", "Good Vibes", "Upbeat Pop"],
        "sad": ["Sad Songs", "Emotional Ballads", "Soft Acoustic"],
        "angry": ["Calm Down", "Peaceful Piano", "Chill Tracks"],
        "fear": ["Confidence Boost", "Relax & Unwind", "Deep Focus"],
        "disgust": ["Mood Booster", "Feel Good Mix", "Daily Lift"],
        "neutral": ["Chill Vibes", "Lofi Beats", "Easy Listening"],
        "surprise": ["Sunny Day", "Pop Favourites", "Daily Mix"]
    }

    queries = emotion_to_query.get(emotion.lower(), ["Mood Booster"])
    playlist_found = False

    for query in queries:
        try:
            results = sp.search(q=query, type="playlist", limit=1)
            playlists = results.get("playlists", {}).get("items", [])

            if playlists:
                playlist_found = True
                playlist = playlists[0]
                playlist_name = playlist.get("name", "Unknown")
                playlist_owner = playlist.get("owner", {}).get("display_name", "Unknown")
                playlist_url = playlist.get("external_urls", {}).get("spotify", "")
                playlist_id = playlist.get("id", "")

                # Get top 5 tracks safely
                tracks_resp = sp.playlist_items(playlist_id, limit=5)
                track_list = [
                    f"{t['track']['name']} by {t['track']['artists'][0]['name']}"
                    for t in tracks_resp.get("items", [])
                    if t.get("track")
                ]

                st.markdown(f"### 🎧 Suggested Playlist: **{playlist_name}** (by {playlist_owner})")
                st.markdown(f"[🔗 Open in Browser]({playlist_url}) | [🎵 Open in Spotify App](spotify:playlist:{playlist_id})")

                if track_list:
                    st.write("**Sample Tracks:**")
                    for track in track_list:
                        st.write(f"- {track}")
                else:
                    st.info("No tracks found in this playlist.")
                break  # Stop after first successful playlist

        except Exception:
            continue  # Try next query if one fails

    if not playlist_found:
        st.warning("⚠️ Could not fetch a playlist right now. Showing a fallback mix instead.")
        st.markdown("[🎵 Open 'Today's Top Hits' on Spotify](https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M)")

# -----------------------
# Helper: Update Mood Tracker
# -----------------------
def update_mood_tracker(emotion):
    key = emotion.lower()
    st.session_state.mood_counts[key] = st.session_state.mood_counts.get(key, 0) + 1

# -----------------------
# Input Options
# -----------------------
option = st.radio(
    "Choose input method:",
    ["📸 Webcam", "📁 Upload Image", "✏️ Type Mood Manually"]
)

# -----------------------
# Webcam Input
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

            st.image(frame, channels="BGR", caption=f"Detected Emotion: {emotion.capitalize()}")
            st.success(f"Detected Emotion: {emotion.capitalize()}")
            st.info(mood_summary.get(emotion.lower(), "Here’s a playlist to match your mood 🎧"))
            recommend_songs_streamlit(emotion)
            update_mood_tracker(emotion)

# -----------------------
# Upload Image Input
# -----------------------
elif option == "📁 Upload Image":
    uploaded_file = st.file_uploader("Upload a face image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        image = cv2.imread(tmp_path)
        result = DeepFace.analyze(image, actions=['emotion'], enforce_detection=False)
        if isinstance(result, list):
            result = result[0]
        emotion = result['dominant_emotion']

        st.image(image, channels="BGR", caption=f"Detected Emotion: {emotion.capitalize()}")
        st.success(f"Detected Emotion: {emotion.capitalize()}")
        st.info(mood_summary.get(emotion.lower(), "Here’s a playlist to match your mood 🎧"))

        # Call recommender safely
        recommend_songs_streamlit(emotion)
        update_mood_tracker(emotion)

# -----------------------
# Manual Text Input
# -----------------------
elif option == "✏️ Type Mood Manually":
    user_text = st.text_area("Describe how you feel (e.g., 'I had a great day!' or 'Feeling tired...')")
    if st.button("Detect Emotion & Get Playlist"):
        if user_text.strip():
            emotion_keywords = {
                "happy": ["happy","joy","excited","good","great","awesome","love","fun"],
                "sad": ["sad","tired","down","depressed","unhappy","lonely"],
                "angry": ["angry","mad","furious","irritated","frustrated"],
                "fear": ["scared","afraid","worried","nervous","anxious"],
                "surprise": ["surprised","amazed","shocked","wow"],
                "neutral": ["okay","fine","normal","alright","meh"]
            }
            detected_emotion = "neutral"
            for emotion, words in emotion_keywords.items():
                if any(word in user_text.lower() for word in words):
                    detected_emotion = emotion
                    break

            st.success(f"Detected Emotion: {detected_emotion.capitalize()}")
            st.info(mood_summary.get(detected_emotion.lower(), "Here’s a playlist to match your mood 🎧"))
            recommend_songs_streamlit(detected_emotion)
            update_mood_tracker(detected_emotion)
        else:
            st.warning("Please type something about how you feel!")

# -----------------------
# Mood Tracker Chart
# -----------------------
st.markdown("---")
st.subheader("📊 Mood Summary Tracker")
mood_df = pd.DataFrame.from_dict(st.session_state.mood_counts, orient="index", columns=["Count"])
st.bar_chart(mood_df)

st.caption("<p style='text-align:center;'>Developed with ❤️ By Rajeswari</p>", unsafe_allow_html=True)
