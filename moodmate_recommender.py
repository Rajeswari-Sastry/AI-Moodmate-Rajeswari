import time
import cv2
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tkinter as tk
from PIL import Image, ImageTk
import webbrowser
import threading
import queue
import sys

# -----------------------
# SPOTIFY CREDENTIALS
# -----------------------
CLIENT_ID = "5e0ac81611ed495aa3ce82ef99784eb1"
CLIENT_SECRET = "d8a7865568ed41dcac9415f2962cb8c9"

try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
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
# SAFE UI UPDATE QUEUE
# -----------------------
update_queue = queue.Queue()


# -----------------------
# POPUP THREAD
# -----------------------
class MoodPopup(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.root = None

    def run(self):
        self.root = tk.Tk()
        self.root.title("Rajeswari's MoodMate 🎧")
        self.root.geometry("460x580")
        self.root.configure(bg="#f4f6f8")
        self.root.attributes("-topmost", True)

        try:
            logo_img = Image.open("moodmate_logo.png").resize((90, 90))
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.root, image=self.logo, bg="#f4f6f8").pack(pady=8)
        except FileNotFoundError:
            tk.Label(self.root, text="🎧 Rajeswari's MoodMate", font=("Segoe UI", 16, "bold"),
                     bg="#f4f6f8", fg="#2b2b2b").pack(pady=12)

        self.mood_label = tk.Label(self.root, text="😀 Detected Mood: ---",
                                   font=("Segoe UI", 13, "bold"), bg="#f4f6f8", fg="#2b2b2b")
        self.mood_label.pack(pady=5)

        self.playlist_label = tk.Label(self.root, text="Recommended Playlist: ---",
                                       font=("Segoe UI", 11), bg="#f4f6f8")
        self.playlist_label.pack(pady=2)

        self.songs_text = tk.Text(self.root, wrap="word", font=("Segoe UI", 10),
                                  height=10, width=50, bg="white", relief="flat")
        self.songs_text.pack(pady=15, padx=15)

        self.browser_link = tk.Label(self.root, text="🌐 Open in Browser", fg="#1DB954", bg="#f4f6f8",
                                     cursor="hand2", font=("Segoe UI", 10, "underline"))
        self.browser_link.pack(pady=2)

        self.app_link = tk.Label(self.root, text="🎧 Open in Spotify App", fg="#1DB954", bg="#f4f6f8",
                                 cursor="hand2", font=("Segoe UI", 10, "underline"))
        self.app_link.pack(pady=2)

        tk.Label(self.root, text="Data Source: Spotify 🎵", font=("Segoe UI", 9, "italic"),
                 bg="#f4f6f8", fg="#555").pack(pady=(10, 0))

        tk.Button(self.root, text="Close", command=self.safe_close, bg="#d62828",
                  fg="white", width=14, relief="flat").pack(pady=15)

        self.root.after(100, self.check_updates)
        self.root.mainloop()

    def safe_close(self):
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def check_updates(self):
        while not update_queue.empty():
            emotion, playlist_name, tracks, spotify_url, spotify_uri = update_queue.get()
            self.mood_label.config(text=f"😀 Detected Mood: {emotion.capitalize()}")
            self.playlist_label.config(text=f"Recommended Playlist: {playlist_name}")
            self.songs_text.config(state="normal")
            self.songs_text.delete("1.0", tk.END)
            self.songs_text.insert("1.0", "\n".join(tracks))
            self.songs_text.config(state="disabled")
            self.browser_link.bind("<Button-1>", lambda e, url=spotify_url: webbrowser.open(url))
            self.app_link.bind("<Button-1>", lambda e, uri=spotify_uri: webbrowser.open(uri))
        self.root.after(100, self.check_updates)


# -----------------------
# SPOTIFY RECOMMENDER
# -----------------------
def recommend_songs(emotion):
    if not sp:
        return

    query = emotion_playlists.get(emotion.lower(), "Mood Booster")
    print(f"🔍 Searching Spotify for playlists related to: {query}")

    playlist = None
    for attempt in range(3):
        try:
            sp.auth_manager.get_access_token(as_dict=False)
            results = sp.search(q=query, type="playlist", limit=3)
            if results and results["playlists"]["items"]:
                playlist = results["playlists"]["items"][attempt % len(results["playlists"]["items"])]
                break
        except Exception as e:
            print(f"⚠️ Spotify search attempt {attempt+1} failed: {e}")
            time.sleep(2)

    if not playlist:
        update_queue.put((emotion, "Playlist Not Found",
                          ["⚠️ Could not fetch playlist."],
                          "https://open.spotify.com/", "spotify:app"))
        return

    playlist_name = playlist.get("name", f"{emotion.capitalize()} Playlist")
    print(f"🎧 Found playlist: {playlist_name}")

    tracks_resp = sp.playlist_items(playlist["id"], limit=5)
    tracks = []
    for item in tracks_resp["items"]:
        track = item.get("track")
        if track:
            tracks.append(f"🎶 {track['name']} — {track['artists'][0]['name']}")

    update_queue.put((emotion, playlist_name, tracks,
                      playlist["external_urls"]["spotify"],
                      f"spotify:playlist:{playlist['id']}"))


# -----------------------
# ONE-SHOT (Silent)
# -----------------------
def detect_emotion_once():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("❌ Failed to capture image from webcam.")
        return

    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
    if isinstance(result, list):
        result = result[0]
    emotion = result['dominant_emotion']
    print(f"😀 Detected Emotion: {emotion}")

    popup = MoodPopup()
    popup.start()
    threading.Thread(target=recommend_songs, args=(emotion,), daemon=True).start()

    # Wait until popup is closed before exiting
    for t in threading.enumerate():
        if isinstance(t, MoodPopup):
            t.join()

    print("✅ Exiting cleanly...")
    sys.exit(0)


# -----------------------
# CONTINUOUS (Silent Webcam)
# -----------------------
def detect_emotion_webcam():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    last_detection_time, cooldown, last_emotion = 0, 5, None

    popup = MoodPopup()
    popup.start()

    print("\n📷 Webcam running privately (no preview). Press Ctrl+C to stop.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Unable to read from webcam.")
                break

            if time.time() - last_detection_time > cooldown:
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                if isinstance(result, list):
                    result = result[0]

                emotion = result['dominant_emotion']

                if emotion != last_emotion:
                    print(f"😀 New Mood Detected: {emotion}")
                    threading.Thread(target=recommend_songs, args=(emotion,), daemon=True).start()
                    last_emotion = emotion
                else:
                    print(f"🙂 Mood unchanged: {emotion}")

                last_detection_time = time.time()

            # Privacy-safe: no preview window shown
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (Ctrl+C).")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        # Wait until popup window closes before exiting
        for t in threading.enumerate():
            if isinstance(t, MoodPopup):
                t.join()

        print("✅ Exiting cleanly...")
        sys.exit(0)


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--oneshot", action="store_true", help="Run once and exit")
    parser.add_argument("--webcam", action="store_true", help="Run continuous mode")
    args = parser.parse_args()

    if args.oneshot:
        detect_emotion_once()
    else:
        detect_emotion_webcam()
