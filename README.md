# 🎧 Spotify-History-Viewer

A PyQt5 desktop application for viewing and interacting with your Spotify streaming history.  
Supports search, playback, queueing, playlist creation, and album art display using the Spotify API.

---

## 🚀 Features

- Load and merge multiple Spotify JSON streaming history files
- Search and filter by song or artist
- Album art thumbnail with blurred background
- Playback controls (Play, Pause, Resume)
- Add songs to queue or to a custom "history" playlist
- Create new playlists from selected tracks (includes date range in name)
- Custom Spotify credentials configuration
- Clean UI with dark theme and interactive tooltips

---

## 🛠️ Installation

### Clone the Repository
```bash
git clone https://github.com/hg9001/Spotify-History-Viewer.git
cd Spotify-History-Viewer
```

### Install Dependencies
Make sure Python 3 is installed.

You can use the helper script:
```bash
chmod +x install.sh
./install.sh
```

Or manually:
```bash
pip install -r requirements.txt
```

---

## 🔐 Setting Up Spotify API Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in and click **"Create an App"**
3. Name it anything, and add a description
4. Under "Redirect URIs", add:
   ```
   http://localhost:8888/callback
   ```
5. Click "Save", then copy your **Client ID** and **Client Secret**
6. Run the app, then go to:
   - `Settings > Configure Credentials`
   - Paste in your Client ID and Secret
   - The app will save it in `config.json` for you

---

## 📥 How to Get Your Spotify Streaming History

1. Go to [Spotify Account Privacy Settings](https://www.spotify.com/account/privacy/)
2. Scroll down to **Download your data**
3. Click **Request data** under "Extended streaming history"
4. Wait for the email (can take a few days)
5. Download and unzip the `.zip` file
6. Open the app and go to **File > Open Files**, and select the `.json` files

---

## 💻 Running the App

You can launch it with:
```bash
python main.py
```

Or use the helper script:
```bash
./setup_and_run.sh
```

---

## 📂 Folder Structure

```
Spotify-History-Viewer/
├── main.py
├── streaming_viewer.py
├── install.sh
├── requirements.txt
├── README.md
└── config.json  # (auto-generated after setting credentials)
```

---

## 🧾 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤘 Made with ❤️ for personal streaming data nerds
