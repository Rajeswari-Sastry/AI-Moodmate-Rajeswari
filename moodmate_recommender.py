import time
import cv2
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
import webbrowser

# -----------------------
# SPOTIFY CREDENTIALS
# -----------------------
CLIENT_ID = "5e0ac81611ed495aa3ce82ef99784eb1"
CLIENT_SECRET = "d8a7865568ed41dcac9415f2962cb8c9"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-library-read playlist-modify-private playlist-modify-public"

# Authenticate with Spotify
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
# SHOW PLAYLIST POPUP
# -----------------------
def show_playlist_popup(title, playlist_name, owner, tracks, spotify_url, spotify_uri):
    def open_spotify_url():
        webbrowser.open(spotify_url)

    def open_spotify_app():
        webbrowser.open(spotify_uri)

    root = tk.Tk()
    root.title(title)
    root.geometry("400x400")
    root.attributes("-topmost", True)

    text = tk.Text(root, wrap="word")
    text.insert("1.0", f"🎵 Playlist: {playlist_name}\nBy: {owner}\n\nSample Tracks:\n" + "\n".join(tracks))
    text.config(state="disabled")
    text.pack(pady=10, padx=10, fill="both", expand=True)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Open in Browser", command=open_spotify_url, bg="lightblue").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Open in Spotify App", command=open_spotify_app, bg="lightgreen").pack(side="left", padx=5)

    tk.Button(root, text="Close", command=root.destroy).pack(pady=10)
    root.mainloop()

# -----------------------
# RECOMMEND SONGS
# -----------------------
def recommend_songs(emotion):
    query_map = {
        "happy": "Happy Hits",
        "sad": "Sad Songs",
        "angry": "Calm Down",
        "fear": "Confidence Boost",
        "disgust": "Mood Booster",
        "neutral": "Chill Vibes",
        "surprise": "Sunny Day"
    }
    query = query_map.get(emotion.lower(), "Mood Booster")

    try:
        results = sp.search(q=query, type="playlist", limit=1)
        playlists = results.get("playlists", {}).get("items", [])

        if playlists:
            playlist = playlists[0]
            tracks = sp.playlist_items(playlist["id"], limit=5)
            track_list = [f"{t['track']['name']} by {t['track']['artists'][0]['name']}" for t in tracks["items"]]

            show_playlist_popup(
                title=f"Recommended Playlist for {emotion.capitalize()} Mood",
                playlist_name=playlist["name"],
                owner=playlist["owner"]["display_name"],
                tracks=track_list,
                spotify_url=playlist['external_urls']['spotify'],
                spotify_uri=f"spotify:playlist:{playlist['id']}"
            )
        else:
            print("⚠️ No playlists found for that emotion.")
    except Exception as e:
        print(f"❌ Spotify API error: {e}")

# -----------------------
# ONE-SHOT EMOTION DETECTION
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
# CONTINUOUS WEBCAM MODE
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--oneshot", action="store_true", help="Run in one-shot mode (detect once and exit)")
    parser.add_argument("--webcam", action="store_true", help="Run in continuous webcam mode")
    args = parser.parse_args()

    if args.oneshot:
        detect_emotion_once()
    else:
        detect_emotion_webcam()
