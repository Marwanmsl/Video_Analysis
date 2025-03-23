import os
import sys
import vlc
import time
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QListWidget, QSlider, QLabel, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt

VIDEO_FOLDER = "videos"
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Analysis")
        self.setGeometry(100, 100, 1080, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.video_path = None
        self.is_paused = False
        self.is_muted = False

        self.init_ui()
        self.load_video_list()

    def init_ui(self):
        layout = QHBoxLayout()

        # Left Panel
        left_panel = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Video")
        left_panel.addWidget(self.search_bar)

        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_video)
        left_panel.addWidget(search_btn)

        self.video_list = QListWidget()
        self.video_list.itemDoubleClicked.connect(self.on_video_select)
        left_panel.addWidget(self.video_list)

        add_video_btn = QPushButton("➕ Add Video")
        add_video_btn.clicked.connect(self.add_video)
        left_panel.addWidget(add_video_btn)

        layout.addLayout(left_panel)

        # Right Panel
        right_panel = QVBoxLayout()
        self.video_label = QLabel("Video Output Here")
        self.video_label.setStyleSheet("background-color: black; min-height: 400px;")
        right_panel.addWidget(self.video_label)

        self.seek_bar = QSlider(Qt.Orientation.Horizontal)
        self.seek_bar.setRange(0, 100)
        self.seek_bar.sliderReleased.connect(self.seek_video)
        right_panel.addWidget(self.seek_bar)

        controls = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        controls.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pause_video)
        self.pause_btn.setEnabled(False)
        controls.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        controls.addWidget(self.stop_btn)

        right_panel.addLayout(controls)

        audio_controls = QHBoxLayout()
        self.mute_btn = QPushButton("🔊 Mute")
        self.mute_btn.clicked.connect(self.toggle_mute)
        audio_controls.addWidget(self.mute_btn)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        audio_controls.addWidget(self.volume_slider)

        right_panel.addLayout(audio_controls)

        layout.addLayout(right_panel)
        self.setLayout(layout)

    def load_video_list(self):
        self.video_list.clear()
        videos = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith((".mp4", ".avi", ".mov", ".mkv"))]
        self.video_list.addItems(videos)

    def search_video(self):
        query = self.search_bar.text().strip().lower()
        if not query:
            QMessageBox.warning(self, "Warning", "Enter a video name to search")
            return

        matches = [self.video_list.item(i).text() for i in range(self.video_list.count()) if
                   query in self.video_list.item(i).text().lower()]
        self.video_list.clear()
        self.video_list.addItems(matches)

    def on_video_select(self):
        self.video_path = os.path.join(VIDEO_FOLDER, self.video_list.currentItem().text())
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)

    def play_video(self):
        if not self.video_path:
            return

        if self.is_paused:
            self.media_player.play()
            self.is_paused = False
        else:
            media = self.instance.media_new(self.video_path)
            self.media_player.set_media(media)
            self.media_player.set_xwindow(self.video_label.winId())
            self.media_player.play()

        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        threading.Thread(target=self.update_seek_bar, daemon=True).start()

    def pause_video(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.is_paused = True
            self.pause_btn.setText("▶ Resume")
        else:
            self.media_player.play()
            self.is_paused = False
            self.pause_btn.setText("⏸ Pause")

    def stop_video(self):
        self.media_player.stop()
        self.is_paused = False
        self.pause_btn.setText("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def add_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            file_name = os.path.basename(file_path)
            new_path = os.path.join(VIDEO_FOLDER, file_name)
            if not os.path.exists(new_path):
                os.rename(file_path, new_path)
                self.load_video_list()
            else:
                QMessageBox.critical(self, "Error", "Video already exists in the folder")

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.media_player.audio_toggle_mute()
        self.mute_btn.setText("🔇 Unmute" if self.is_muted else "🔊 Mute")

    def set_volume(self):
        self.media_player.audio_set_volume(self.volume_slider.value())

    def seek_video(self):
        if self.media_player.get_length() > 0:
            new_time = int((self.media_player.get_length() * self.seek_bar.value()) / 100)
            self.media_player.set_time(new_time)

    def update_seek_bar(self):
        while self.media_player.get_state() not in [vlc.State.Ended, vlc.State.Stopped]:
            length = self.media_player.get_length()
            if length > 0:
                current_time = self.media_player.get_time()
                self.seek_bar.setValue(int((current_time / length) * 100))
            time.sleep(0.5)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
