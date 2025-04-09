# Spotify-History-Viewer

A PyQt5 app to view and interact with your Spotify streaming history.  
Supports search, playback, queueing, playlist creation, and album art display using the Spotify API.

## 🔐 Setup Your Own Spotify Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in and click **"Create an App"**.
3. Set the app name and description (anything is fine).
4. After the app is created:
   - Click on the app to open settings.
   - Add the following Redirect URI:  
     ```
     http://localhost:8888/callback
     ```
   - Click **Save**.

5. Note down your **Client ID** and **Client Secret**.

6. Run the app and go to **Settings > Configure Credentials** to paste your own Client ID and Secret.

---

## 📁 How to Get Your Spotify Streaming History

Spotify lets you request your full streaming history from your account:

1. Go to your [Spotify Privacy Settings](https://www.spotify.com/account/privacy/).
2. Scroll down to **Download your data**.
3. Click **Request Data** under **Extended streaming history**.
4. Spotify will email you a download link (can take a few days).
5. Download and unzip the data package.
6. Inside, you'll find one or more `.json` files (usually named like `StreamingHistory0.json`, etc).

---

## ▶️ How the Application Works

- Launch the app.
- Go to **File > Open Files** to load your `.json` streaming history files.
- The app merges and displays your history in a searchable table.
- Select tracks to:
  - **Play**, **Pause**, or **Resume** playback
  - **Queue** them on your active device
  - **Add to "history" playlist**
  - **Create a new playlist** from selected items (with automatic date range naming)
- When selecting a track, its album art is shown and blurred into the background.
- Right-click and middle-click support included for power users.
- Requires Spotify Premium to control playback.

---

## 💡 Notes

- Your Spotify credentials and token cache are stored locally.
- You can clear the cache from **File > Clear Cache** if needed.
- This app only reads `.json` history files and does not send or upload your data anywhere.

---

## 📦 Dependencies

Install with pip:
```bash
pip install PyQt5 spotipy pandas Pillow requests
