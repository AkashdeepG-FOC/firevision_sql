import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, 
                            QApplication, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QMovie, QColor

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class LoadingScreen(QWidget):
    """
    Professional loading screen widget that displays during application initialization.
    Features:
    - Modern dark theme matching the application
    - Animated GIF loading indicator
    - Status text updates
    - Smooth fade-in/fade-out animations
    - Maintains taskbar icon visibility
    """
    
    # Signal emitted when loading is complete
    loading_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_progress = 0
        self.movie = None
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Setup the loading screen UI"""
        # Window configuration
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set to fullscreen
        # Use same size as SplashScreen
        window_width = 1366
        window_height = 768
        
        self.setFixedSize(window_width, window_height)
        
        # Center the window
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.move(x, y)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)
        
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent;")
        # DO NOT use setScaledContents(True) — it re-scales every frame on top of
        # QMovie.setScaledSize(), causing double CPU scaling which freezes the GIF.
        self.gif_label.setFixedSize(window_width, window_height)

        # Load the GIF
        gif_path = resource_path(os.path.join("assests", "loading_screen.gif"))
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            # Cache all frames to reduce CPU decoding overhead during playback
            self.movie.setCacheMode(QMovie.CacheAll)
            self.movie.setSpeed(100)
            # Scale movie frames exactly once, to fit the screen
            self.movie.setScaledSize(QSize(window_width, window_height))
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.gif_label.setText("Loading...")
            self.gif_label.setStyleSheet("color: white; font-size: 24px;")
            print(f"Warning: Loading GIF not found at {gif_path}")
            
        layout.addWidget(self.gif_label)
        
    def setup_animations(self):
        """Setup fade-in and fade-out animations"""
        # Opacity effect for fade animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade-in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Fade-out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(500)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(self.on_fade_out_complete)
        
    def center_on_screen(self):
        """No longer needed as we are fullscreen, but kept for compatibility"""
        pass
        
    def show_with_fade(self):
        """Show the loading screen with fade-in animation"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.fade_in_animation.start()
        if self.movie:
            self.movie.start()
        
    def hide_with_fade(self):
        """Hide the loading screen with fade-out animation"""
        self.fade_out_animation.start()
        
    def on_fade_out_complete(self):
        """Called when fade-out animation completes"""
        if self.movie:
            self.movie.stop()
        self.hide()
        self.loading_complete.emit()
        
    def update_status(self, message, progress=None):
        """
        Update status - kept for compatibility but does nothing visually now
        except process events to keep UI responsive
        """
        # Process events to update UI
        QApplication.processEvents()
        
    def complete_loading(self):
        """Mark loading as complete and hide the screen"""
        QTimer.singleShot(500, self.hide_with_fade)


# Demo/Test code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    loading = LoadingScreen()
    loading.show_with_fade()
    
    # Simulate loading stages
    def simulate_loading():
        stages = [
            ("Loading configuration...", 20),
            ("Initializing camera systems...", 40),
            ("Loading AI models...", 60),
            ("Starting background services...", 80),
            ("Finalizing setup...", 95),
            ("Ready!", 100)
        ]
        
        for i, (message, progress) in enumerate(stages):
            QTimer.singleShot(i * 1000, lambda m=message, p=progress: loading.update_status(m, p))
        
        QTimer.singleShot(len(stages) * 1000, loading.complete_loading)
        QTimer.singleShot((len(stages) + 1) * 1000, app.quit)
    
    QTimer.singleShot(500, simulate_loading)
    
    sys.exit(app.exec_())
