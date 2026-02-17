import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_vlc_player/flutter_vlc_player.dart';
import '../models/camera_model.dart';
import '../utils/app_theme.dart';

class CameraStreamScreen extends StatefulWidget {
  final Camera camera;

  const CameraStreamScreen({
    super.key,
    required this.camera,
  });

  @override
  State<CameraStreamScreen> createState() => _CameraStreamScreenState();
}

class _CameraStreamScreenState extends State<CameraStreamScreen> {
  late VlcPlayerController _vlcController;
  bool _isFullscreen = false;
  bool _isLoading = true;
  bool _hasError = false;
  String _errorMessage = '';
  bool _isPlaying = false;
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      // Initialize VLC player with RTSP stream
      _vlcController = VlcPlayerController.network(
        widget.camera.source, // RTSP URL from your camera
        hwAcc: HwAcc.full,
        autoPlay: false,
        options: VlcPlayerOptions(
          advanced: VlcAdvancedOptions([
            VlcAdvancedOptions.networkCaching(300),
            VlcAdvancedOptions.clockJitter(0),
          ]),
          video: VlcVideoOptions([
            VlcVideoOptions.dropLateFrames(true),
            VlcVideoOptions.skipFrames(true),
          ]),
          audio: VlcAudioOptions([
            VlcAudioOptions.audioTimeStretch(true),
          ]),
          rtp: VlcRtpOptions([
            VlcRtpOptions.rtpOverRtsp(true),
          ]),
        ),
      );

      // Add initialization listener
      _vlcController.addOnInitListener(() {
        if (mounted) {
          _vlcController.play();
          setState(() {
            _isLoading = false;
            _isPlaying = true;
          });
        }
      });

      // Add player state listener
      _vlcController.addListener(() {
        if (mounted) {
          final state = _vlcController.value.playingState;

          switch (state) {
            case PlayingState.playing:
              setState(() {
                _isPlaying = true;
                _isLoading = false;
                _hasError = false;
              });
              break;
            case PlayingState.paused:
              setState(() {
                _isPlaying = false;
                _isLoading = false;
              });
              break;
            case PlayingState.stopped:
              setState(() {
                _isPlaying = false;
                _isLoading = false;
              });
              break;
            case PlayingState.buffering:
              setState(() {
                _isLoading = true;
              });
              break;
            case PlayingState.error:
              setState(() {
                _hasError = true;
                _errorMessage = 'Failed to connect to camera stream';
                _isLoading = false;
                _isPlaying = false;
              });
              break;
            default:
              break;
          }
        }
      });

    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = 'Error initializing stream: ${e.toString()}';
          _isLoading = false;
        });
      }
    }
  }

  void _toggleFullscreen() {
    setState(() {
      _isFullscreen = !_isFullscreen;
    });

    if (_isFullscreen) {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersive);
      SystemChrome.setPreferredOrientations([
        DeviceOrientation.landscapeLeft,
        DeviceOrientation.landscapeRight,
      ]);
    } else {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
      SystemChrome.setPreferredOrientations([
        DeviceOrientation.portraitUp,
        DeviceOrientation.landscapeLeft,
        DeviceOrientation.landscapeRight,
      ]);
    }
  }

  void _togglePlayPause() {
    if (_vlcController.value.isPlaying) {
      _vlcController.pause();
    } else {
      _vlcController.play();
    }
  }

  void _stopStream() {
    _vlcController.stop();
  }

  void _restartStream() {
    _vlcController.stop();
    Future.delayed(const Duration(milliseconds: 500), () {
      _vlcController.play();
    });
  }

  String _maskRtspUrl(String url) {
    if (url.contains('@')) {
      final parts = url.split('@');
      if (parts.length >= 2) {
        final protocol = parts[0].split('://')[0];
        final credentials = parts[0].split('://')[1];
        final maskedCredentials = credentials.replaceAll(RegExp(r'.'), '*');
        return '$protocol://$maskedCredentials@${parts.sublist(1).join('@')}';
      }
    }
    return url;
  }

  @override
  void dispose() {
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    _vlcController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isFullscreen) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: _buildStreamContent(),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.camera.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.fullscreen),
            onPressed: _toggleFullscreen,
            tooltip: 'Fullscreen',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _restartStream,
            tooltip: 'Restart Stream',
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              switch (value) {
                case 'settings':
                  _showStreamSettings();
                  break;
                case 'record':
                  _toggleRecording();
                  break;
                case 'snapshot':
                  _takeSnapshot();
                  break;
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'settings',
                child: Row(
                  children: [
                    Icon(Icons.settings),
                    SizedBox(width: 8),
                    Text('Stream Settings'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'record',
                child: Row(
                  children: [
                    Icon(Icons.fiber_manual_record),
                    SizedBox(width: 8),
                    Text('Record'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'snapshot',
                child: Row(
                  children: [
                    Icon(Icons.camera_alt),
                    SizedBox(width: 8),
                    Text('Snapshot'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Stream Area
          Expanded(
            flex: 3,
            child: _buildStreamContent(),
          ),

          // Stream Controls
          Container(
            padding: const EdgeInsets.all(16),
            child: _buildStreamControls(),
          ),

          // Camera Info
          Expanded(
            flex: 1,
            child: _buildCameraInfo(),
          ),
        ],
      ),
    );
  }

  Widget _buildStreamContent() {
    return Container(
      width: double.infinity,
      color: Colors.black,
      child: Stack(
        children: [
          // VLC Player
          if (!_hasError)
            VlcPlayer(
              controller: _vlcController,
              aspectRatio: 16 / 9,
              placeholder: Container(
                color: Colors.black,
                child: const Center(
                  child: CircularProgressIndicator(
                    color: Colors.white,
                  ),
                ),
              ),
            ),

          // Error State
          if (_hasError)
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline,
                    color: Colors.red,
                    size: 64,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _errorMessage,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _restartStream,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry Connection'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryColor,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),
            ),

          // Loading State
          if (_isLoading)
            Container(
              color: Colors.black54,
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 3,
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Connecting to RTSP stream...',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // Fullscreen controls
          if (_isFullscreen)
            Positioned(
              top: 40,
              right: 16,
              child: Row(
                children: [
                  _buildControlButton(
                    Icons.fullscreen_exit,
                    'Exit Fullscreen',
                    _toggleFullscreen,
                  ),
                  const SizedBox(width: 8),
                  _buildControlButton(
                    Icons.close,
                    'Close',
                        () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

          // Stream info overlay
          if (!_isLoading && !_hasError)
            Positioned(
              top: 16,
              left: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _isPlaying ? Colors.red : Colors.grey,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _isPlaying ? 'LIVE' : 'PAUSED',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // Recording indicator
          if (_isRecording)
            Positioned(
              top: 16,
              right: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.fiber_manual_record,
                      color: Colors.white,
                      size: 12,
                    ),
                    SizedBox(width: 4),
                    Text(
                      'REC',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildControlButton(IconData icon, String tooltip, VoidCallback onPressed) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.5),
        borderRadius: BorderRadius.circular(20),
      ),
      child: IconButton(
        icon: Icon(icon, color: Colors.white),
        onPressed: onPressed,
        tooltip: tooltip,
      ),
    );
  }

  Widget _buildStreamControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildControlIcon(
          _isPlaying ? Icons.pause : Icons.play_arrow,
          _isPlaying ? 'Pause' : 'Play',
          _togglePlayPause,
        ),
        _buildControlIcon(Icons.stop, 'Stop', _stopStream),
        _buildControlIcon(Icons.refresh, 'Restart', _restartStream),
        _buildControlIcon(Icons.camera_alt, 'Snapshot', _takeSnapshot),
        _buildControlIcon(
          _isRecording ? Icons.stop : Icons.fiber_manual_record,
          _isRecording ? 'Stop Recording' : 'Start Recording',
          _toggleRecording,
        ),
      ],
    );
  }

  Widget _buildControlIcon(IconData icon, String tooltip, VoidCallback onPressed) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(25),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(25),
            border: Border.all(
              color: AppTheme.primaryColor.withOpacity(0.3),
            ),
          ),
          child: Icon(
            icon,
            color: AppTheme.primaryColor,
            size: 24,
          ),
        ),
      ),
    );
  }

  Widget _buildCameraInfo() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.videocam,
                color: AppTheme.primaryColor,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'Stream Information',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ListView(
              children: [
                _buildInfoRow('Camera', widget.camera.name),
                _buildInfoRow('Status', _getStreamStatus()),
                _buildInfoRow('Source', _maskRtspUrl(widget.camera.source)),
                _buildInfoRow('Resolution', 'Auto-detected'),
                _buildInfoRow('Protocol', 'RTSP/RTP'),
                if (_vlcController.value.isInitialized)
                  _buildInfoRow('Position', _formatDuration(_vlcController.value.position)),
                if (_vlcController.value.isInitialized)
                  _buildInfoRow('Duration', _formatDuration(_vlcController.value.duration)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getStreamStatus() {
    if (_hasError) return 'ERROR';
    if (_isLoading) return 'CONNECTING';
    if (_isPlaying) return 'STREAMING';
    return 'STOPPED';
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, "0");
    String twoDigitMinutes = twoDigits(duration.inMinutes.remainder(60));
    String twoDigitSeconds = twoDigits(duration.inSeconds.remainder(60));
    return "${twoDigits(duration.inHours)}:$twoDigitMinutes:$twoDigitSeconds";
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w500,
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }

  void _showStreamSettings() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Stream Settings',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.high_quality),
              title: const Text('Hardware Acceleration'),
              subtitle: const Text('Enabled'),
              trailing: Switch(
                value: true,
                onChanged: (value) {
                  // Implement hardware acceleration toggle
                },
              ),
            ),
            ListTile(
              leading: const Icon(Icons.network_check),
              title: const Text('Network Caching'),
              subtitle: const Text('300ms'),
              onTap: () {
                // Implement network caching settings
              },
            ),
            ListTile(
              leading: const Icon(Icons.aspect_ratio),
              title: const Text('Aspect Ratio'),
              subtitle: const Text('16:9'),
              onTap: () {
                // Implement aspect ratio settings
              },
            ),
            ListTile(
              leading: const Icon(Icons.volume_up),
              title: const Text('Audio'),
              subtitle: const Text('Enabled'),
              trailing: Switch(
                value: true,
                onChanged: (value) {
                  if (value) {
                    _vlcController.setVolume(100);
                  } else {
                    _vlcController.setVolume(0);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _toggleRecording() {
    setState(() {
      _isRecording = !_isRecording;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _isRecording ? 'Recording started' : 'Recording stopped',
        ),
        backgroundColor: _isRecording ? AppTheme.successColor : AppTheme.warningColor,
      ),
    );

    // TODO: Implement actual recording functionality
    // You can use packages like flutter_screen_recording or implement native recording
  }

  void _takeSnapshot() async {
    try {
      // Take screenshot using VLC controller
      final screenshot = await _vlcController.takeSnapshot();

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Snapshot captured successfully'),
          backgroundColor: AppTheme.successColor,
        ),
      );

      // TODO: Save screenshot to gallery or local storage
      // You can use packages like image_gallery_saver or path_provider

    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to take snapshot: ${e.toString()}'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    }
  }
}