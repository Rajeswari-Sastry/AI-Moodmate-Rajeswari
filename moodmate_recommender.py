import time
import cv2
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tkinter as tk
from PIL import Image, ImageTk
import webbrowser

# -----------------------
# SPOTIFY CREDENTIALS
# -----------------------
CLIENT_ID = "5e0ac81611ed495aa3ce82ef99784eb1"
CLIENT_SECRET = "d8a7865568ed41dcac9415f2962cb8c9"

# Authenticate without login or browser
try:
    auth_manager = SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("✅ Spotify connected successfully (no login required).")
except Exception as e:
    print(f"❌ Spotify connection failed: {e}")
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
# POPUP WINDOW
# -----------------------
def show_playlist_popup(emotion, playlist_name, tracks, spotify_url, spotify_uri):
    def open_spotify_url(event=None):
        webbrowser.open(spotify_url)

    def open_spotify_app(event=None):
        webbrowser.open(spotify_uri)

    root = tk.Tk()
    root.title("Rajeswari's MoodMate 🎧")
    root.geometry("460x550")
    root.configure(bg="#f4f6f8")
    root.attributes("-topmost", True)

    # --- Logo ---
    try:
        logo_img = Image.open("moodmate_logo.png")
        logo_img = logo_img.resize((90, 90))
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo, bg="#f4f6f8")
        logo_label.image = logo
        logo_label.pack(pady=8)
    except FileNotFoundError:
        tk.Label(root, text="🎧 Rajeswari's MoodMate", font=("Segoe UI", 16, "bold"),
                 bg="#f4f6f8", fg="#2b2b2b").pack(pady=12)

    # --- Mood Info ---
    tk.Label(root, text=f"😀 Detected Mood: {emotion.capitalize()}",
             font=("Segoe UI", 13, "bold"), bg="#f4f6f8", fg="#2b2b2b").pack(pady=5)

    tk.Label(root, text=f"Recommended Playlist: {playlist_name}",
             font=("Segoe UI", 11), bg="#f4f6f8").pack(pady=2)

    # --- Songs List ---
    songs_text = tk.Text(root, wrap="word", font=("Segoe UI", 10),
                         height=10, width=50, bg="white", relief="flat")
    songs_text.insert("1.0", "\n".join(tracks))
    songs_text.config(state="disabled")
    songs_text.pack(pady=15, padx=15)

    # --- Links Section ---
    tk.Label(root, text="🎵 Explore Playlist:", font=("Segoe UI", 11, "bold"),
             bg="#f4f6f8").pack(pady=(5, 2))

    browser_link = tk.Label(root, text="🌐 Open in Browser", fg="#1DB954", bg="#f4f6f8",
                            cursor="hand2", font=("Segoe UI", 10, "underline"))
    browser_link.pack(pady=2)
    browser_link.bind("<Button-1>", open_spotify_url)

    app_link = tk.Label(root, text="🎧 Open in Spotify App", fg="#1DB954", bg="#f4f6f8",
                        cursor="hand2", font=("Segoe UI", 10, "underline"))
    app_link.pack(pady=2)
    app_link.bind("<Button-1>", open_spotify_app)

    tk.Button(root, text="Close", command=root.destroy, bg="#d62828",
              fg="white", width=14, relief="flat").pack(pady=15)

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
        if not results or not results["playlists"]["items"]:
            print("⚠️ No playlists found.")
            return

        playlist = results["playlists"]["items"][0]
        tracks_resp = sp.playlist_items(playlist["id"], limit=5)

        track_list = []
        for item in tracks_resp["items"]:
            track = item.get("track")
            if track and "name" in track and "artists" in track:
                track_list.append(f"🎶 {track['name']} — {track['artists'][0]['name']}")

        if not track_list:
            track_list = ["No track details available."]

        show_playlist_popup(
            emotion=emotion,
            playlist_name=playlist.get("name", "Unknown"),
            tracks=track_list,
            spotify_url=playlist["external_urls"]["spotify"],
            spotify_uri=f"spotify:playlist:{playlist['id']}"
        )

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
    print(f"😀 Detected Emotion: {emotion}")
    recommend_songs(emotion)


# -----------------------
# CONTINUOUS WEBCAM MODE
# -----------------------
def detect_emotion_webcam():
    cap = cv2.VideoCapture(0)
    last_detection_time = 0
    cooldown = 5

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
    parser.add_argument("--oneshot", action="store_true", help="Run once")
    parser.add_argument("--webcam", action="store_true", help="Run continuous webcam mode")
    args = parser.parse_args()

    if args.oneshot:
        detect_emotion_once()
    else:
        detect_emotion_webcam()
