import sys
import os
import json
import re
import requests
import webbrowser
from io import BytesIO
import pandas as pd
from PIL import Image, ImageFilter
import logging

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableView, QFileDialog, QMessageBox, QLabel, QHeaderView,
    QDialog, QProgressDialog, QMenuBar, QMenu, QStatusBar
)
from PyQt5.QtGui import (
    QStandardItemModel, QStandardItem, QPixmap, QImage, QPalette, QBrush
)
from PyQt5.QtCore import Qt, QEvent

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configure logging (optional)
logging.basicConfig(filename="app_debug.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

# Default credentials for local use (update these via Configure Credentials)
DEFAULT_CLIENT_ID = ""  # Set via Settings > Configure Credentials
DEFAULT_CLIENT_SECRET = ""
DEFAULT_REDIRECT_URI = "http://localhost:8888/callback"

CONFIG_FILE = "config.json"
RELEASE_NAME = "WeeWee1.0 The Big Release"

class StreamingHistoryViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Streaming History Viewer - {RELEASE_NAME}")
        self.setGeometry(100, 100, 1200, 700)
        self.client_id = DEFAULT_CLIENT_ID
        self.client_secret = DEFAULT_CLIENT_SECRET
        self.redirect_uri = DEFAULT_REDIRECT_URI
        self.sp_client = None
        self.full_df = pd.DataFrame()
        self.loadConfig()
        self.setupUI()
        self.showChangeLog()  # Show changelog window on launch
    
    def loadConfig(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.client_id = config.get("client_id", DEFAULT_CLIENT_ID)
                self.client_secret = config.get("client_secret", DEFAULT_CLIENT_SECRET)
            except Exception as e:
                logging.error(f"Error loading config: {e}")
    
    def saveConfig(self):
        config = {"client_id": self.client_id, "client_secret": self.client_secret}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def setupUI(self):
        # Create Menu Bar with File, Settings, and Help menus.
        menu_bar = QMenuBar(self)
        file_menu = QMenu("File", self)
        settings_menu = QMenu("Settings", self)
        help_menu = QMenu("Help", self)
        
        file_menu.addAction("Open Files", self.openFiles)
        file_menu.addAction("Clear Cache", self.clearCache)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        settings_menu.addAction("Configure Credentials", self.configureCredentials)
        
        help_menu.addAction("About", self.showAboutDialog)
        
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(settings_menu)
        menu_bar.addMenu(help_menu)
        self.setMenuBar(menu_bar)
        
        # Create Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.now_playing_label = QLabel("Now Playing: None")
        self.status_bar.addPermanentWidget(self.now_playing_label)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top control bar layout
        control_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search...")
        self.search_button = QPushButton("Search")
        self.clear_button = QPushButton("Clear")
        self.click_me_button = QPushButton("Click Me!")
        self.open_button = QPushButton("Open Files")
        self.playlist_button = QPushButton("Create Playlist")
        
        control_layout.addWidget(self.search_field)
        control_layout.addWidget(self.search_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.click_me_button)
        control_layout.addWidget(self.open_button)
        control_layout.addWidget(self.playlist_button)
        main_layout.addLayout(control_layout)
        
        # Table view for streaming history
        self.table_view = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Date/Time", "Song", "Creator", "Skipped", "Track URI"])
        self.table_view.setModel(self.model)
        self.table_view.setColumnHidden(4, True)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(self.table_view.SelectRows)
        self.table_view.setSelectionMode(self.table_view.SingleSelection)
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                gridline-color: gray;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
            }
            QTableView::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        self.table_view.setToolTip("Double-click or press the 'Play' button to start playback.\nRight-click to add to queue.\nMiddle-click to add to 'history' playlist.")
        
        # Right side: Thumbnail frame with playback and action buttons.
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table_view)
        self.thumbnail_frame = QWidget()
        self.thumbnail_frame.setFixedWidth(250)
        thumb_layout = QVBoxLayout(self.thumbnail_frame)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(200, 200)
        self.thumbnail_label.setStyleSheet("background-color: transparent;")
        self.thumbnail_label.setScaledContents(True)
        thumb_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignHCenter)
        
        # Playback buttons under thumbnail.
        playback_layout = QHBoxLayout()
        self.play_btn_thumb = QPushButton("Play")
        self.pause_btn_thumb = QPushButton("Pause")
        self.resume_btn_thumb = QPushButton("Resume")
        playback_layout.addWidget(self.play_btn_thumb)
        playback_layout.addWidget(self.pause_btn_thumb)
        playback_layout.addWidget(self.resume_btn_thumb)
        thumb_layout.addLayout(playback_layout)
        
        # Single-track actions: Queue and Add to Playlist.
        actions_layout = QHBoxLayout()
        self.queue_button = QPushButton("Queue")
        self.add_to_playlist_button = QPushButton("Add to Playlist")
        actions_layout.addWidget(self.queue_button)
        actions_layout.addWidget(self.add_to_playlist_button)
        thumb_layout.addLayout(actions_layout)
        
        content_layout.addWidget(self.thumbnail_frame)
        main_layout.addLayout(content_layout)
        
        # Connect signals for top controls.
        self.click_me_button.clicked.connect(self.clickMe)
        self.open_button.clicked.connect(self.openFiles)
        self.search_button.clicked.connect(self.search)
        self.clear_button.clicked.connect(self.clearSearch)
        self.playlist_button.clicked.connect(self.createPlaylist)
        
        # Connect signals for bottom playback/actions.
        self.play_btn_thumb.clicked.connect(self.playSelectedTrack)
        self.pause_btn_thumb.clicked.connect(self.pausePlayback)
        self.resume_btn_thumb.clicked.connect(self.resumePlayback)
        self.queue_button.clicked.connect(self.queueSelectedTrack)
        self.add_to_playlist_button.clicked.connect(self.addSelectedTrackToHistory)
        
        # Connect table row selection.
        self.table_view.clicked.connect(self.onRowSelect)
        self.table_view.doubleClicked.connect(self.playSelectedTrack)
    
    def showChangeLog(self):
        """Display a changelog dialog on launch."""
        changelog = (
            f"{RELEASE_NAME}\n\n"
            "Changelog:\n"
            "- Merged multiple JSON history files\n"
            "- Added playback controls (Play, Pause, Resume)\n"
            "- Added single-track actions: Queue and Add to Playlist\n"
            "- Right-click to queue; Middle-click to add to 'history' playlist\n"
            "- Configurable Spotify API credentials\n"
            "- Sorting, tooltips, and a fun 'Click Me!' button\n"
        )
        dialog = QDialog(self)
        dialog.setWindowTitle("Changelog")
        layout = QVBoxLayout(dialog)
        label = QLabel(changelog)
        label.setWordWrap(True)
        layout.addWidget(label)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.exec_()
    
    def showAboutDialog(self):
        QMessageBox.information(self, "About",
            f"WeeWee1.0 The Big Release\n\n"
            "Streaming History Viewer\n"
            "A multi-user Spotify playback control application.\n\n"
            "Features:\n"
            "- Load & merge multiple JSON history files\n"
            "- Playback, queue, and playlist creation controls\n"
            "- Configurable Spotify API credentials\n"
            "- Changelog on launch\n\n"
            "Enjoy!")
    
    def clickMe(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&autoplay=1"
        webbrowser.open(url)
    
    def clearCache(self):
        cache_file = ".cache-spotify"
        if os.path.exists(cache_file):
            os.remove(cache_file)
            self.sp_client = None
            QMessageBox.information(self, "Cache Cleared", "The Spotify token cache has been cleared.")
        else:
            QMessageBox.information(self, "No Cache Found", "No token cache was found.")
    
    def configureCredentials(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Spotify Credentials")
        layout = QVBoxLayout(dialog)
        
        cid_label = QLabel("Client ID:")
        self.cid_edit = QLineEdit()
        self.cid_edit.setText(self.client_id)
        cs_label = QLabel("Client Secret:")
        self.cs_edit = QLineEdit()
        self.cs_edit.setText(self.client_secret)
        self.cs_edit.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(cid_label)
        layout.addWidget(self.cid_edit)
        layout.addWidget(cs_label)
        layout.addWidget(self.cs_edit)
        
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addLayout(btn_layout)
        
        ok_button.clicked.connect(lambda: dialog.accept())
        cancel_button.clicked.connect(lambda: dialog.reject())
        
        if dialog.exec_() == QDialog.Accepted:
            self.client_id = self.cid_edit.text().strip()
            self.client_secret = self.cs_edit.text().strip()
            self.sp_client = None
            cache_file = ".cache-spotify"
            if os.path.exists(cache_file):
                os.remove(cache_file)
            self.saveConfig()
            QMessageBox.information(self, "Credentials Updated",
                                    "Your Spotify API credentials have been updated and cache cleared.")
    
    def get_sp_client(self):
        if self.sp_client is None:
            self.sp_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="playlist-modify-public user-modify-playback-state user-read-playback-state",
                show_dialog=True,
                cache_path=".cache-spotify"
            ))
        return self.sp_client
    
    def normalize_track_uri(self, uri):
        if uri.startswith("https://open.spotify.com/track/"):
            m = re.search(r'https://open\.spotify\.com/track/([A-Za-z0-9]+)', uri)
            if m:
                return f"spotify:track:{m.group(1)}"
        return uri
    
    def openFiles(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open JSON Files", "", "JSON Files (*.json);;All Files (*)"
        )
        if files:
            progress = QProgressDialog("Loading files...", "Cancel", 0, len(files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            all_data = []
            for i, file_path in enumerate(files):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load file {file_path}: {e}")
                progress.setValue(i + 1)
                if progress.wasCanceled():
                    break
            progress.close()
            if all_data:
                self.full_df = pd.DataFrame(all_data)
                columns_to_use = ["ts", "master_metadata_track_name", "master_metadata_album_artist_name", "spotify_track_uri", "skipped"]
                self.full_df = self.full_df[columns_to_use]
                self.full_df.rename(columns={
                    "ts": "Date/Time",
                    "master_metadata_track_name": "Song",
                    "master_metadata_album_artist_name": "Creator",
                    "spotify_track_uri": "Track URI",
                    "skipped": "Skipped"
                }, inplace=True)
                self.full_df["Date/Time"] = pd.to_datetime(self.full_df["Date/Time"], errors="coerce")
                self.full_df.sort_values("Date/Time", inplace=True)
                self.full_df.fillna("", inplace=True)
                self.populateTable(self.full_df)
                self.setWindowTitle(f"Streaming History Viewer - {len(files)} files loaded")
    
    def populateTable(self, df):
        self.model.removeRows(0, self.model.rowCount())
        for index, row in df.iterrows():
            track_uri = self.normalize_track_uri(row["Track URI"])
            item1 = QStandardItem(str(row["Date/Time"]))
            item1.setEditable(False)
            item2 = QStandardItem(row["Song"])
            item2.setEditable(False)
            item3 = QStandardItem(row["Creator"])
            item3.setEditable(False)
            skipped_val = "Yes" if row["Skipped"] else "No"
            item4 = QStandardItem(skipped_val)
            item4.setEditable(False)
            item5 = QStandardItem(track_uri)
            item5.setEditable(False)
            self.model.appendRow([item1, item2, item3, item4, item5])
    
    def search(self):
        query = self.search_field.text().strip()
        if query == "":
            return
        filtered = self.full_df[
            self.full_df["Song"].str.contains(query, case=False, na=False) |
            self.full_df["Creator"].str.contains(query, case=False, na=False)
        ]
        self.populateTable(filtered)
    
    def clearSearch(self):
        self.search_field.clear()
        self.populateTable(self.full_df)
    
    def onRowSelect(self, index):
        row = index.row()
        track_uri = self.model.item(row, 4).text()  # Hidden column
        track_uri = self.normalize_track_uri(track_uri)
        if track_uri.startswith("spotify:track:"):
            album_art, blurred = self.fetchAlbumArt(track_uri)
            if blurred:
                pix = self.pil2pixmap(blurred)
                self.setBackgroundPixmap(pix)
            if album_art:
                thumb_pix = self.pil2pixmap(album_art)
                self.thumbnail_label.setPixmap(thumb_pix)
                song = self.model.item(row, 1).text()
                self.now_playing_label.setText(f"Now Playing: {song}")
        else:
            self.setBackgroundPixmap(QPixmap())
            self.thumbnail_label.clear()
            self.now_playing_label.setText("Now Playing: None")
    
    def setBackgroundPixmap(self, pixmap):
        if not pixmap:
            pixmap = QPixmap()
        palette = self.centralWidget().palette()
        brush = QBrush(pixmap)
        palette.setBrush(self.centralWidget().backgroundRole(), brush)
        self.centralWidget().setPalette(palette)
        self.centralWidget().setAutoFillBackground(True)
    
    def playSelectedTrack(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Playback", "No row selected.")
            return
        row = selected_indexes[0].row()
        track_uri = self.model.item(row, 4).text()  # Hidden column
        track_uri = self.normalize_track_uri(track_uri)
        if not track_uri.startswith("spotify:track:"):
            QMessageBox.information(self, "Playback", "Invalid track URI.")
            return
        try:
            sp = self.get_sp_client()
            user_info = sp.current_user()
            product = user_info.get("product", "")
            if product and product.lower() != "premium":
                QMessageBox.critical(self, "Error", "Spotify Premium is required for playback.")
                return
            devices = sp.devices().get("devices", [])
            if not devices:
                QMessageBox.critical(self, "Error", "No active Spotify devices found. Please open Spotify on a device.")
                return
            device_id = devices[0]["id"]
            sp.add_to_queue(track_uri, device_id=device_id)
            sp.next_track(device_id=device_id)
            song = self.model.item(row, 1).text()
            self.now_playing_label.setText(f"Now Playing: {song}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Playback failed: {e}")
    
    def pausePlayback(self):
        try:
            sp = self.get_sp_client()
            sp.pause_playback()
            self.now_playing_label.setText("Now Playing: Paused")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Pause failed: {e}")
    
    def resumePlayback(self):
        try:
            sp = self.get_sp_client()
            devices = sp.devices().get("devices", [])
            if not devices:
                QMessageBox.critical(self, "Error", "No active Spotify devices found.")
                return
            device_id = devices[0]["id"]
            sp.start_playback(device_id=device_id)
            self.now_playing_label.setText("Now Playing: Resumed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Resume failed: {e}")
    
    def queueSelectedTrack(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Queue", "No row selected.")
            return
        row = selected_indexes[0].row()
        track_uri = self.model.item(row, 4).text()
        track_uri = self.normalize_track_uri(track_uri)
        if not track_uri.startswith("spotify:track:"):
            QMessageBox.information(self, "Queue", "Invalid track URI.")
            return
        try:
            sp = self.get_sp_client()
            devices = sp.devices().get("devices", [])
            if not devices:
                QMessageBox.critical(self, "Error", "No active Spotify devices found.")
                return
            device_id = devices[0]["id"]
            sp.add_to_queue(track_uri, device_id=device_id)
            self.status_bar.showMessage("Track added to queue", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to queue track: {e}")
    
    def addSelectedTrackToHistory(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Playlist", "No row selected.")
            return
        row = selected_indexes[0].row()
        track_uri = self.model.item(row, 4).text()
        track_uri = self.normalize_track_uri(track_uri)
        if not track_uri.startswith("spotify:track:"):
            QMessageBox.information(self, "Playlist", "Invalid track URI.")
            return
        try:
            sp = self.get_sp_client()
            user_info = sp.current_user()
            user_id = user_info["id"]
            history_playlist = None
            playlists = sp.current_user_playlists(limit=50)
            for playlist in playlists["items"]:
                if playlist["name"].lower() == "history":
                    history_playlist = playlist
                    break
            if not history_playlist:
                history_playlist = sp.user_playlist_create(
                    user=user_id, name="history", public=True,
                    description="History playlist from the app"
                )
            sp.playlist_add_items(history_playlist["id"], [track_uri])
            self.status_bar.showMessage("Track added to 'history' playlist", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add track to 'history' playlist:\n{e}")
    
    def createPlaylist(self):
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Info", "No rows selected.")
            return
        track_uris = []
        dates = []
        for idx in selected:
            row = idx.row()
            track_uri = self.model.item(row, 4).text()  # Hidden column
            track_uri = self.normalize_track_uri(track_uri)
            date_time = self.model.item(row, 0).text()
            if track_uri.startswith("spotify:track:"):
                track_uris.append(track_uri)
                dates.append(date_time)
        if not track_uris:
            QMessageBox.information(self, "Info", "No valid tracks selected.")
            return
        track_uris = list(dict.fromkeys(track_uris))
        try:
            parsed_min = pd.to_datetime(min(dates), errors="coerce")
            parsed_max = pd.to_datetime(max(dates), errors="coerce")
            start_str = parsed_min.strftime("%Y-%m-%d") if pd.notnull(parsed_min) else "unknown"
            end_str = parsed_max.strftime("%Y-%m-%d") if pd.notnull(parsed_max) else "unknown"
        except Exception:
            start_str, end_str = "unknown", "unknown"
        playlist_name = f"Playlist {start_str} to {end_str}"
        try:
            sp = self.get_sp_client()
            user_id = sp.current_user()["id"]
            playlist = sp.user_playlist_create(
                user=user_id, name=playlist_name, public=True,
                description="Created from streaming history"
            )
            sp.playlist_add_items(playlist["id"], track_uris)
            QMessageBox.information(self, "Success", f"Playlist '{playlist_name}' created!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Playlist creation failed:\n{e}")
    
    def fetchAlbumArt(self, track_uri):
        sp = self.get_sp_client()
        track_id = track_uri.split(":")[-1]
        try:
            track_info = sp.track(track_id)
            images = track_info.get("album", {}).get("images", [])
            if images:
                image_url = images[0]["url"]
                response = requests.get(image_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                width, height = self.width(), self.height()
                blurred = img.copy().resize((width, height), Image.Resampling.LANCZOS)
                blurred = blurred.filter(ImageFilter.GaussianBlur(radius=15))
                blurred = blurred.convert("RGBA")
                overlay = Image.new("RGBA", blurred.size, (0, 0, 0, 80))
                blurred = Image.alpha_composite(blurred, overlay)
                blurred = blurred.convert("RGB")
                album_art = img.copy()
                album_art.thumbnail((200, 200), Image.Resampling.LANCZOS)
                return album_art, blurred
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error fetching album art:\n{e}")
        return None, None
    
    def pil2pixmap(self, im):
        im = im.convert("RGB")
        data = im.tobytes("raw", "RGB")
        qimg = QImage(data, im.size[0], im.size[1], QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StreamingHistoryViewer()
    window.show()
    sys.exit(app.exec_())
