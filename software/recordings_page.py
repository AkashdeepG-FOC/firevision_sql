import os
import sys
import subprocess
import cv2
import datetime
import threading
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QHBoxLayout, QMessageBox, QScrollArea, QGridLayout, QSlider, QFrame,
    QDialog, QFileDialog, QSizePolicy, QStackedWidget, QApplication
)
from PyQt5.QtCore import pyqtSignal, QUrl, Qt, QTimer, QSize, QRect, QPoint, QThread, pyqtSlot
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QCursor, QPixmap, QImage, QPainter, QColor, QPen, QFont, QIcon

class ThumbnailGeneratorThread(QThread):
    """Thread for generating video thumbnails"""
    thumbnail_ready = pyqtSignal(str, str)  # video_path, thumbnail_path
    
    def __init__(self, video_path, output_path):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
    
    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                return
            
            # Get frame at 10% of video duration
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_pos = int(total_frames * 0.1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            ret, frame = cap.read()
            if ret:
                # Resize to card size
                frame_resized = cv2.resize(frame, (320, 180))
                cv2.imwrite(self.output_path, frame_resized)
                self.thumbnail_ready.emit(self.video_path, self.output_path)
            
            cap.release()
        except Exception as e:
            print(f"Error generating thumbnail: {e}")

class ModernRecordingCard(QWidget):
    """Modern recording card matching the reference design exactly"""
    
    play_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.video_path = os.path.join("recordings", filename)
        self.thumbnail_path = None
        
        self.setFixedSize(320, 240)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set the exact styling from the reference image
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d29;
                border: 1px solid #2a2d3a;
                border-radius: 12px;
                margin: 5px;
            }
            QWidget:hover {
                background-color: #1f2235;
                border: 1px solid #3a3d4a;
            }
        """)
        
        self.setup_ui()
        self.generate_thumbnail()
    
    def setup_ui(self):
        """Setup the card UI to match reference design exactly"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video thumbnail area (top part)
        self.thumbnail_widget = QWidget()
        self.thumbnail_widget.setFixedSize(320, 180)
        self.thumbnail_widget.setStyleSheet("""
            QWidget {
                background-color: #0f1419;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: none;
                margin: 0px;
            }
        """)
        
        thumbnail_layout = QVBoxLayout(self.thumbnail_widget)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                color: #666;
                font-size: 48px;
            }
        """)
        self.thumbnail_label.setText("\ud83d\udcf9")
        
        thumbnail_layout.addWidget(self.thumbnail_label)
        
        # Info section (bottom part)
        info_widget = QWidget()
        info_widget.setFixedSize(320, 60)
        info_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                margin: 0px;
            }
        """)
        
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(4)
        
        # Recording name
        name_text = self.get_clean_name()
        self.name_label = QLabel(name_text)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        # Bottom row with date and buttons
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        # Date with calendar icon
        date_str = self.extract_date_from_filename()
        self.date_label = QLabel(f"\ud83d\udcc5 {date_str}")
        self.date_label.setStyleSheet("""
            QLabel {
                color: #8a8a8a;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        
        # Action buttons container
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        
        # Play button (blue)
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(24, 24)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #5ba0f2;
            }
            QPushButton:pressed {
                background-color: #3a80d2;
            }
        """)
        self.play_btn.clicked.connect(lambda: self.play_clicked.emit(self.filename))
        
        # Delete button (red)
        self.delete_btn = QPushButton()
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #f75c4c;
            }
            QPushButton:pressed {
                background-color: #d73c2c;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.filename))
        
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.delete_btn)
        
        bottom_layout.addWidget(self.date_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(buttons_widget)
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(bottom_row)
        
        layout.addWidget(self.thumbnail_widget)
        layout.addWidget(info_widget)
    
    def get_clean_name(self):
        """Get clean recording name"""
        name = os.path.splitext(self.filename)[0]
        # Keep the format from reference: manual_recording_171e7e57
        return name
    
    def extract_date_from_filename(self):
        """Extract date from filename"""
        try:
            # Try to extract from filename pattern
            parts = self.filename.split('_')
            if len(parts) >= 4:
                date_part = parts[-2]
                time_part = parts[-1].split('.')[0]
                dt = datetime.datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S")
                return dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass
        
        # Fallback to file modification time
        try:
            if os.path.exists(self.video_path):
                ts = os.path.getmtime(self.video_path)
                return datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except:
            pass
        
        return "Unknown"
    
    def generate_thumbnail(self):
        """Generate thumbnail for the video"""
        if not os.path.exists(self.video_path):
            return
        
        # Create thumbnails directory
        thumb_dir = "thumbnails"
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)
        
        # Thumbnail path
        thumb_name = f"{os.path.splitext(self.filename)[0]}.jpg"
        self.thumbnail_path = os.path.join(thumb_dir, thumb_name)
        
        # Check if thumbnail already exists
        if os.path.exists(self.thumbnail_path):
            self.load_thumbnail()
            return
        
        # Generate thumbnail in background thread
        self.thumb_thread = ThumbnailGeneratorThread(self.video_path, self.thumbnail_path)
        self.thumb_thread.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumb_thread.start()
    
    @pyqtSlot(str, str)
    def on_thumbnail_ready(self, video_path, thumbnail_path):
        """Handle thumbnail generation completion"""
        if video_path == self.video_path:
            self.load_thumbnail()
    
    def load_thumbnail(self):
        """Load the generated thumbnail"""
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            pixmap = QPixmap(self.thumbnail_path)
            if not pixmap.isNull():
                # Scale to fit the thumbnail area
                scaled_pixmap = pixmap.scaled(
                    320, 180,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
                self.thumbnail_label.setStyleSheet("""
                    QLabel {
                        background-color: transparent;
                        border: none;
                    }
                """)
    
    def mousePressEvent(self, event):
        """Handle card click to play video"""
        # Only emit play_clicked if the click is on the play button, not the card itself
        if event.button() == Qt.LeftButton and event.x() >= 10 and event.x() < 290:
            self.play_clicked.emit(self.filename)
        super().mousePressEvent(event)

class VideoTimelineWidget(QWidget):
    """Enhanced timeline widget with thumbnail previews"""
    
    position_changed = pyqtSignal(int)  # Position in milliseconds
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.duration = 0
        self.position = 0
        self.thumbnails = []
        self.thumbnail_timestamps = []
        self.is_dragging = False
        self.hover_position = -1
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d29;
                border: 1px solid #2a2d3a;
                border-radius: 8px;
            }
        """)
        
        self.setMouseTracking(True)
    
    def set_duration(self, duration_ms):
        """Set video duration"""
        self.duration = max(1, duration_ms)
        self.update()
    
    def set_position(self, position_ms):
        """Set current position"""
        self.position = min(max(0, position_ms), self.duration)
        self.update()
    
    def set_thumbnails(self, thumbnail_paths, timestamps):
        """Set timeline thumbnails"""
        self.thumbnails = []
        self.thumbnail_timestamps = timestamps
        
        # Load thumbnail pixmaps
        for path in thumbnail_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(80, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.thumbnails.append(scaled)
                else:
                    # Create placeholder
                    placeholder = QPixmap(80, 45)
                    placeholder.fill(QColor(40, 40, 40))
                    self.thumbnails.append(placeholder)
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline"""
        if self.duration <= 0:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor(26, 29, 41))
        
        # Draw thumbnails
        if self.thumbnails:
            thumb_count = len(self.thumbnails)
            if thumb_count > 0:
                spacing = (width - 20) / thumb_count
                
                for i, pixmap in enumerate(self.thumbnails):
                    x = 10 + (spacing * i) + (spacing - pixmap.width()) / 2
                    y = 10
                    
                    # Draw thumbnail border
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                    painter.drawRect(int(x) - 1, int(y) - 1, pixmap.width() + 2, pixmap.height() + 2)
                    
                    # Draw thumbnail
                    painter.drawPixmap(int(x), int(y), pixmap)
        
        # Draw timeline track
        track_y = height - 25
        track_height = 4
        track_rect = QRect(10, track_y, width - 20, track_height)
        
        # Background track
        painter.fillRect(track_rect, QColor(60, 60, 60))
        
        # Progress track
        if self.duration > 0:
            progress_width = int((self.position / self.duration) * (width - 20))
            progress_rect = QRect(10, track_y, progress_width, track_height)
            painter.fillRect(progress_rect, QColor(231, 76, 60))
        
        # Position handle
        if self.duration > 0:
            handle_x = 10 + int((self.position / self.duration) * (width - 20))
            handle_rect = QRect(handle_x - 6, track_y - 4, 12, 12)
            painter.fillRect(handle_rect, QColor(231, 76, 60))
        
        # Hover indicator
        if self.hover_position >= 0 and not self.is_dragging:
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.DashLine))
            painter.drawLine(self.hover_position, 0, self.hover_position, height - 30)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.seek_to_position(event.x())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        self.hover_position = event.x()
        
        if self.is_dragging:
            self.seek_to_position(event.x())
        
        self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.hover_position = -1
        self.update()
    
    def seek_to_position(self, x_pos):
        """Seek to position based on x coordinate"""
        if self.duration <= 0:
            return
        
        # Account for margins
        effective_width = self.width() - 20
        relative_x = max(0, min(effective_width, x_pos - 10))
        
        ratio = relative_x / effective_width
        position_ms = int(ratio * self.duration)
        
        self.position = position_ms
        self.position_changed.emit(position_ms)
        self.update()

class InWindowVideoPlayer(QWidget):
    """In-window video player with timeline using QMediaPlayer"""
    back_clicked = pyqtSignal()

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.setStyleSheet("""
            QWidget {
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
            QPushButton:pressed {
                background-color: #4a4d5a;
            }
        """)
        self.setup_ui()
        self.setup_media_player()
        self.load_video()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #1a1d29; border-bottom: 1px solid #2a2d3a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        back_btn = QPushButton("← Back to Recordings")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f75c4c;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        title_label = QLabel(f"Playing: {self.video_name}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(back_btn)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addWidget(header)
        # Video display
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget, 1)
        # Controls
        controls = QWidget()
        controls.setFixedHeight(80)
        controls.setStyleSheet("background-color: #1a1d29; border-top: 1px solid #2a2d3a;")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(20, 10, 20, 10)
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
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 14px;")
        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("color: white; font-size: 16px;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.position_slider, 1)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.time_label)
        controls_layout.addStretch()
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider)
        layout.addWidget(controls)

    def setup_media_player(self):
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)

    def load_video(self):
        if os.path.exists(self.video_path):
            url = QUrl.fromLocalFile(os.path.abspath(self.video_path))
            self.media_player.setMedia(QMediaContent(url))
            self.media_player.setVolume(self.volume_slider.value())
            self.media_player.play()
        else:
            QMessageBox.warning(self, "Error", f"Video file not found: {self.video_path}")

    def toggle_play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸️")
        else:
            self.play_pause_btn.setText("▶️")

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_time_label()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_volume(self, volume):
        self.media_player.setVolume(volume)

    def update_time_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        pos_str = self.format_time(position)
        dur_str = self.format_time(duration)
        self.time_label.setText(f"{pos_str} / {dur_str}")

    def format_time(self, ms):
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"

    def handle_error(self, error):
        error_string = self.media_player.errorString()
        QMessageBox.critical(self, "Media Error", f"Error: {error_string}")

    def closeEvent(self, event):
        self.media_player.stop()
        super().closeEvent(event)

class EnhancedRecordingsPage(QWidget):
    """Enhanced recordings page matching the reference design"""
    
    back_to_cameras = pyqtSignal()
    
    def __init__(self, drive_manager=None):
        super().__init__()
        self.drive_manager = drive_manager
        self.current_video_player = None
        
        # Set the exact styling from reference
        self.setStyleSheet("""
            QWidget {
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
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2a2d3a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4d5a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a5d6a;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the recordings page UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Stacked widget for switching between recordings list and video player
        self.stacked_widget = QStackedWidget()
        
        # Recordings list page
        self.recordings_list_page = self.create_recordings_list_page()
        self.stacked_widget.addWidget(self.recordings_list_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Load recordings
        self.refresh_recordings_list()
    
    def create_recordings_list_page(self):
        """Create the recordings list page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header matching reference design
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Recordings")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: white;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # Back button matching reference
        back_btn = QPushButton("← Back to Cameras")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #f75c4c;
            }
        """)
        back_btn.clicked.connect(self.back_to_cameras.emit)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)
        
        # Recordings grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.recordings_container = QWidget()
        self.recordings_layout = QGridLayout(self.recordings_container)
        self.recordings_layout.setContentsMargins(0, 0, 0, 0)
        self.recordings_layout.setSpacing(20)
        self.recordings_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.recordings_container)
        layout.addWidget(self.scroll_area, 1)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5ba0f2;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_recordings_list)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(refresh_btn)
        
        layout.addLayout(bottom_layout)
        
        return page
    
    def refresh_recordings_list(self):
        """Refresh the recordings list"""
        # Clear existing cards
        for i in reversed(range(self.recordings_layout.count())):
            child = self.recordings_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get recordings
        recordings_dir = "recordings"
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)
        
        files = [f for f in os.listdir(recordings_dir) 
                if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov'))]
        
        if not files:
            # Show empty state
            empty_label = QLabel("No recordings found.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #8a8a8a;
                    font-size: 18px;
                    padding: 50px;
                }
            """)
            self.recordings_layout.addWidget(empty_label, 0, 0, 1, 3)
        else:
            # Add recording cards in grid (3 columns)
            cols = 3
            for idx, filename in enumerate(sorted(files, reverse=True)):
                row = idx // cols
                col = idx % cols
                
                card = ModernRecordingCard(filename)
                card.play_clicked.connect(self.play_recording)
                card.delete_clicked.connect(self.delete_recording)
                
                self.recordings_layout.addWidget(card, row, col)
    
    def play_recording(self, filename):
        """Play a recording"""
        video_path = os.path.join("recordings", filename)
        
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "File Not Found", 
                              f"Recording file not found:\n{filename}")
            self.refresh_recordings_list()
            return
        
        # Create in-window video player
        self.current_video_player = InWindowVideoPlayer(video_path)
        self.current_video_player.back_clicked.connect(self.return_to_recordings_list)
        
        # Add to stacked widget and switch to it
        self.stacked_widget.addWidget(self.current_video_player)
        self.stacked_widget.setCurrentWidget(self.current_video_player)
    
    def return_to_recordings_list(self):
        """Return to recordings list from video player"""
        if self.current_video_player:
            # Stop the video player
            if hasattr(self.current_video_player, 'media_player'):
                self.current_video_player.media_player.stop()
            
            # Remove from stacked widget
            self.stacked_widget.removeWidget(self.current_video_player)
            self.current_video_player.setParent(None)
            self.current_video_player = None
        
        # Switch back to recordings list
        self.stacked_widget.setCurrentWidget(self.recordings_list_page)
        
        # Refresh the list
        self.refresh_recordings_list()
    
    def delete_recording(self, filename):
        """Delete a recording"""
        reply = QMessageBox.question(
            self, "Delete Recording",
            f"Are you sure you want to delete this recording?\n\n{filename}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                video_path = os.path.join("recordings", filename)
                if os.path.exists(video_path):
                    os.remove(video_path)
                
                # Also remove thumbnail if exists
                thumb_path = os.path.join("thumbnails", f"{os.path.splitext(filename)[0]}.jpg")
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                
                self.refresh_recordings_list()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", 
                                  f"Could not delete recording:\n{str(e)}")

# At the end of the file, alias EnhancedRecordingsPage as RecordingsPage for compatibility
RecordingsPage = EnhancedRecordingsPage
