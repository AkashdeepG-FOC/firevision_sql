import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QPalette, QColor

class StandaloneVideoPlayer(QMainWindow):
    """Standalone video player window"""
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        
        self.setWindowTitle(f"Video Player - {self.video_name}")
        self.setMinimumSize(800, 600)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1419;
                color: white;
            }
            QPushButton {
                background-color: #2a2d3a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3d4a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 6px;
                background: #4a4d5a;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #e74c3c;
                border: 1px solid #e74c3c;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        
        self.setup_ui()
        self.setup_media_player()
        self.load_video()
    
    def setup_ui(self):
        """Setup the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget, 1)
        
        # Controls
        controls = QWidget()
        controls.setFixedHeight(80)
        controls.setStyleSheet("background-color: #1a1d29; border-top: 1px solid #2a2d3a;")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(20, 10, 20, 10)
        
        # Play/Pause
        self.play_pause_btn = QPushButton("▶️")
        self.play_pause_btn.setFixedSize(50, 50)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 25px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #f75c4c;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Volume
        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("color: white; font-size: 16px;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # Fullscreen button
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(40, 40)
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.position_slider, 1)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.time_label)
        controls_layout.addStretch()
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(fullscreen_btn)
        
        layout.addWidget(controls)
    
    def setup_media_player(self):
        """Setup media player"""
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)
    
    def load_video(self):
        """Load video file"""
        if os.path.exists(self.video_path):
            url = QUrl.fromLocalFile(os.path.abspath(self.video_path))
            self.media_player.setMedia(QMediaContent(url))
            self.media_player.setVolume(70)
            self.media_player.play()
        else:
            QMessageBox.warning(self, "Error", f"Video file not found: {self.video_path}")
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def media_state_changed(self, state):
        """Handle media state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸️")
        else:
            self.play_pause_btn.setText("▶️")
    
    def position_changed(self, position):
        """Handle position changes"""
        self.position_slider.setValue(position)
        self.update_time_label()
    
    def duration_changed(self, duration):
        """Handle duration changes"""
        self.position_slider.setRange(0, duration)
        self.update_time_label()
    
    def set_position(self, position):
        """Set playback position"""
        self.media_player.setPosition(position)
    
    def set_volume(self, volume):
        """Set volume"""
        self.media_player.setVolume(volume)
    
    def update_time_label(self):
        """Update time display"""
        position = self.media_player.position()
        duration = self.media_player.duration()
        
        pos_str = self.format_time(position)
        dur_str = self.format_time(duration)
        
        self.time_label.setText(f"{pos_str} / {dur_str}")
    
    def format_time(self, ms):
        """Format time"""
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def toggle_fullscreen(self):
        """Toggle fullscreen"""
        was_playing = self.media_player.state() == QMediaPlayer.PlayingState
        self.media_player.pause()
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        # Re-set video output and resume playback
        self.media_player.setVideoOutput(self.video_widget)
        if was_playing:
            self.media_player.play()
    
    def handle_error(self, error):
        """Handle errors"""
        error_string = self.media_player.errorString()
        QMessageBox.critical(self, "Media Error", f"Error: {error_string}")
    
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close"""
        self.media_player.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if len(sys.argv) > 1:
        player = StandaloneVideoPlayer(sys.argv[1])
        player.show()
        sys.exit(app.exec_())
    else:
        print("Usage: python standalone_video_player.py <video_file>")
