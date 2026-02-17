# 🎤 Voice Commands for FireVision Pro

FireVision Pro now includes a comprehensive voice command system that allows you to control the application hands-free using natural speech commands.

## 🚀 Quick Start

1. **Install Dependencies**: Run the voice command installer
   ```bash
   python install_voice_dependencies.py
   ```

2. **Start FireVision Pro**: Launch the application normally

3. **Access Voice Commands**: Click on "🎤 Voice Commands" in the sidebar

4. **Start Listening**: Click "Start Listening" button

5. **Use Voice Commands**: Say "Fire Vision" followed by your command

## 🎯 Available Voice Commands

### Camera Control
- **"Fire Vision show cameras"** - Open camera view
- **"Fire Vision add camera"** - Open add camera dialog
- **"Fire Vision delete camera"** - Open camera deletion dialog

### Navigation
- **"Fire Vision show recordings"** - Open recordings page
- **"Fire Vision show alerts"** - Open alerts page
- **"Fire Vision show map"** - Open map view
- **"Fire Vision go back"** - Return to previous view
- **"Fire Vision home"** - Return to main view

### System Control
- **"Fire Vision start service"** - Start background service
- **"Fire Vision stop service"** - Stop background service
- **"Fire Vision test cameras"** - Test all cameras
- **"Fire Vision settings"** - Open device settings
- **"Fire Vision sensors"** - Open sensors page
- **"Fire Vision advanced camera"** - Open advanced camera settings

### Voice Control
- **"Fire Vision stop listening"** - Disable voice commands
- **"Fire Vision start listening"** - Enable voice commands
- **"Fire Vision help"** - Get list of available commands

### Status & Information
- **"Fire Vision status"** - Get system status
- **"Fire Vision how many cameras"** - Get camera count

## 🎤 How It Works

### Speech Recognition Options
The voice command system supports two speech recognition engines:

#### OpenAI Whisper (Recommended)
- **Higher accuracy** for different accents and noisy environments
- **Offline processing** - works without internet connection
- **Multiple model sizes** - from tiny (39MB) to large (1550MB)
- **Better handling** of technical terms and commands

#### Google Speech Recognition
- **Requires internet connection**
- **Good accuracy** in quiet environments
- **Fast processing** for simple commands

### Wake Word System
The voice command system uses a wake word approach:
1. Say **"Fire Vision"** to activate the system
2. Follow with your command
3. The system will respond with voice feedback

### Example Usage
```
You: "Fire Vision show cameras"
System: "Showing camera view"

You: "Fire Vision add camera"
System: "Opening add camera dialog"

You: "Fire Vision status"
System: "System status: 3 cameras connected, background service running"
```

## ⚙️ Voice Command Settings

### Accessing Settings
1. Go to "🎤 Voice Commands" in the sidebar
2. The voice command widget shows:
   - Current status (Listening/Disabled)
   - Start/Stop buttons
   - Recent commands list
   - Help button

### Customization Options
- **Wake Word**: Currently set to "Fire Vision" (can be customized in code)
- **Voice Settings**: Speech rate and volume can be adjusted
- **Microphone**: Automatically detects and uses default microphone

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Microphone access
- Internet connection (for speech recognition)

### Automatic Installation
```bash
python install_voice_dependencies.py
```

### Manual Installation
```bash
pip install SpeechRecognition>=3.8.1
pip install pyttsx3>=2.90
pip install pyaudio>=0.2.11
pip install openai-whisper>=20231117
```

### System-Specific Notes

#### Windows
- May require Microsoft Visual C++ Build Tools
- If PyAudio fails, try: `pip install pipwin && pipwin install pyaudio`

#### Linux
- Install system dependencies: `sudo apt-get install portaudio19-dev python3-pyaudio`
- Ensure microphone permissions are granted

#### macOS
- Install PortAudio: `brew install portaudio`
- Grant microphone access in System Preferences

## 🎯 Voice Command Widget Features

### Status Display
- **Green**: Voice commands are listening
- **Gray**: Voice commands are disabled

### Control Buttons
- **Start Listening**: Activates voice recognition
- **Stop Listening**: Deactivates voice recognition
- **Voice Commands Help**: Shows detailed help

### Recent Commands
- Shows the last 5 recognized commands
- Helps you see what the system understood

## 🚨 Troubleshooting

### Common Issues

#### "No module named 'speech_recognition'"
```bash
pip install SpeechRecognition
```

#### "No module named 'pyaudio'"
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio
```

#### "Microphone not detected"
1. Check microphone permissions
2. Ensure microphone is set as default device
3. Test microphone in system settings

#### "Voice commands not responding"
1. Check internet connection (required for speech recognition)
2. Ensure wake word "Fire Vision" is said clearly
3. Try speaking more slowly and clearly
4. Check if microphone is working in other applications

#### "Text-to-speech not working"
1. Check system audio settings
2. Ensure speakers/headphones are connected
3. Try adjusting voice settings in the code

### Performance Tips
- Speak clearly and at a normal pace
- Minimize background noise
- Use the wake word "Fire Vision" before each command
- Wait for voice feedback before giving the next command

## 🔒 Privacy & Security

### Speech Recognition
- Uses Google's Speech Recognition API
- Audio is sent to Google for processing
- No audio is stored locally
- Commands are processed in real-time

### Local Processing
- Voice feedback (text-to-speech) is processed locally
- No voice data is stored on your system
- Commands are executed locally in the application

## 🎨 Customization

### Adding New Commands
To add custom voice commands, edit `voice_command_manager.py`:

```python
# Add to _setup_command_handlers method
self.command_handlers.update({
    'your custom command': self._handle_your_command,
})

# Add handler method
def _handle_your_command(self, command):
    # Your custom logic here
    self.speak("Custom command executed")
```

### Changing Wake Word
```python
# In VoiceCommandManager.__init__
self.wake_word = "your custom wake word"
```

### Voice Settings
```python
# In VoiceCommandManager.__init__
self.voice_settings = {
    'rate': 150,      # Speech rate (words per minute)
    'volume': 0.8,    # Volume (0.0 to 1.0)
    'voice_id': None  # Specific voice ID
}
```

## 📱 System Tray Integration

Voice commands can also be controlled from the system tray:
- Right-click the FireVision Pro tray icon
- Select "🎤 Start Voice Commands" or "🔇 Stop Voice Commands"
- Voice commands work even when the app is minimized

## 🎉 Advanced Features

### Continuous Listening Mode
- Once activated with wake word, can process multiple commands
- Say "stop listening" to deactivate

### Error Handling
- Graceful handling of network issues
- Fallback responses for unrecognized commands
- Automatic microphone reconnection

### Multi-language Support
- Can be extended to support multiple languages
- Uses Google's multi-language speech recognition

## 📞 Support

If you encounter issues with voice commands:

1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Test microphone in other applications
4. Check system audio settings
5. Verify internet connection for speech recognition

## 🔄 Updates

Voice command features are regularly updated. Check for updates to:
- Speech recognition accuracy
- New voice commands
- Performance improvements
- Bug fixes

---

**Note**: Voice commands require an internet connection for speech recognition. The system uses Google's Speech Recognition API for processing voice input. 