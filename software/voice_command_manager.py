import speech_recognition as sr
import pyttsx3
import threading
import time
import queue
import json
import os
import tempfile
import wave
import numpy as np
from typing import Dict, List, Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
import logging
from PyQt5.QtWidgets import QApplication # Added for QApplication.processEvents()
import difflib
from pydub import AudioSegment, effects, silence
import noisereduce as nr
import webrtcvad

# Whisper imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ OpenAI Whisper not available. Install with: pip install openai-whisper")

class VoiceCommandManager(QObject):
    """Comprehensive voice command system for FireVision Pro"""
    
    # Signals for voice command events
    command_detected = pyqtSignal(str, str)  # command_type, command_text
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    speech_recognized = pyqtSignal(str)  # recognized_text
    error_occurred = pyqtSignal(str)  # error_message
    voice_feedback = pyqtSignal(str)  # feedback_text
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        
        # Whisper model
        self.whisper_model = None
        self.use_whisper = WHISPER_AVAILABLE
        if self.use_whisper:
            self._load_whisper_model()
        
        # Voice command state
        self.is_listening = False
        self.is_enabled = False
        self.wake_word = "fire vision"
        self.wake_word_detected = False
        
        # Threading
        self.listening_thread = None
        self.command_queue = queue.Queue()
        self.processing_thread = None
        
        # Voice settings
        self.voice_settings = {
            'rate': 150,
            'volume': 0.8,
            'voice_id': None
        }
        
        # Whisper settings
        self.whisper_settings = {
            'model_size': 'medium',  # 'tiny', 'base', 'small', 'medium', 'large'
            'language': None,  # None means auto-detect
            'task': 'transcribe'
        }
        
        # Command mappings
        self.command_handlers = {}
        self.command_aliases = {}
        
        # Initialize voice engine
        self._setup_voice_engine()
        
        # Setup command handlers
        self._setup_command_handlers()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_commands, daemon=True)
        self.processing_thread.start()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print("🎤 Voice Command Manager initialized")
        if self.use_whisper:
            print("✅ Using OpenAI Whisper for speech recognition")
        else:
            print("⚠️ Using Google Speech Recognition (Whisper not available)")
    
    def _load_whisper_model(self):
        """Load Whisper model in a separate thread to avoid blocking UI"""
        def load_model():
            try:
                print(f"📥 Loading Whisper model: {self.whisper_settings['model_size']}")
                self.whisper_model = whisper.load_model(self.whisper_settings['model_size'])
                print("✅ Whisper model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load Whisper model: {e}")
                self.use_whisper = False
        
        # Load model in background thread
        model_thread = threading.Thread(target=load_model, daemon=True)
        model_thread.start()
    
    def _apply_vad(self, wav_path, aggressiveness=2):
        """Return a new wav file path with only speech segments using VAD."""
        import contextlib
        import collections
        import struct
        vad = webrtcvad.Vad(aggressiveness)
        with wave.open(wav_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            pcm_data = wf.readframes(wf.getnframes())
        frame_duration = 30  # ms
        frame_bytes = int(sample_rate * 2 * frame_duration / 1000)
        frames = [pcm_data[i:i+frame_bytes] for i in range(0, len(pcm_data), frame_bytes)]
        speech_frames = b''
        for frame in frames:
            if len(frame) < frame_bytes:
                continue
            is_speech = vad.is_speech(frame, sample_rate)
            if is_speech:
                speech_frames += frame
        # Write speech frames to new file
        vad_path = wav_path.replace('.wav', '_vad.wav')
        with wave.open(vad_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(speech_frames)
        return vad_path
    
    def _recognize_speech_whisper(self, audio_data):
        """Recognize speech using OpenAI Whisper with language detection and preprocessing"""
        try:
            if not self.whisper_model:
                return None
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
            # Write audio data to WAV file
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_data.get_wav_data())
            # --- Audio Preprocessing ---
            audio = AudioSegment.from_wav(temp_filename)
            audio = effects.normalize(audio)
            audio = silence.strip_silence(audio, silence_len=200, silence_thresh=audio.dBFS-16)
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            reduced = nr.reduce_noise(y=samples, sr=audio.frame_rate)
            audio = audio._spawn(reduced.astype(np.int16).tobytes())
            audio.export(temp_filename, format="wav")
            # --- VAD ---
            vad_path = self._apply_vad(temp_filename)
            # --- End Preprocessing ---
            # Language detection
            detected_lang = None
            if self.whisper_settings['language'] is None:
                result_lang = self.whisper_model.transcribe(vad_path, task='transcribe', language=None, initial_prompt=None, condition_on_previous_text=False)
                detected_lang = result_lang.get('language', 'en')
                print(f"🌐 Detected language: {detected_lang}")
            else:
                detected_lang = self.whisper_settings['language']
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                vad_path,
                language=detected_lang,
                task=self.whisper_settings['task']
            )
            # Clean up temporary files
            os.unlink(temp_filename)
            os.unlink(vad_path)
            return result['text'].strip().lower()
        except Exception as e:
            print(f"❌ Whisper recognition error: {e}")
            return None
    
    def _recognize_speech_google(self, audio_data):
        """Recognize speech using Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(audio_data).lower()
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"❌ Google Speech Recognition error: {e}")
            return None
    
    def _setup_voice_engine(self):
        """Setup text-to-speech engine"""
        try:
            # Configure voice settings
            self.engine.setProperty('rate', self.voice_settings['rate'])
            self.engine.setProperty('volume', self.voice_settings['volume'])
            
            # Get available voices and set a good one
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            print(f"✅ Voice engine configured with {len(voices)} available voices")
            
        except Exception as e:
            print(f"❌ Error setting up voice engine: {e}")
    
    def _setup_command_handlers(self):
        """Setup voice command handlers and aliases"""
        
        # Camera control commands
        self.command_handlers.update({
            'show cameras': self._handle_show_cameras,
            'camera view': self._handle_show_cameras,
            'view cameras': self._handle_show_cameras,
            'open cameras': self._handle_show_cameras,
            
            'show recordings': self._handle_show_recordings,
            'recordings': self._handle_show_recordings,
            'view recordings': self._handle_show_recordings,
            
            'show alerts': self._handle_show_alerts,
            'alerts': self._handle_show_alerts,
            'view alerts': self._handle_show_alerts,
            
            'show map': self._handle_show_map,
            'map view': self._handle_show_map,
            'open map': self._handle_show_map,
            
            'add camera': self._handle_add_camera,
            'new camera': self._handle_add_camera,
            'install camera': self._handle_add_camera,
            
            'delete camera': self._handle_delete_camera,
            'remove camera': self._handle_delete_camera,
            'uninstall camera': self._handle_delete_camera,
        })
        
        # System control commands
        self.command_handlers.update({
            'start service': self._handle_start_service,
            'start background service': self._handle_start_service,
            'enable service': self._handle_start_service,
            
            'stop service': self._handle_stop_service,
            'stop background service': self._handle_stop_service,
            'disable service': self._handle_stop_service,
            
            'test cameras': self._handle_test_cameras,
            'test all cameras': self._handle_test_cameras,
            'camera test': self._handle_test_cameras,
            
            'settings': self._handle_show_settings,
            'open settings': self._handle_show_settings,
            'device settings': self._handle_show_settings,
            
            'sensors': self._handle_show_sensors,
            'sensor page': self._handle_show_sensors,
            'view sensors': self._handle_show_sensors,
            
            'advanced camera': self._handle_show_advanced_camera,
            'camera advanced': self._handle_show_advanced_camera,
            'advanced settings': self._handle_show_advanced_camera,
        })
        
        # Navigation commands
        self.command_handlers.update({
            'go back': self._handle_go_back,
            'back': self._handle_go_back,
            'return': self._handle_go_back,
            'previous': self._handle_go_back,
            
            'home': self._handle_go_home,
            'main menu': self._handle_go_home,
            'dashboard': self._handle_go_home,
            
            'logout': self._handle_logout,
            'sign out': self._handle_logout,
            'exit': self._handle_logout,
        })
        
        # Voice control commands
        self.command_handlers.update({
            'stop listening': self._handle_stop_listening,
            'disable voice': self._handle_stop_listening,
            'mute voice': self._handle_stop_listening,
            
            'start listening': self._handle_start_listening,
            'enable voice': self._handle_start_listening,
            'voice on': self._handle_start_listening,
            
            'what can you do': self._handle_help,
            'help': self._handle_help,
            'commands': self._handle_help,
            'voice commands': self._handle_help,
        })
        
        # Status commands
        self.command_handlers.update({
            'status': self._handle_status,
            'system status': self._handle_status,
            'camera status': self._handle_status,
            
            'how many cameras': self._handle_camera_count,
            'camera count': self._handle_camera_count,
            'number of cameras': self._handle_camera_count,
        })
    
    def start_listening(self):
        """Start listening for voice commands"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.is_enabled = True
        self.wake_word_detected = False
        
        self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listening_thread.start()
        
        self.listening_started.emit()
        self.speak("Voice commands activated. Say 'fire vision' followed by your command.")
        print("🎤 Voice listening started")
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        self.is_enabled = False
        
        if self.listening_thread:
            self.listening_thread.join(timeout=1.0)
        
        self.listening_stopped.emit()
        self.speak("Voice commands deactivated.")
        print("🔇 Voice listening stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        with sr.Microphone() as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening:
                try:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    # Recognize speech using appropriate method
                    if self.use_whisper and self.whisper_model:
                        text = self._recognize_speech_whisper(audio)
                    else:
                        text = self._recognize_speech_google(audio)
                    
                    if text:
                        self.speech_recognized.emit(text)
                        self._process_speech(text)
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    self.error_occurred.emit(f"Speech recognition error: {e}")
                    break
                except Exception as e:
                    self.error_occurred.emit(f"Listening error: {e}")
                    break
    
    def _process_speech(self, text):
        """Process recognized speech text"""
        print(f"🎤 Recognized: '{text}'")
        
        # Check for wake word
        if self.wake_word in text:
            self.wake_word_detected = True
            # Remove wake word from text
            command_text = text.replace(self.wake_word, "").strip()
            
            if command_text:
                self.speak("Command received")
                self.command_queue.put(command_text)
            else:
                self.speak("I'm listening. What would you like me to do?")
        elif self.wake_word_detected:
            # Process command without wake word if already activated
            self.command_queue.put(text)
    
    def _process_commands(self):
        """Process commands from queue"""
        while True:
            try:
                command = self.command_queue.get(timeout=1)
                self._execute_command(command)
            except queue.Empty:
                continue
            except Exception as e:
                self.error_occurred.emit(f"Command processing error: {e}")
    
    def _execute_command(self, command_text):
        """Execute a voice command"""
        print(f"🔍 Processing command: '{command_text}'")
        
        # Find matching command handler
        handler = None
        for cmd, func in self.command_handlers.items():
            if cmd in command_text or any(alias in command_text for alias in self.command_aliases.get(cmd, [])):
                handler = func
                break
        
        if handler:
            try:
                handler(command_text)
                self.command_detected.emit("success", command_text)
            except Exception as e:
                error_msg = f"Error executing command: {e}"
                self.error_occurred.emit(error_msg)
                self.speak("Sorry, I couldn't execute that command.")
        else:
            self.speak("I didn't understand that command. Say 'help' for available commands.")
            print(f"❌ Unknown command: '{command_text}'")
    
    def speak(self, text):
        """Speak text using text-to-speech"""
        try:
            self.voice_feedback.emit(text)
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"❌ Speech error: {e}")
    
    # Command handlers
    def _handle_show_cameras(self, command):
        """Handle show cameras command"""
        if self.main_window:
            self.main_window.show_cameras_page()
            self.speak("Showing camera view")
    
    def _handle_show_recordings(self, command):
        """Handle show recordings command"""
        if self.main_window:
            self.main_window.show_recordings_page()
            self.speak("Showing recordings")
    
    def _handle_show_alerts(self, command):
        """Handle show alerts command"""
        if self.main_window:
            self.main_window.show_alerts_page()
            self.speak("Showing alerts")
    
    def _handle_show_map(self, command):
        """Handle show map command"""
        if self.main_window:
            self.main_window.show_map_overview_page()
            self.speak("Showing map view")
    
    def _handle_add_camera(self, command):
        """Handle add camera command"""
        if self.main_window:
            self.main_window.show_add_camera_dialog()
            self.speak("Opening add camera dialog")
    
    def _handle_delete_camera(self, command):
        """Handle delete camera command"""
        if self.main_window:
            self.main_window.show_delete_cameras_dialog()
            self.speak("Opening camera deletion dialog")
    
    def _handle_start_service(self, command):
        """Handle start service command"""
        if self.main_window:
            self.main_window.start_background_service()
            self.speak("Starting background service")
    
    def _handle_stop_service(self, command):
        """Handle stop service command"""
        if self.main_window:
            self.main_window.stop_background_service()
            self.speak("Stopping background service")
    
    def _handle_test_cameras(self, command):
        """Handle test cameras command"""
        if self.main_window:
            self.main_window.test_all_cameras()
            self.speak("Testing all cameras")
    
    def _handle_show_settings(self, command):
        """Handle show settings command"""
        if self.main_window:
            self.main_window.show_device_settings_page()
            self.speak("Opening device settings")
    
    def _handle_show_sensors(self, command):
        """Handle show sensors command"""
        if self.main_window:
            self.main_window.show_sensors_page()
            self.speak("Showing sensors page")
    
    def _handle_show_advanced_camera(self, command):
        """Handle show advanced camera command"""
        if self.main_window:
            self.main_window.show_advanced_camera_page()
            self.speak("Opening advanced camera settings")
    
    def _handle_go_back(self, command):
        """Handle go back command"""
        if self.main_window:
            self.main_window.return_to_grid()
            self.speak("Going back")
    
    def _handle_go_home(self, command):
        """Handle go home command"""
        if self.main_window:
            # Navigate to main dashboard
            self.main_window.show_cameras_page()
            self.speak("Returning to main view")
    
    def _handle_logout(self, command):
        """Handle logout command"""
        if self.main_window:
            self.main_window.logout()
            self.speak("Logging out")
    
    def _handle_stop_listening(self, command):
        """Handle stop listening command"""
        self.stop_listening()
    
    def _handle_start_listening(self, command):
        """Handle start listening command"""
        self.start_listening()
    
    def _handle_help(self, command):
        """Handle help command"""
        help_text = """
        Available voice commands:
        Camera control: show cameras, add camera, delete camera
        Navigation: show recordings, show alerts, show map
        System: start service, stop service, test cameras
        Settings: settings, sensors, advanced camera
        Navigation: go back, home, logout
        Voice control: stop listening, start listening
        Status: status, how many cameras
        """
        self.speak("Here are the available commands. Camera control includes show cameras, add camera, and delete camera. Navigation includes show recordings, alerts, and map. System commands include start service, stop service, and test cameras. Settings include settings, sensors, and advanced camera. Navigation includes go back, home, and logout. Voice control includes stop listening and start listening. Status commands include status and how many cameras.")
    
    def _handle_status(self, command):
        """Handle status command"""
        if self.main_window:
            # Get system status
            camera_count = len(self.main_window.camera_widgets)
            service_running = hasattr(self.main_window, 'background_service') and self.main_window.background_service.running
            
            status_text = f"System status: {camera_count} cameras connected, background service {'running' if service_running else 'stopped'}"
            self.speak(status_text)
    
    def _handle_camera_count(self, command):
        """Handle camera count command"""
        if self.main_window:
            camera_count = len(self.main_window.camera_widgets)
            self.speak(f"You have {camera_count} cameras connected")
    
    def is_voice_enabled(self):
        """Check if voice commands are enabled"""
        return self.is_enabled
    
    def get_voice_status(self):
        """Get current voice command status"""
        return {
            'enabled': self.is_enabled,
            'listening': self.is_listening,
            'wake_word': self.wake_word,
            'voice_settings': self.voice_settings
        }
    
    def update_voice_settings(self, settings):
        """Update voice settings"""
        self.voice_settings.update(settings)
        self._setup_voice_engine()
    
    def set_wake_word(self, wake_word):
        """Set custom wake word"""
        self.wake_word = wake_word.lower()
        self.speak(f"Wake word changed to {wake_word}")
    
    def update_whisper_settings(self, settings):
        """Update Whisper settings"""
        self.whisper_settings.update(settings)
        if self.use_whisper and 'model_size' in settings:
            # Reload model if size changed
            self._load_whisper_model()
    
    def get_whisper_status(self):
        """Get Whisper status and settings"""
        return {
            'available': self.use_whisper,
            'model_loaded': self.whisper_model is not None,
            'settings': self.whisper_settings.copy()
        }
    
    def switch_to_whisper(self):
        """Switch to Whisper recognition"""
        if WHISPER_AVAILABLE:
            self.use_whisper = True
            if not self.whisper_model:
                self._load_whisper_model()
            self.speak("Switched to Whisper speech recognition")
        else:
            self.speak("Whisper is not available. Please install it first.")
    
    def switch_to_google(self):
        """Switch to Google Speech Recognition"""
        self.use_whisper = False
        self.speak("Switched to Google Speech Recognition")

    def recognize_and_execute_snippet(self):
        """Record a short audio snippet and recognize command with fuzzy and keyword matching"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for a short snippet...")
            audio = self.recognizer.listen(source, timeout=3)
        if audio:
            if self.use_whisper and self.whisper_model:
                text = self._recognize_speech_whisper(audio)
            else:
                text = self._recognize_speech_google(audio)
            if text:
                print(f"Recognized snippet: '{text}'")
                # Fuzzy match to available commands
                commands = list(self.command_handlers.keys())
                match, score = self._fuzzy_best_match(text, commands)
                print(f"Best match: {match} (score: {score:.2f})")
                if match and score >= 0.7:
                    try:
                        self.command_handlers[match](text)
                        return text, match, score
                    except Exception as e:
                        print(f"Error executing snippet command '{match}': {e}")
                        return text, match, score
                # Keyword-based fallback
                for cmd in commands:
                    if cmd in text:
                        print(f"Keyword-based match: {cmd}")
                        try:
                            self.command_handlers[cmd](text)
                            return text, cmd, 0.6
                        except Exception as e:
                            print(f"Error executing keyword command '{cmd}': {e}")
                            return text, cmd, 0.6
                print(f"No good command match for snippet: '{text}'")
                return text, None, score
            else:
                print("Could not recognize snippet.")
                return None, None, 0.0
        else:
            print("No audio data received for snippet.")
            return None, None, 0.0

    def _fuzzy_best_match(self, text, choices):
        """Return the best fuzzy match and its score (0-1)"""
        best = difflib.get_close_matches(text, choices, n=1, cutoff=0)
        if best:
            match = best[0]
            score = difflib.SequenceMatcher(None, text, match).ratio()
            return match, score
        return None, 0.0


class VoiceCommandWidget(QWidget):
    """Voice command control widget for the UI"""
    
    def __init__(self, voice_manager, parent=None):
        super().__init__(parent)
        self.voice_manager = voice_manager
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the voice command widget UI"""
        layout = QVBoxLayout()
        # Tip label
        self.tip_label = QLabel("Tip: Speak a short, clear command (e.g., 'show cameras')")
        self.tip_label.setStyleSheet("color: #888; font-size: 13px; margin-bottom: 6px;")
        layout.addWidget(self.tip_label)
        
        # Title
        title = QLabel("Voice Commands")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Status indicator
        self.status_label = QLabel("Voice Commands: Disabled")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Listening")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        
        self.stop_button = QPushButton("Stop Listening")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        
        # Record Command button
        self.record_cmd_button = QPushButton("🎙️ Record Command")
        self.record_cmd_button.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:pressed {
                background-color: #22313f;
            }
        """)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.record_cmd_button)
        layout.addLayout(button_layout)
        
        # Recognition method selector
        recognition_layout = QHBoxLayout()
        
        self.whisper_button = QPushButton("Use Whisper")
        self.whisper_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        
        self.google_button = QPushButton("Use Google")
        self.google_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        
        recognition_layout.addWidget(self.whisper_button)
        recognition_layout.addWidget(self.google_button)
        layout.addLayout(recognition_layout)
        
        # Recognition status
        self.recognition_status = QLabel("Recognition: Google")
        self.recognition_status.setStyleSheet("""
            QLabel {
                padding: 5px;
                border-radius: 3px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.recognition_status)
        
        # Help button
        self.help_button = QPushButton("Voice Commands Help")
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(self.help_button)
        
        # Recent commands
        self.recent_label = QLabel("Recent Commands:")
        self.recent_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.recent_label)
        
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(100)
        self.recent_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.recent_list)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.start_button.clicked.connect(self.voice_manager.start_listening)
        self.stop_button.clicked.connect(self.voice_manager.stop_listening)
        self.whisper_button.clicked.connect(self.switch_to_whisper)
        self.google_button.clicked.connect(self.switch_to_google)
        self.help_button.clicked.connect(self.show_help)
        self.record_cmd_button.clicked.connect(self.record_command_snippet)
        
        # Connect voice manager signals
        self.voice_manager.listening_started.connect(self.update_status)
        self.voice_manager.listening_stopped.connect(self.update_status)
        self.voice_manager.speech_recognized.connect(self.add_recent_command)
        self.voice_manager.error_occurred.connect(self.show_error)
        
        # Update initial recognition status
        self.update_recognition_status()
    
    def update_status(self):
        """Update status display"""
        if self.voice_manager.is_listening:
            self.status_label.setText("Voice Commands: Listening...")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #d5f4e6;
                    color: #27ae60;
                }
            """)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("Voice Commands: Disabled")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                }
            """)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def add_recent_command(self, command):
        """Add command to recent list"""
        self.recent_list.insertItem(0, command)
        if self.recent_list.count() > 5:
            self.recent_list.takeItem(5)
    
    def switch_to_whisper(self):
        """Switch to Whisper recognition"""
        self.voice_manager.switch_to_whisper()
        self.update_recognition_status()
    
    def switch_to_google(self):
        """Switch to Google recognition"""
        self.voice_manager.switch_to_google()
        self.update_recognition_status()
    
    def update_recognition_status(self):
        """Update recognition status display"""
        status = self.voice_manager.get_whisper_status()
        if status['available'] and self.voice_manager.use_whisper:
            if status['model_loaded']:
                self.recognition_status.setText("Recognition: Whisper (Ready)")
                self.recognition_status.setStyleSheet("""
                    QLabel {
                        padding: 5px;
                        border-radius: 3px;
                        background-color: #d5f4e6;
                        color: #27ae60;
                        font-size: 12px;
                    }
                """)
            else:
                self.recognition_status.setText("Recognition: Whisper (Loading...)")
                self.recognition_status.setStyleSheet("""
                    QLabel {
                        padding: 5px;
                        border-radius: 3px;
                        background-color: #fff3cd;
                        color: #856404;
                        font-size: 12px;
                    }
                """)
        else:
            self.recognition_status.setText("Recognition: Google")
            self.recognition_status.setStyleSheet("""
                QLabel {
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                    font-size: 12px;
                }
            """)
    
    def show_help(self):
        """Show voice commands help"""
        help_text = """
        <h3>Voice Commands Help</h3>
        <p><b>Wake Word:</b> Say "Fire Vision" followed by your command</p>
        
        <h4>Camera Control:</h4>
        <ul>
        <li>"Show cameras" - Open camera view</li>
        <li>"Add camera" - Open add camera dialog</li>
        <li>"Delete camera" - Open camera deletion dialog</li>
        </ul>
        
        <h4>Navigation:</h4>
        <ul>
        <li>"Show recordings" - Open recordings page</li>
        <li>"Show alerts" - Open alerts page</li>
        <li>"Show map" - Open map view</li>
        <li>"Go back" - Return to previous view</li>
        <li>"Home" - Return to main view</li>
        </ul>
        
        <h4>System Control:</h4>
        <ul>
        <li>"Start service" - Start background service</li>
        <li>"Stop service" - Stop background service</li>
        <li>"Test cameras" - Test all cameras</li>
        <li>"Settings" - Open device settings</li>
        </ul>
        
        <h4>Voice Control:</h4>
        <ul>
        <li>"Stop listening" - Disable voice commands</li>
        <li>"Start listening" - Enable voice commands</li>
        <li>"Help" - Show this help</li>
        </ul>
        """
        
        QMessageBox.information(self, "Voice Commands Help", help_text)
    
    def show_error(self, error):
        """Show error message"""
        QMessageBox.warning(self, "Voice Command Error", error) 

    def record_command_snippet(self):
        """Record a short audio snippet and recognize command"""
        self.status_label.setText("Recording 3s snippet... Please speak a clear command.")
        QApplication.processEvents()
        result, matched_cmd, score = self.voice_manager.recognize_and_execute_snippet()
        if result:
            self.status_label.setText(f"Recognized: '{result}'\nMatched: '{matched_cmd}' (score: {score:.2f})")
            self.add_recent_command(result)
        else:
            self.status_label.setText("Could not recognize command.") 