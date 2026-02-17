import os
import cv2
import datetime
import threading
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal

class RecordingManager(QObject):
    """Manages video recording functionality"""
    
    recording_started = pyqtSignal(str, str)  # camera_id, filename
    recording_stopped = pyqtSignal(str, str)  # camera_id, filename
    recording_error = pyqtSignal(str, str)    # camera_id, error
    
    def __init__(self, recordings_dir="recordings"):
        super().__init__()
        self.recordings_dir = recordings_dir
        self.active_recordings = {}  # camera_id -> recording_info
        
        # Create recordings directory
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)
    
    def start_recording(self, camera_id: str, camera_name: str, frame_size: tuple, fps: int = 30) -> bool:
        """Start recording for a camera"""
        try:
            if camera_id in self.active_recordings:
                print(f"⚠️ Recording already active for camera {camera_id}")
                return False
            
            # Generate filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"{camera_name}_{timestamp}.mp4")
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)
            
            if not video_writer.isOpened():
                print(f"❌ Failed to create video writer for {camera_id}")
                return False
            
            # Store recording info
            self.active_recordings[camera_id] = {
                'filename': filename,
                'video_writer': video_writer,
                'start_time': datetime.datetime.now(),
                'frame_count': 0
            }
            
            self.recording_started.emit(camera_id, filename)
            print(f"🎬 Recording started for camera {camera_id}: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting recording for camera {camera_id}: {e}")
            self.recording_error.emit(camera_id, str(e))
            return False
    
    def stop_recording(self, camera_id: str) -> Optional[str]:
        """Stop recording for a camera"""
        try:
            if camera_id not in self.active_recordings:
                print(f"⚠️ No active recording for camera {camera_id}")
                return None
            
            recording_info = self.active_recordings[camera_id]
            video_writer = recording_info['video_writer']
            filename = recording_info['filename']
            
            # Release video writer
            video_writer.release()
            
            # Remove from active recordings
            del self.active_recordings[camera_id]
            
            self.recording_stopped.emit(camera_id, filename)
            print(f"🎬 Recording stopped for camera {camera_id}: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error stopping recording for camera {camera_id}: {e}")
            self.recording_error.emit(camera_id, str(e))
            return None
    
    def add_frame(self, camera_id: str, frame) -> bool:
        """Add a frame to the recording"""
        try:
            if camera_id in self.active_recordings:
                recording_info = self.active_recordings[camera_id]
                video_writer = recording_info['video_writer']
                
                video_writer.write(frame)
                recording_info['frame_count'] += 1
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error adding frame to recording for camera {camera_id}: {e}")
            return False
    
    def is_recording(self, camera_id: str) -> bool:
        """Check if camera is currently recording"""
        return camera_id in self.active_recordings
    
    def get_recording_info(self, camera_id: str) -> Optional[Dict]:
        """Get recording information for a camera"""
        return self.active_recordings.get(camera_id)
    
    def stop_all_recordings(self):
        """Stop all active recordings"""
        for camera_id in list(self.active_recordings.keys()):
            self.stop_recording(camera_id)
