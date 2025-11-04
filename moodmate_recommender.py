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
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
    print("✅ Spotify authentication successful.")
except Exception as e:
    print(f"❌ Spotify authentication failed: {e}")
    sp = None

# -----------------------
# EMOTION TO PLAYLIST MAPPING
# -----------------------
emotion_playlists = {
    "happy": "Happy Hits",
    "sad": "Sad Songs",
    "angry": "Calm Down",
    "fear": "Confidence Boost",
    "disgust": "Mood Booster",
    "neutral": "Chill Vibes",
    "surprise": "Sunny Day"
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
    if not sp:
        print("❌ Spotify client not initialized properly.")
        return

    query = emotion_playlists.get(emotion.lower(), "Mood Booster")
    print(f"🔍 Searching Spotify for playlists related to: {query}")

    try:
        results = sp.search(q=query, type="playlist", limit=1)
        if not results or "playlists" not in results or not results["playlists"]["items"]:
            print("⚠️ No playlists found in Spotify search results.")
            return

        playlist = results["playlists"]["items"][0]
        print(f"🎧 Found playlist: {playlist['name']} by {playlist['owner']['display_name']}")

        tracks_resp = sp.playlist_items(playlist["id"], limit=5)
        if not tracks_resp or "items" not in tracks_resp:
            print("⚠️ No tracks found in playlist.")
            return

        track_list = []
        for item in tracks_resp["items"]:
            track = item.get("track")
            if track and "name" in track and "artists" in track:
                track_list.append(f"{track['name']} by {track['artists'][0]['name']}")

        if not track_list:
            track_list = ["No track details available."]

        show_playlist_popup(
            title=f"Recommended Playlist for {emotion.capitalize()} Mood",
            playlist_name=playlist.get("name", "Unknown"),
            owner=playlist.get("owner", {}).get("display_name", "Unknown"),
            tracks=track_list,
            spotify_url=playlist["external_urls"]["spotify"],
            spotify_uri=f"spotify:playlist:{playlist['id']}"
        )

    except spotipy.exceptions.SpotifyException as e:
        print(f"❌ Spotify authentication or permission error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Spotify API error: {e}")

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
    print(f"😀 Detected Emotion: {emotion}")
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
            print(f"😀 Detected Emotion: {emotion}")
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
