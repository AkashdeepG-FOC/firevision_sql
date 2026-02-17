import os
import sys
import cv2
import datetime
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class VideoPlayer(QMainWindow):
    """Standalone video player with timeline and thumbnails"""
    
    def __init__(self, video_path=None):
        super().__init__()
        
        self.video_path = video_path
        self.is_playing = False
        self.duration = 0
        self.thumbnails = []
        self.thumbnail_timestamps = []
        
        self.setWindowTitle("Video Player")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        
        if video_path:
            self.load_video(video_path)
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Video display area
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_widget, 1)
        
        # Timeline with thumbnails
        from recordings_page import VideoTimelineWidget, ThumbnailGenerator
        
        self.timeline = VideoTimelineWidget()
        self.timeline.position_changed.connect(self.seek_to_position)
        main_layout.addWidget(self.timeline)
        
        # Controls area
        controls_widget = QWidget()
        controls_widget.setStyleSheet("background-color: #181818;")
        controls_widget.setMinimumHeight(80)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(20, 10, 20, 10)
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("▶️")
        self.play_pause_btn.setFixedSize(50, 50)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                border-radius: 25px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        
        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_icon = QLabel("🔊")
        volume_icon.setStyleSheet("color: white; font-size: 16px;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        # Open file button
        open_btn = QPushButton("Open File")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        open_btn.clicked.connect(self.open_file)
        
        # Fullscreen button
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(40, 40)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        # Add widgets to controls layout
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.time_label)
        controls_layout.addStretch()
        controls_layout.addLayout(volume_layout)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(open_btn)
        controls_layout.addWidget(self.fullscreen_btn)
        
        main_layout.addWidget(controls_widget)
        
        # Initialize media player
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect signals
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.stateChanged.connect(self.update_player_state)
        
        # Initialize thumbnail generator
        self.thumbnail_generator = ThumbnailGenerator()
    
    def load_video(self, video_path):
        """Load a video file"""
        self.video_path = video_path
        self.setWindowTitle(f"Video Player - {os.path.basename(video_path)}")
        
        # Set media content
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(video_path))))
        self.media_player.setVolume(self.volume_slider.value())
        
        # Start playing
        self.media_player.play()
        self.is_playing = True
        
        # Generate thumbnails
        self.generate_thumbnails()
    
    def generate_thumbnails(self):
        """Generate thumbnails for the timeline"""
        if not self.video_path:
            return
            
        try:
            # Generate 10 thumbnails across the video
            thumbnails, timestamps = self.thumbnail_generator.generate_timeline_thumbnails(
                self.video_path, count=10
            )
            
            if thumbnails:
                self.thumbnails = thumbnails
                self.thumbnail_timestamps = timestamps
                self.timeline.set_thumbnails(thumbnails, timestamps)
        except Exception as e:
            print(f"Error generating thumbnails: {e}")
    
    def update_duration(self, duration):
        """Update the timeline with video duration"""
        self.duration = duration
        self.timeline.set_duration(duration)
        self.update_time_label()
    
    def update_position(self, position):
        """Update the timeline with current position"""
        self.timeline.set_position(position)
        self.update_time_label()
    
    def update_time_label(self):
        """Update the time display label"""
        position = self.media_player.position()
        duration = self.media_player.duration()
        
        position_str = self.format_time(position)
        duration_str = self.format_time(duration)
        
        self.time_label.setText(f"{position_str} / {duration_str}")
    
    def format_time(self, ms):
        """Format milliseconds to MM:SS format"""
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def seek_to_position(self, position):
        """Seek to position in milliseconds"""
        self.media_player.setPosition(position)
    
    def toggle_play_pause(self):
        """Toggle play/pause state"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.is_playing = False
        else:
            self.media_player.play()
            self.is_playing = True
    
    def update_player_state(self, state):
        """Update UI based on player state"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸️")
        else:
            self.play_pause_btn.setText("▶️")
    
    def set_volume(self, volume):
        """Set player volume"""
        self.media_player.setVolume(volume)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def open_file(self):
        """Open a video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv)"
        )
        
        if file_path:
            self.load_video(file_path)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close"""
        self.media_player.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set dark palette
    dark_palette = app.palette()
    dark_palette.setColor(QPalette.Window, QColor(18, 18, 18))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    # Check if a file was provided as argument
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    player = VideoPlayer(video_path)
    player.show()
    
    sys.exit(app.exec_())
