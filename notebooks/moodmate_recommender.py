import time
import cv2
import argparse
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# -----------------------
# SPOTIFY CREDENTIALS
# -----------------------
CLIENT_ID = "5e0ac81611ed495aa3ce82ef99784eb1"
CLIENT_SECRET = "d8a7865568ed41dcac9415f2962cb8c9"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-library-read playlist-modify-private playlist-modify-public"

# Authenticate ONCE
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

# -----------------------
# EMOTION TO PLAYLIST MAPPING
# -----------------------
emotion_playlists = {
    "happy": ["Good Vibes", "Happy Hits", "Sunny Day"],
    "sad": ["Sad Songs", "Life Sucks", "Melancholy Vibes"],
    "angry": ["Calm Down", "Chill Vibes", "Peaceful Piano"],
    "neutral": ["Focus Playlist", "Deep Focus", "Chill Hits"],
    "surprise": ["Pop Surprises", "Unexpected Tunes"],
    "fear": ["Calm Anxiety", "Soothing Sounds"],
    "disgust": ["Mood Reset", "Positive Energy"]
}

# -----------------------
# FUNCTION: RECOMMEND SONGS
# -----------------------
def recommend_songs(emotion):
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
    print(f"🎵 Suggested Playlist: {query}")

    try:
        results = sp.search(q=query, type="playlist", limit=1)
        playlists = results.get("playlists", {}).get("items", [])

        if playlists:
            playlist = playlists[0]
            print(f"✅ Found Spotify playlist: {playlist['name']} (by {playlist['owner']['display_name']})")
            print(f"🔗 Playlist URL: {playlist['external_urls']['spotify']}")
        else:
            print("⚠️ No playlists found for that emotion. Try again with a different query.")

    except Exception as e:
        print(f"❌ Spotify API error: {e}")


# -----------------------
# FUNCTION: ONE-SHOT EMOTION DETECTION
# -----------------------
def detect_emotion_once():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()

    if not ret:
        print("❌ Failed to capture image from webcam.")
        return

    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
    if isinstance(result, list):
        result = result[0]

    emotion = result['dominant_emotion']
    recommend_songs(emotion)

# -----------------------
# FUNCTION: CONTINUOUS WEBCAM MODE
# -----------------------
def detect_emotion_webcam():
    cap = cv2.VideoCapture(0)
    last_detection_time = 0
    cooldown = 5  # seconds between detections

    print("\n📷 Webcam started. Press 'q' to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if time.time() - last_detection_time > cooldown:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(result, list):
                result = result[0]

            emotion = result['dominant_emotion']
            recommend_songs(emotion)
            last_detection_time = time.time()

        cv2.imshow("Webcam - Press Q to Exit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oneshot", action="store_true", help="Run in one-shot mode (detect once and exit)")
    parser.add_argument("--webcam", action="store_true", help="Run in continuous webcam mode")
    args = parser.parse_args()

    if args.oneshot:
        detect_emotion_once()
    else:
        detect_emotion_webcam()
