#!/usr/bin/env python3
"""
Voice Command System Test Script for FireVision Pro
This script tests the voice command functionality without running the full application.
"""

import sys
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

# Import voice command manager
try:
    from voice_command_manager import VoiceCommandManager, VoiceCommandWidget
    VOICE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Voice command system not available: {e}")
    VOICE_AVAILABLE = False

class TestWindow(QMainWindow):
    """Test window for voice commands"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FireVision Pro - Voice Command Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🎤 Voice Command System Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 14px; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Voice command widget
        if VOICE_AVAILABLE:
            self.voice_manager = VoiceCommandManager()
            self.voice_widget = VoiceCommandWidget(self.voice_manager)
            layout.addWidget(self.voice_widget)
            
            # Connect signals
            self.voice_manager.listening_started.connect(self.on_listening_started)
            self.voice_manager.listening_stopped.connect(self.on_listening_stopped)
            self.voice_manager.speech_recognized.connect(self.on_speech_recognized)
            self.voice_manager.command_detected.connect(self.on_command_detected)
            self.voice_manager.error_occurred.connect(self.on_error)
            self.voice_manager.voice_feedback.connect(self.on_voice_feedback)
        else:
            error_label = QLabel("❌ Voice command system not available")
            error_label.setStyleSheet("color: red; font-size: 14px; margin: 10px;")
            layout.addWidget(error_label)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        self.log_area.setStyleSheet("background-color: #f0f0f0; font-family: monospace;")
        layout.addWidget(self.log_area)
        
        # Test buttons
        if VOICE_AVAILABLE:
            test_layout = QVBoxLayout()
            
            test_btn = QPushButton("Test Voice Feedback")
            test_btn.clicked.connect(self.test_voice_feedback)
            test_layout.addWidget(test_btn)
            
            help_btn = QPushButton("Test Help Command")
            help_btn.clicked.connect(self.test_help_command)
            test_layout.addWidget(help_btn)
            
            status_btn = QPushButton("Test Status Command")
            status_btn.clicked.connect(self.test_status_command)
            test_layout.addWidget(status_btn)
            
            # Whisper test buttons
            whisper_btn = QPushButton("Switch to Whisper")
            whisper_btn.clicked.connect(self.test_whisper_switch)
            test_layout.addWidget(whisper_btn)
            
            google_btn = QPushButton("Switch to Google")
            google_btn.clicked.connect(self.test_google_switch)
            test_layout.addWidget(google_btn)
            
            whisper_status_btn = QPushButton("Test Whisper Status")
            whisper_status_btn.clicked.connect(self.test_whisper_status)
            test_layout.addWidget(whisper_status_btn)
            
            layout.addLayout(test_layout)
    
    def on_listening_started(self):
        """Called when voice listening starts"""
        self.status_label.setText("Status: Listening...")
        self.status_label.setStyleSheet("font-size: 14px; margin: 5px; color: green;")
        self.log_message("🎤 Voice listening started")
    
    def on_listening_stopped(self):
        """Called when voice listening stops"""
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("font-size: 14px; margin: 5px; color: red;")
        self.log_message("🔇 Voice listening stopped")
    
    def on_speech_recognized(self, text):
        """Called when speech is recognized"""
        self.log_message(f"🎤 Recognized: '{text}'")
    
    def on_command_detected(self, command_type, command_text):
        """Called when a command is detected"""
        self.log_message(f"✅ Command executed: '{command_text}'")
    
    def on_error(self, error):
        """Called when an error occurs"""
        self.log_message(f"❌ Error: {error}")
    
    def on_voice_feedback(self, text):
        """Called when voice feedback is given"""
        self.log_message(f"🔊 Voice feedback: '{text}'")
    
    def test_voice_feedback(self):
        """Test voice feedback functionality"""
        if VOICE_AVAILABLE:
            self.voice_manager.speak("Voice feedback test successful")
            self.log_message("🧪 Testing voice feedback...")
    
    def test_help_command(self):
        """Test help command"""
        if VOICE_AVAILABLE:
            self.voice_manager._handle_help("help")
            self.log_message("🧪 Testing help command...")
    
    def test_status_command(self):
        """Test status command"""
        if VOICE_AVAILABLE:
            self.voice_manager._handle_status("status")
            self.log_message("🧪 Testing status command...")
    
    def test_whisper_switch(self):
        """Test switching to Whisper"""
        if VOICE_AVAILABLE:
            self.voice_manager.switch_to_whisper()
            self.log_message("🧪 Switching to Whisper...")
    
    def test_google_switch(self):
        """Test switching to Google"""
        if VOICE_AVAILABLE:
            self.voice_manager.switch_to_google()
            self.log_message("🧪 Switching to Google...")
    
    def test_whisper_status(self):
        """Test Whisper status"""
        if VOICE_AVAILABLE:
            status = self.voice_manager.get_whisper_status()
            self.log_message(f"🧪 Whisper status: {status}")
    
    def log_message(self, message):
        """Add message to log area"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.ensureCursorVisible()

def test_voice_dependencies():
    """Test if voice command dependencies are available"""
    print("🔍 Testing voice command dependencies...")
    
    # Test SpeechRecognition
    try:
        import speech_recognition as sr
        print("✅ SpeechRecognition imported successfully")
        
        # Test microphone
        try:
            mic = sr.Microphone()
            print("✅ Microphone detected")
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            
    except ImportError as e:
        print(f"❌ SpeechRecognition not available: {e}")
        return False
    
    # Test pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("✅ pyttsx3 imported successfully")
        
        # Test voices
        voices = engine.getProperty('voices')
        print(f"✅ Found {len(voices)} available voices")
        
    except ImportError as e:
        print(f"❌ pyttsx3 not available: {e}")
        return False
    
    # Test PyAudio
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        print("✅ PyAudio imported successfully")
        
        # Test audio devices
        device_count = p.get_device_count()
        print(f"✅ Found {device_count} audio devices")
        
        p.terminate()
        
    except ImportError as e:
        print(f"❌ PyAudio not available: {e}")
        return False
    
    # Test OpenAI Whisper
    try:
        import whisper
        print("✅ OpenAI Whisper imported successfully")
        
        # Test model loading (small model for testing)
        print("📥 Testing Whisper model loading...")
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded successfully")
        
    except ImportError as e:
        print(f"⚠️ OpenAI Whisper not available: {e}")
        print("💡 Install with: pip install openai-whisper")
    except Exception as e:
        print(f"⚠️ Whisper model loading failed: {e}")
    
    print("✅ All voice command dependencies are available!")
    return True

def main():
    """Main test function"""
    print("🎤 FireVision Pro Voice Command Test")
    print("=" * 40)
    
    # Test dependencies first
    if not test_voice_dependencies():
        print("\n❌ Voice command dependencies are not properly installed.")
        print("Please run: python install_voice_dependencies.py")
        return
    
    print("\n🚀 Starting voice command test application...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create test window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 