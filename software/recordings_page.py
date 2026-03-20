import os
import sys
import datetime
import threading
import cv2
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QMessageBox, QScrollArea, QGridLayout,
    QSlider, QFrame, QSizePolicy, QStackedWidget, QApplication,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import pyqtSignal, QUrl, Qt, QTimer, QSize, QThread, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QCursor, QPixmap, QImage, QPainter, QColor, QPen, QFont, QIcon, QLinearGradient, QBrush

# ─── Colour Palette ──────────────────────────────────────────────────────────
BG_DEEP    = "#09090b"   # page background
BG_CARD    = "#111115"   # card surface
BG_RAISED  = "#18181c"   # raised elements / inputs
BG_HEADER  = "#0f0f13"   # header bar
BORDER     = "#27272d"   # subtle border
BORDER_LT  = "#3f3f46"   # lighter border / divider
ACCENT     = "#e84040"   # brand red
ACCENT_DIM = "#7a1f1f"   # dimmed red for hovers
BLUE       = "#3b82f6"
BLUE_DIM   = "#1e40af"
GREEN      = "#10b981"
TEXT_PRI   = "#fafafa"
TEXT_SEC   = "#a1a1aa"
TEXT_MUTED = "#52525b"

CARD_STYLE = f"""
    QWidget {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
    }}
    QWidget:hover {{
        border: 1px solid {BORDER_LT};
    }}
"""

# ─── Thumbnail Thread ─────────────────────────────────────────────────────────
class ThumbnailGeneratorThread(QThread):
    thumbnail_ready = pyqtSignal(str, str)

    def __init__(self, video_path, output_path):
        super().__init__()
        self.video_path  = video_path
        self.output_path = output_path

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                return
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(total * 0.12)))
            ret, frame = cap.read()
            if ret:
                frame_resized = cv2.resize(frame, (320, 180))
                cv2.imwrite(self.output_path, frame_resized)
                self.thumbnail_ready.emit(self.video_path, self.output_path)
            cap.release()
        except Exception as e:
            print(f"Thumbnail error: {e}")


# ─── Recording Card ───────────────────────────────────────────────────────────
class ModernRecordingCard(QWidget):
    play_clicked   = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename      = filename
        self.video_path    = os.path.join("recordings", filename)
        self.thumbnail_path = None

        self.setFixedSize(300, 250)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self._setup_ui()
        self._generate_thumbnail()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Thumbnail ──────────────────────────────────
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(300, 168)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet(f"""
            QLabel {{
                background-color: #0a0a0d;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border: none;
                color: {TEXT_MUTED};
                font-size: 36px;
            }}
        """)
        self.thumb_label.setText("  ")   # placeholder — will be replaced by pixmap

        # Placeholder icon painted via a child label
        self._placeholder = QLabel(self.thumb_label)
        self._placeholder.setText("[ VIDEO ]")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setGeometry(0, 0, 300, 168)
        self._placeholder.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                color: {TEXT_MUTED};
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 3px;
                border: none;
            }}
        """)

        root.addWidget(self.thumb_label)

        # ── Info Strip ─────────────────────────────────
        info = QWidget()
        info.setFixedSize(300, 82)
        info.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_CARD};
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
                border: none;
            }}
        """)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(12, 8, 12, 10)
        info_layout.setSpacing(5)

        # File name (clean)
        raw   = os.path.splitext(self.filename)[0]
        name  = raw if len(raw) <= 34 else raw[:31] + "..."
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRI};
                font-size: 12px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        name_lbl.setToolTip(raw)

        # Bottom row: date  |  action buttons
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)

        date_lbl = QLabel(f"  {self._extract_date()}")
        date_lbl.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SEC};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)

        # ── Play button ────────────────────────────────
        self.play_btn = QPushButton("  Play")
        self.play_btn.setFixedHeight(26)
        self.play_btn.setMinimumWidth(64)
        self.play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background-color: #60a5fa; }}
            QPushButton:pressed {{ background-color: {BLUE_DIM}; }}
        """)
        self.play_btn.clicked.connect(lambda: self.play_clicked.emit(self.filename))

        # ── Delete button ──────────────────────────────
        self.del_btn = QPushButton("  Delete")
        self.del_btn.setFixedHeight(26)
        self.del_btn.setMinimumWidth(64)
        self.del_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_RAISED};
                color: {ACCENT};
                border: 1px solid {ACCENT_DIM};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
            QPushButton:pressed {{ background-color: {ACCENT_DIM}; }}
        """)
        self.del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.filename))

        row.addWidget(date_lbl, 1)
        row.addWidget(self.play_btn)
        row.addWidget(self.del_btn)

        info_layout.addWidget(name_lbl)
        info_layout.addLayout(row)
        root.addWidget(info)

    def _extract_date(self):
        try:
            parts = self.filename.split('_')
            if len(parts) >= 4:
                date_part = parts[-2]
                time_part = parts[-1].split('.')[0]
                dt = datetime.datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S")
                return dt.strftime("%d %b %Y  %H:%M")
        except Exception:
            pass
        try:
            if os.path.exists(self.video_path):
                ts = os.path.getmtime(self.video_path)
                return datetime.datetime.fromtimestamp(ts).strftime("%d %b %Y  %H:%M")
        except Exception:
            pass
        return "Unknown date"

    def _generate_thumbnail(self):
        if not os.path.exists(self.video_path):
            return
        thumb_dir = "thumbnails"
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_name  = f"{os.path.splitext(self.filename)[0]}.jpg"
        self.thumbnail_path = os.path.join(thumb_dir, thumb_name)
        if os.path.exists(self.thumbnail_path):
            self._load_thumbnail()
            return
        self._thumb_thread = ThumbnailGeneratorThread(self.video_path, self.thumbnail_path)
        self._thumb_thread.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._thumb_thread.start()

    @pyqtSlot(str, str)
    def _on_thumbnail_ready(self, vp, tp):
        if vp == self.video_path:
            self._load_thumbnail()

    def _load_thumbnail(self):
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            px = QPixmap(self.thumbnail_path)
            if not px.isNull():
                scaled = px.scaled(300, 168, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.thumb_label.setPixmap(scaled)
                self._placeholder.hide()


# ─── Stat Pill ────────────────────────────────────────────────────────────────
def _make_stat_pill(label: str, value: str, color: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet(f"""
        QWidget {{
            background-color: {BG_RAISED};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}
    """)
    lay = QVBoxLayout(w)
    lay.setContentsMargins(16, 12, 16, 12)
    lay.setSpacing(2)

    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"color:{color}; font-size:22px; font-weight:800; background:transparent; border:none;")
    lbl_lbl = QLabel(label)
    lbl_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; font-weight:600; letter-spacing:1px; text-transform:uppercase; background:transparent; border:none;")
    lay.addWidget(val_lbl)
    lay.addWidget(lbl_lbl)
    return w


# ─── Video Player ─────────────────────────────────────────────────────────────
class InWindowVideoPlayer(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.setStyleSheet(f"QWidget {{ background-color: {BG_DEEP}; color: {TEXT_PRI}; }}")
        self._setup_ui()
        self._setup_player()
        self._load_video()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background:{BG_HEADER}; border-bottom:1px solid {BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        h_lay.setSpacing(16)

        back_btn = QPushButton("  Back to Recordings")
        back_btn.setFixedHeight(34)
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_RAISED};
                color: {TEXT_PRI};
                border: 1px solid {BORDER_LT};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {BORDER_LT}; color:white; }}
        """)
        back_btn.clicked.connect(self.back_clicked.emit)

        sep = QLabel("|")
        sep.setStyleSheet(f"color:{BORDER_LT}; border:none; background:transparent;")

        name_lbl = QLabel(self.video_name)
        name_lbl.setStyleSheet(f"color:{TEXT_SEC}; font-size:13px; font-weight:500; background:transparent; border:none;")

        h_lay.addWidget(back_btn)
        h_lay.addWidget(sep)
        h_lay.addWidget(name_lbl)
        h_lay.addStretch()
        root.addWidget(header)

        # ── Video widget ──────────────────────────────
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background:black;")
        root.addWidget(self.video_widget, 1)

        # ── Controls ──────────────────────────────────
        ctrl = QWidget()
        ctrl.setFixedHeight(72)
        ctrl.setStyleSheet(f"background:{BG_HEADER}; border-top:1px solid {BORDER};")
        c_lay = QHBoxLayout(ctrl)
        c_lay.setContentsMargins(20, 8, 20, 8)
        c_lay.setSpacing(14)

        # Play/Pause btn
        self.play_btn = QPushButton("  Play")
        self.play_btn.setFixedSize(80, 38)
        self.play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #f75656; }}
            QPushButton:pressed {{ background-color: {ACCENT_DIM}; }}
        """)
        self.play_btn.clicked.connect(self._toggle_play_pause)

        # Progress slider
        self.pos_slider = QSlider(Qt.Horizontal)
        self.pos_slider.setRange(0, 0)
        self.pos_slider.sliderMoved.connect(self._set_position)
        self.pos_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {BORDER_LT};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ACCENT};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
        """)

        self.time_lbl = QLabel("00:00 / 00:00")
        self.time_lbl.setStyleSheet(f"color:{TEXT_SEC}; font-size:12px; font-weight:600; background:transparent; border:none;")
        self.time_lbl.setFixedWidth(110)

        # Volume
        vol_lbl = QLabel("Vol")
        vol_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; background:transparent; border:none;")
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(70)
        self.vol_slider.setFixedWidth(90)
        self.vol_slider.setStyleSheet(self.pos_slider.styleSheet())
        self.vol_slider.valueChanged.connect(self._set_volume)

        c_lay.addWidget(self.play_btn)
        c_lay.addWidget(self.pos_slider, 1)
        c_lay.addWidget(self.time_lbl)
        c_lay.addWidget(vol_lbl)
        c_lay.addWidget(self.vol_slider)
        root.addWidget(ctrl)

    def _setup_player(self):
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_widget)
        self.player.stateChanged.connect(self._state_changed)
        self.player.positionChanged.connect(self._pos_changed)
        self.player.durationChanged.connect(self._dur_changed)
        self.player.error.connect(self._handle_error)

    def _load_video(self):
        if os.path.exists(self.video_path):
            url = QUrl.fromLocalFile(os.path.abspath(self.video_path))
            self.player.setMedia(QMediaContent(url))
            self.player.setVolume(self.vol_slider.value())
            self.player.play()
        else:
            QMessageBox.warning(self, "Error", f"File not found:\n{self.video_path}")

    def _toggle_play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _state_changed(self, state):
        self.play_btn.setText("  Pause" if state == QMediaPlayer.PlayingState else "  Play")

    def _pos_changed(self, pos):
        self.pos_slider.setValue(pos)
        self._update_time()

    def _dur_changed(self, dur):
        self.pos_slider.setRange(0, dur)
        self._update_time()

    def _set_position(self, pos):
        self.player.setPosition(pos)

    def _set_volume(self, vol):
        self.player.setVolume(vol)

    def _update_time(self):
        pos = self.player.position()
        dur = self.player.duration()
        self.time_lbl.setText(f"{self._fmt(pos)} / {self._fmt(dur)}")

    @staticmethod
    def _fmt(ms):
        s = int(ms / 1000)
        return f"{s//60:02d}:{s%60:02d}"

    def _handle_error(self, _):
        QMessageBox.critical(self, "Playback Error", self.player.errorString())

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)


# ─── Main Page ────────────────────────────────────────────────────────────────
class EnhancedRecordingsPage(QWidget):
    back_to_cameras = pyqtSignal()

    # Global stylesheet for the page
    _PAGE_STYLE = f"""
        QWidget {{
            background-color: {BG_DEEP};
            color: {TEXT_PRI};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: {BG_RAISED};
            width: 8px;
            border-radius: 4px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER_LT};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {TEXT_MUTED};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """

    def __init__(self, drive_manager=None):
        super().__init__()
        self.drive_manager        = drive_manager
        self.current_video_player = None
        self.setStyleSheet(self._PAGE_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        self.list_page = self._build_list_page()
        self.stack.addWidget(self.list_page)
        root.addWidget(self.stack)

        self.refresh_recordings_list()

    def _build_list_page(self):
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Top header bar ─────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(f"background:{BG_HEADER}; border-bottom:1px solid {BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
        h_lay.setSpacing(12)

        # Dot accent + title
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background:{ACCENT}; border-radius:5px; border:none;")

        title = QLabel("Recordings")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRI};
                font-size: 20px;
                font-weight: 800;
                letter-spacing: -0.5px;
                background: transparent;
                border: none;
            }}
        """)

        h_lay.addWidget(dot)
        h_lay.addSpacing(4)
        h_lay.addWidget(title)
        h_lay.addStretch()

        # Refresh button
        ref_btn = QPushButton("  Refresh")
        ref_btn.setFixedHeight(34)
        ref_btn.setMinimumWidth(100)
        ref_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ref_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_RAISED};
                color: {TEXT_SEC};
                border: 1px solid {BORDER_LT};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {BORDER_LT}; color: white; }}
        """)
        ref_btn.clicked.connect(self.refresh_recordings_list)

        # Back button
        back_btn = QPushButton("  Back to Cameras")
        back_btn.setFixedHeight(34)
        back_btn.setMinimumWidth(140)
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: #f75656; }}
            QPushButton:pressed {{ background-color: {ACCENT_DIM}; }}
        """)
        back_btn.clicked.connect(self.back_to_cameras.emit)

        h_lay.addWidget(ref_btn)
        h_lay.addWidget(back_btn)
        lay.addWidget(header)

        # ── Stat bar ───────────────────────────────────────────────────────────
        self.stat_bar = QWidget()
        self.stat_bar.setStyleSheet(f"background:{BG_DEEP}; border-bottom:1px solid {BORDER};")
        sb_lay = QHBoxLayout(self.stat_bar)
        sb_lay.setContentsMargins(24, 14, 24, 14)
        sb_lay.setSpacing(12)

        self.stat_total = _make_stat_pill("Total Recordings", "0", TEXT_PRI)
        self.stat_size  = _make_stat_pill("Folder Size", "0 MB", BLUE)
        self.stat_today = _make_stat_pill("Today", "0", GREEN)
        for w in [self.stat_total, self.stat_size, self.stat_today]:
            sb_lay.addWidget(w)
        sb_lay.addStretch()
        lay.addWidget(self.stat_bar)

        # ── Grid scroll area ───────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background:{BG_DEEP}; border:none;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(24, 24, 24, 24)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.grid_container)
        lay.addWidget(self.scroll, 1)

        return page

    # ─── Data ─────────────────────────────────────────────────────────────────
    def refresh_recordings_list(self):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        rec_dir = "recordings"
        os.makedirs(rec_dir, exist_ok=True)
        files = sorted(
            [f for f in os.listdir(rec_dir) if f.lower().endswith(('.mp4','.avi','.mkv','.mov'))],
            reverse=True
        )

        # Update stats
        self._update_stats(files, rec_dir)

        if not files:
            empty = QLabel("No recordings found")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_MUTED};
                    font-size: 16px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    background: transparent;
                    border: none;
                    padding: 80px;
                }}
            """)
            self.grid_layout.addWidget(empty, 0, 0, 1, 3)
            return

        COLS = 3
        for idx, fn in enumerate(files):
            card = ModernRecordingCard(fn)
            card.play_clicked.connect(self.play_recording)
            card.delete_clicked.connect(self.delete_recording)
            self.grid_layout.addWidget(card, idx // COLS, idx % COLS)

    def _update_stats(self, files, rec_dir):
        total = len(files)
        size_bytes = sum(
            os.path.getsize(os.path.join(rec_dir, f))
            for f in files if os.path.exists(os.path.join(rec_dir, f))
        )
        size_mb = size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"

        today = datetime.date.today().strftime("%Y%m%d")
        today_count = sum(1 for f in files if today in f)

        # Refresh stat pill values
        def _set_val(pill, val):
            lbl = pill.layout().itemAt(0).widget()
            if lbl:
                lbl.setText(str(val))

        _set_val(self.stat_total, total)
        _set_val(self.stat_size,  size_str)
        _set_val(self.stat_today, today_count)

    # ─── Actions ──────────────────────────────────────────────────────────────
    def play_recording(self, filename):
        video_path = os.path.join("recordings", filename)
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Not Found", f"Recording not found:\n{filename}")
            self.refresh_recordings_list()
            return

        self.current_video_player = InWindowVideoPlayer(video_path)
        self.current_video_player.back_clicked.connect(self._return_to_list)
        self.stack.addWidget(self.current_video_player)
        self.stack.setCurrentWidget(self.current_video_player)

    def _return_to_list(self):
        if self.current_video_player:
            if hasattr(self.current_video_player, 'player'):
                self.current_video_player.player.stop()
            self.stack.removeWidget(self.current_video_player)
            self.current_video_player.setParent(None)
            self.current_video_player = None
        self.stack.setCurrentWidget(self.list_page)
        self.refresh_recordings_list()

    def delete_recording(self, filename):
        reply = QMessageBox.question(
            self, "Delete Recording",
            f"Permanently delete this recording?\n\n{filename}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                vp = os.path.join("recordings", filename)
                if os.path.exists(vp):
                    os.remove(vp)
                tp = os.path.join("thumbnails", f"{os.path.splitext(filename)[0]}.jpg")
                if os.path.exists(tp):
                    os.remove(tp)
                self.refresh_recordings_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete:\n{e}")


# Alias for backwards compatibility
RecordingsPage = EnhancedRecordingsPage
