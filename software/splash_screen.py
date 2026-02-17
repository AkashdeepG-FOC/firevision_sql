import sys
import time
import random
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import (
    QPixmap, QFont, QPainter, QColor, QLinearGradient,
    QBrush, QPen, QPolygon, QPainterPath
)
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QRectF


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SplashScreen(QSplashScreen):
    """Premium custom splash screen for Fire Vision Pro"""

    def __init__(self):
        pixmap = QPixmap(1366, 768)
        super().__init__(pixmap)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.progress = 0
        self.loading_text = "Initializing..."

        self.create_splash_design()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

    def create_splash_design(self):
        """Design the splash screen with premium styling and background image"""
        pixmap = QPixmap(1366, 768)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define the rounded path for the entire window
        window_path = QPainterPath()
        window_rect = QRectF(0, 0, 1366, 768)
        radius = 20.0  # The radius of the curve. Adjust as needed.
        window_path.addRoundedRect(window_rect, radius, radius)

        # Clip all subsequent drawing to this rounded path
        painter.setClipPath(window_path)

        # Step 1: Black base background
        painter.fillRect(window_rect, QBrush(QColor(0, 0, 0)))

        # Step 2: Draw background image with reduced opacity
        bg_path = resource_path("assests/bg.webp")
        bg_image = QPixmap(bg_path)  # Make sure the path is correct
        if not bg_image.isNull():
            scaled_bg = bg_image.scaled(1366, 768, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.setOpacity(0.25)  # Set opacity for background image
            painter.drawPixmap(0, 0, scaled_bg)
            painter.setOpacity(1.0)  # Reset opacity for further drawing

        # Step 3: Logo
        logo_path = resource_path("assests/logo1-white.png")
        logo = QPixmap(logo_path)
        scaled_logo = logo.scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap((1366 - scaled_logo.width()) // 2, 90, scaled_logo)

        # Step 4: Glowing title
        font = QFont("Segoe UI", 54, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 51, 51, 160), 4))
        painter.drawText(QRect(0, 180, 1366, 100), Qt.AlignCenter, "FIRE VISION PRO")
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawText(QRect(0, 180, 1366, 100), Qt.AlignCenter, "FIRE VISION PRO")

        # Step 5: Subtitle
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Segoe UI", 18)
        painter.setFont(font)
        painter.drawText(QRect(0, 300, 1366, 40), Qt.AlignCenter, "AI-Powered CCTV Surveillance System")

        # Step 6: Version
        painter.setPen(QPen(QColor(160, 160, 160)))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(QRect(0, 380, 1366, 30), Qt.AlignCenter, "Version 2.0 - Professional Edition")

        painter.end()
        self.setPixmap(pixmap)

    def draw_camera_icons(self, painter):
        """Draw left and right security camera icons"""
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.setBrush(QBrush(QColor(90, 90, 90)))

        # Left camera
        painter.drawRect(100, 250, 80, 50)
        painter.drawEllipse(110, 260, 30, 30)
        painter.drawRect(90, 300, 100, 12)
        for i in range(3):
            painter.drawLine(190, 260 + (i * 10), 220, 260 + (i * 10))

        # Right camera
        painter.drawRect(1186, 250, 80, 50)
        painter.drawEllipse(1206, 260, 30, 30)
        painter.drawRect(1176, 300, 100, 12)
        for i in range(3):
            painter.drawLine(1146, 260 + (i * 10), 1176, 260 + (i * 10))

    def show_with_progress(self):
        """Show splash screen and center it"""
        self.show()
        self.timer.start(100)
        self.move(
            QApplication.desktop().screen().rect().center() - self.rect().center()
        )
        return self

    def update_progress(self):
        """Simulate loading progress"""
        self.progress += 2
        if self.progress < 20:
            self.loading_text = "Initializing system..."
        elif self.progress < 40:
            self.loading_text = "Loading AI models..."
        elif self.progress < 60:
            self.loading_text = "Setting up camera manager..."
        elif self.progress < 80:
            self.loading_text = "Configuring background services..."
        elif self.progress < 95:
            self.loading_text = "Finalizing setup..."
        else:
            self.loading_text = "Ready to launch!"

        self.showMessage(
            f"{self.loading_text}\n\nLoading... {self.progress}%",
            Qt.AlignBottom | Qt.AlignCenter,
            QColor(255, 255, 255)
        )

        if self.progress >= 100:
            self.timer.stop()
            QTimer.singleShot(700, self.close)

    def drawContents(self, painter):
        """Draw the premium progress bar with curved corners"""
        if self.progress > 0:
            bar_rect = QRect(200, 620, 966, 8)
            radius = 4.0

            # Draw the background of the progress bar (a rounded rectangle)
            painter.setBrush(QColor(40, 40, 40))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, radius, radius)

            # Define the fill area based on progress
            fill_width = int((self.progress / 100) * bar_rect.width())
            fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_width, bar_rect.height())

            # Define the gradient for the fill
            gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            gradient.setColorAt(0, QColor(173, 216, 230))  # Light blue
            gradient.setColorAt(1, QColor(240, 248, 255))  # Alice blue

            # --- Use clipping to draw the filled part with rounded corners ---
            painter.save()
            # Create a rounded path that will be our clipping region
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(bar_rect), radius, radius)
            painter.setClipPath(clip_path)

            # Draw the progress fill; it will only be visible inside the clip path
            painter.fillRect(fill_rect, QBrush(gradient))

            # Restore the painter, removing the clip path
            painter.restore()

            # Draw the outer border of the progress bar
            painter.setPen(QPen(QColor(173, 216, 230), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(bar_rect, radius, radius)

        super().drawContents(painter)

def show_splash_screen():
    """Launch splash screen"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show_with_progress()
    app.processEvents()
    return splash


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = show_splash_screen()

    # Simulate loading
    start_time = time.time()
    while time.time() - start_time < 5:
        app.processEvents()
        time.sleep(0.05)

    splash.close()
    sys.exit()
