import cv2
import sys
import numpy as np
import time
import threading
import json
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("Warning: ultralytics not found. Fire/Smoke detection disabled.")
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import os
from dotenv import load_dotenv

load_dotenv()

from workers.base_worker import BaseWorker, WorkerStatus
from core.confidence_engine import TemporalConfidenceEngine, AlertLevel, DetectionEvidence


class FireSmokeDetector(QObject):
    def send_fire_alert_to_mobile(self, screenshot_path, alert_type="fire", mobile_ip=None, port=None):
        """Send fire alert screenshot and info to mobile app via HTTP POST."""
        import requests
        
        mobile_ip = mobile_ip or os.getenv("MOBILE_ALERT_IP", "192.168.1.4")
        port = port or int(os.getenv("ALERT_API_PORT", 58766))
        
        url = f"http://{mobile_ip}:{port}/fire_alert"
        with open(screenshot_path, "rb") as img_file:
            files = {"screenshot": img_file}
            data = {"alert_type": alert_type}
            try:
                response = requests.post(url, files=files, data=data, timeout=2)
                print("Alert sent to mobile:", response.status_code)
            except Exception as e:
                print("Failed to send alert to mobile:", e)
    """YOLOv8-based fire and smoke detection system with alerts"""
    
    detection_result = pyqtSignal(str, np.ndarray, list, dict)  # camera_id, frame_with_boxes, detections, alert_info
    fire_alert = pyqtSignal(str, str, float, str)  # camera_id, alert_type ('fire'/'smoke'), confidence, alert_level
    alert_level_changed = pyqtSignal(str, str, str)  # camera_id, old_level, new_level
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        
        # Load config values
        self.detection_config = {}
        if self.config_manager:
            self.detection_config = self.config_manager.get_detection_config()
            
        self.model = None
        self.model_loaded = False
        self.detection_enabled = {}
        self.confidence_threshold = self.detection_config.get('fire_threshold', 0.5)
        self.min_area = 1000
        
        # Initialize Temporal Confidence Engine
        self.confidence_engine = TemporalConfidenceEngine(config_manager)
        
        # Alert system
        self.alert_cooldown = {}  # camera_id -> last_alert_time
        self.alert_cooldown_duration = 10  # seconds between alerts
        self.alert_sound_enabled = True
        self.previous_alert_levels = {}  # Track previous alert levels per camera
        
        # Performance optimization
        self.frame_skip = {}
        self.process_every_n_frames = self.detection_config.get('process_every_n_frames', 2)
        self.last_detection_time = {}
        self.last_detections = {}
        self.detection_threads = {}
        self.detection_queue = {}
        self.max_queue_size = 1

        # Night-mode preprocessing and temporal check
        self.night_preprocessing_enabled = self.detection_config.get('night_mode_enabled', True)
        self.temporal_check_enabled = self.detection_config.get('temporal_check_enabled', True)
        self.temporal_masks = {}  # camera_id -> deque of recent binary masks
        self.temporal_history = 5
        self.temporal_flicker_threshold = 0.02  # 2% of image area changes between frames
        
        # Fire/Smoke class mapping (adjust based on your model)
        self.fire_smoke_classes = {
            0: 'fire',
            1: 'smoke'
        }
        
        # Evidence snapshot system
        self.snapshot_config = self.config_manager.get_config('confidence_engine', {}) if config_manager else {}
        self.snapshots_enabled = self.snapshot_config.get('enable_snapshots', True)
        self.snapshot_dir = Path('snapshots')
        if self.snapshots_enabled:
            self.snapshot_dir.mkdir(exist_ok=True)
            print(f"📸 Evidence snapshot system enabled: {self.snapshot_dir.absolute()}")
        
        # Initialize pygame for alert sounds
        try:
            pygame.mixer.init()
            self.sound_initialized = True
        except:
            self.sound_initialized = False
            print("⚠️ Could not initialize sound system")
        
        # Load model in separate thread
        self.model_thread = threading.Thread(target=self.load_model)
        self.model_thread.daemon = True
        self.model_thread.start()
        
    def reload_config(self):
        """Reload configuration from ConfigManager"""
        if self.config_manager:
            print("🔄 Reloading FireSmokeDetector configuration...")
            self.detection_config = self.config_manager.get_detection_config()
            self.confidence_threshold = self.detection_config.get('fire_threshold', 0.5)
            self.process_every_n_frames = self.detection_config.get('process_every_n_frames', 2)
            self.night_preprocessing_enabled = self.detection_config.get('night_mode_enabled', True)
            self.temporal_check_enabled = self.detection_config.get('temporal_check_enabled', True)
            print(f"✅ FireSmokeDetector config reloaded: Conf={self.confidence_threshold}, Night={self.night_preprocessing_enabled}")

    def send_fire_alert_to_mobile(self, screenshot_path, alert_type="fire", mobile_ip=None, port=None):
        """Send fire alert screenshot and info to mobile app via HTTP POST."""
        import requests
        
        # Use config if arguments not provided
        if mobile_ip is None or port is None:
            if self.config_manager:
                net_config = self.config_manager.get_network_config()
                # Parse full URL if needed, but for now assuming direct URL in config
                mobile_url = net_config.get('mobile_app_url', f"http://{os.getenv('MOBILE_ALERT_IP', '192.168.1.4')}:{os.getenv('ALERT_API_PORT', 58766)}")
                url = f"{mobile_url}/fire_alert"
            else:
                # Fallback to defaults
                mobile_ip = mobile_ip or os.getenv("MOBILE_ALERT_IP", "192.168.1.4")
                port = port or int(os.getenv("ALERT_API_PORT", 58766))
                url = f"http://{mobile_ip}:{port}/fire_alert"
        else:
            url = f"http://{mobile_ip}:{port}/fire_alert"
            
        with open(screenshot_path, "rb") as img_file:
            files = {"screenshot": img_file}
            data = {"alert_type": alert_type}
            try:
                response = requests.post(url, files=files, data=data, timeout=2)
                print("Alert sent to mobile:", response.status_code)
            except Exception as e:
                print("Failed to send alert to mobile:", e)
    def set_nvr_mode(self, enabled):
        """Enable or disable NVR-only mode (optimizes for low-end devices)"""
        if enabled:
            print("🛑 Switching FireSmokeDetector to NVR Mode (unloading models)")
            self.unload_model()
        else:
            print("🔄 Switching FireSmokeDetector to Standard Mode (reloading model)")
            if not self.model_loaded:
                threading.Thread(target=self.load_model, daemon=True).start()

    def unload_model(self):
        """Unload the AI model to free resources"""
        self.model = None
        self.model_loaded = False
        if HAS_YOLO:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            import gc
            gc.collect()
        print("✅ Fire/Smoke model unloaded")

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def load_model(self):
        """Load YOLO model for fire and smoke detection"""
        try:
            print("🔥 Loading Fire/Smoke detection model...")
            start_time = time.time()
            
            if HAS_YOLO:
                # Look for models in models/ subdirectory relative to executable
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                models_dir = os.path.join(base_path, 'models')
                
                # Check for best_m.pt
                model_path = os.path.join(models_dir, 'best_m.pt')
                if not os.path.exists(model_path):
                     # Fallback for dev environment
                     model_path = 'best_m.pt'
                
                model_loaded = False
                try:
                    if os.path.exists(model_path):
                        self.model = YOLO(model_path)
                        print(f"✅ Loaded model: {model_path}")
                        model_loaded = True
                    else:
                        print(f"⚠️ Model file not found at: {model_path}")
                except Exception as e:
                    print(f"⚠️ Could not load {model_path}: {e}")
                
                if not model_loaded:
                    # Load default model and configure for fire detection
                    fallback_model_path = os.path.join(models_dir, 'yolov8n.pt')
                    if not os.path.exists(fallback_model_path):
                        fallback_model_path = 'yolov8n.pt'
                        
                    try:
                        if os.path.exists(fallback_model_path):
                            self.model = YOLO(fallback_model_path)
                            print(f"⚠️ Using general model from {fallback_model_path} - fire detection may be limited")
                            model_loaded = True
                        else:
                             # Last resort: try loading by name
                            print(f"⚠️ Fallback model not found at {fallback_model_path}, trying direct load...")
                            self.model = YOLO('yolov8n.pt')
                            print("⚠️ Using general model (direct load) - fire detection may be limited")
                            model_loaded = True
                    except Exception as e:
                         print(f"❌ Failed to load fallback model: {e}")

                if model_loaded:
                    # Optimize model for inference
                    try:
                        self.model.fuse()
                        
                        # Warm up the model
                        dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
                        for _ in range(3):
                            self.model(dummy_input, verbose=False)
                            
                        self.model_loaded = True
                        elapsed = time.time() - start_time
                        print(f"✅ Fire/Smoke detection model loaded in {elapsed:.2f} seconds")
                    except Exception as e:
                         print(f"⚠️ Error optimizing/warming up model: {e}")
                         # Still consider loaded if we got this far
                         self.model_loaded = True
                else:
                    print("❌ No model could be loaded. Fire detection disabled.")
                    self.model_loaded = False
            else:
                print("⚠️ YOLO not available - Fire/Smoke detection disabled")
                self.model_loaded = False
            
        except Exception as e:
            print(f"❌ Critical error loading Fire/Smoke detection model: {e}")
            self.model_loaded = False

    def set_night_preprocessing_enabled(self, enabled: bool):
        """Enable/disable night-specific preprocessing globally."""
        self.night_preprocessing_enabled = bool(enabled)
        print(f"🌙 Night preprocessing {'enabled' if enabled else 'disabled'}")

    def set_temporal_check_enabled(self, enabled: bool):
        """Enable/disable temporal flicker check to suppress static lights."""
        self.temporal_check_enabled = bool(enabled)
        print(f"🕒 Temporal flicker check {'enabled' if enabled else 'disabled'}")

    def _is_grayscale_like(self, frame: np.ndarray) -> bool:
        """Heuristic to detect grayscale/low-color frames.
        Returns True when the frame appears black & white (night mode).
        """
        try:
            if frame is None or frame.ndim < 2:
                return False
            if frame.ndim == 2:
                return True
            # For 3-channel: if channel differences are tiny, consider grayscale
            b, g, r = cv2.split(frame)
            diff_bg = cv2.absdiff(b, g)
            diff_br = cv2.absdiff(b, r)
            diff_gr = cv2.absdiff(g, r)
            mean_diff = (float(np.mean(diff_bg)) + float(np.mean(diff_br)) + float(np.mean(diff_gr))) / 3.0
            return mean_diff < 3.0  # very low color variance
        except Exception:
            return False

    def _night_preprocess(self, camera_id: str, frame_bgr: np.ndarray):
        """Apply CLAHE + bright-region masking for night fire detection.
        Returns processed_bgr, mask (uint8 0/255), flicker_score (0..1).
        """
        h, w = frame_bgr.shape[:2]
        # 1) Grayscale
        gray = frame_bgr if frame_bgr.ndim == 2 else cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        # 2) CLAHE contrast enhancement
        try:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray_eq = clahe.apply(gray)
        except Exception:
            gray_eq = cv2.equalizeHist(gray)
        # 3) Threshold bright regions
        p90 = float(np.percentile(gray_eq, 90))
        thresh_val = int(max(180, min(250, p90)))
        _, mask = cv2.threshold(gray_eq, thresh_val, 255, cv2.THRESH_BINARY)
        # Morphology to reduce noise and expand regions
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        # 4) Apply mask to original frame
        processed_bgr = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask)

        # Temporal flicker check (optional)
        flicker_score = 0.0
        if self.temporal_check_enabled:
            dq = self.temporal_masks.get(camera_id)
            if dq is None:
                dq = deque(maxlen=self.temporal_history)
                self.temporal_masks[camera_id] = dq
            if len(dq) > 0:
                prev = dq[-1]
                # XOR-like difference to measure change
                diff = cv2.absdiff(mask, prev)
                changed = float(np.count_nonzero(diff))
                flicker_score = changed / float(h * w)
            dq.append(mask)

        return processed_bgr, mask, flicker_score

    def enable_detection(self, camera_id, enabled=True):
        """Enable or disable fire/smoke detection for a specific camera"""
        self.detection_enabled[camera_id] = enabled
        
        if enabled:
            if camera_id not in self.frame_skip:
                self.frame_skip[camera_id] = 0
            if camera_id not in self.detection_queue:
                self.detection_queue[camera_id] = []
            if camera_id not in self.alert_cooldown:
                self.alert_cooldown[camera_id] = 0
                
            # Start detection thread if not already running
            if camera_id not in self.detection_threads or not self.detection_threads[camera_id].isRunning():
                self.detection_threads[camera_id] = FireSmokeDetectionThread(self, camera_id)
                self.detection_threads[camera_id].daemon = True
                self.detection_threads[camera_id].start()
        else:
            # Clean up resources when detection is disabled
            if camera_id in self.detection_queue:
                self.detection_queue[camera_id] = []
                
        print(f"🔥 Fire/Smoke detection {'enabled' if enabled else 'disabled'} for camera {camera_id}")

    def is_detection_enabled(self, camera_id):
        """Check if fire/smoke detection is enabled for a camera"""
        return self.detection_enabled.get(camera_id, False)

    def detect_fire_smoke(self, camera_id, frame):
        """Queue frame for fire/smoke detection"""
        if not self.model_loaded or not self.is_detection_enabled(camera_id):
            return frame, [], {}

        # Skip frames to reduce processing load
        if camera_id in self.frame_skip:
            self.frame_skip[camera_id] += 1
            if self.frame_skip[camera_id] < self.process_every_n_frames:
                # Return last detection results if available
                if camera_id in self.last_detections:
                    last_frame, last_detections, last_alert_info = self.last_detections[camera_id]
                    
                    # Create fresh copy of current frame
                    annotated_frame = frame.copy()
                    
                    # Draw last detections on new frame
                    for detection in last_detections:
                        self._draw_detection_box(annotated_frame, detection)
                    
                    # Draw alert info
                    self._draw_alert_info(annotated_frame, last_alert_info)
                    
                    return annotated_frame, last_detections, last_alert_info
                return frame, [], {}
            else:
                self.frame_skip[camera_id] = 0
        
        # Add frame to processing queue
        if camera_id in self.detection_queue:
            self.detection_queue[camera_id] = [frame.copy()]
        
        # Return last detection results if available
        if camera_id not in self.last_detections:
            return frame, [], {}
            
        last_frame, last_detections, last_alert_info = self.last_detections[camera_id]
        return last_frame, last_detections, last_alert_info

    def _process_detection(self, camera_id, frame):
        """Process fire/smoke detection in background thread"""
        if not self.model_loaded:
            return
            
        try:
            start_time = time.time()
            
            # Ensure frame is in BGR format (OpenCV default)
            frame_copy = frame.copy()
            # DO NOT convert to RGB here!
            
            # Decide if we should use night preprocessing
            use_night_preproc = self.night_preprocessing_enabled and self._is_grayscale_like(frame_copy)

            # Resize for faster processing if needed
            h, w = frame_copy.shape[:2]
            resized = False
            new_h, new_w = h, w
            if h > 720 or w > 1280:
                scale = min(720 / h, 1280 / w)
                new_h, new_w = int(h * scale), int(w * scale)
                resized = True

            # Apply night preprocessing (CLAHE + bright mask) when applicable
            flicker_score = 0.0
            if use_night_preproc:
                processed_bgr, mask, flicker_score = self._night_preprocess(camera_id, frame_copy)
                resized_frame = cv2.resize(processed_bgr, (new_w, new_h)) if resized else processed_bgr
            else:
                resized_frame = cv2.resize(frame_copy, (new_w, new_h)) if resized else frame_copy
            
            # Run detection
            results = self.model(resized_frame, verbose=False)
            
            detections = []
            alert_info = {'fire_count': 0, 'smoke_count': 0, 'max_confidence': 0.0, 'alert_type': None}
            annotated_frame = frame_copy.copy()  # This is BGR
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Check if it's fire or smoke (adjust class IDs based on your model)
                        detection_type = None
                        if class_id in self.fire_smoke_classes:
                            detection_type = self.fire_smoke_classes[class_id]
                        elif class_id == 0 and confidence >= self.confidence_threshold:
                            # If using general model, assume class 0 could be fire-related
                            detection_type = 'fire'
                        
                        if detection_type and confidence >= self.confidence_threshold:
                            # Get coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                            
                            # Scale back if resized
                            if resized:
                                scale_factor = w / new_w
                                x1, x2 = int(x1 * scale_factor), int(x2 * scale_factor)
                                y1, y2 = int(y1 * scale_factor), int(y2 * scale_factor)
                            
                            area = (x2 - x1) * (y2 - y1)
                            if area < self.min_area:
                                continue
                                
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            
                            detection = {
                                'bbox': (x1, y1, x2, y2),
                                'center': (center_x, center_y),
                                'confidence': confidence,
                                'type': detection_type,
                                'class_id': class_id
                            }
                            
                            detections.append(detection)
                            
                            # Update alert info
                            if detection_type == 'fire':
                                alert_info['fire_count'] += 1
                            elif detection_type == 'smoke':
                                alert_info['smoke_count'] += 1
                            
                            if confidence > alert_info['max_confidence']:
                                alert_info['max_confidence'] = confidence
                                alert_info['alert_type'] = detection_type
                            
                            # Draw detection box (on BGR image)
                            self._draw_detection_box(annotated_frame, detection)
            
            # Optional temporal flicker suppression for static bright objects (night mode)
            if use_night_preproc and self.temporal_check_enabled:
                # If there's little change across frames and confidence isn't very high, suppress
                if flicker_score < self.temporal_flicker_threshold and alert_info['max_confidence'] < max(0.8, self.confidence_threshold + 0.2):
                    detections = []
                    alert_info = {'fire_count': 0, 'smoke_count': 0, 'max_confidence': 0.0, 'alert_type': None}

            # Pass detections to confidence engine for temporal analysis
            current_time = time.time()
            temporal_confidence, alert_level = self.confidence_engine.add_detection(
                camera_id=camera_id,
                detections=detections,
                frame_timestamp=current_time,
                is_night=use_night_preproc
            )
            
            # Update alert info with temporal confidence and alert level
            alert_info['temporal_confidence'] = temporal_confidence
            alert_info['alert_level'] = alert_level.value
            alert_info['is_night_mode'] = use_night_preproc
            
            # Check for alert level changes
            prev_level = self.previous_alert_levels.get(camera_id, AlertLevel.NONE)
            if alert_level != prev_level:
                self.alert_level_changed.emit(camera_id, prev_level.value, alert_level.value)
                self.previous_alert_levels[camera_id] = alert_level
            
            # Capture evidence snapshot for WARNING or CRITICAL alerts
            if self.snapshots_enabled and alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
                snapshot_config = self.snapshot_config
                if ((alert_level == AlertLevel.WARNING and snapshot_config.get('snapshot_on_warning', True)) or
                    (alert_level == AlertLevel.CRITICAL and snapshot_config.get('snapshot_on_critical', True))):
                    self._capture_evidence_snapshot(
                        camera_id=camera_id,
                        frame=annotated_frame,
                        detections=detections,
                        alert_level=alert_level.value,
                        confidence=temporal_confidence,
                        is_night=use_night_preproc
                    )

            # Handle alerts based on alert level
            if alert_level != AlertLevel.NONE:
                self._handle_alert(camera_id, alert_info, alert_level)
            
            # Draw alert information (on BGR image)
            self._draw_alert_info(annotated_frame, alert_info)
            
            # Store results
            self.last_detections[camera_id] = (annotated_frame, detections, alert_info)
            self.last_detection_time[camera_id] = time.time()
            
            # Calculate processing time
            elapsed = time.time() - start_time
            fps = 1.0 / elapsed if elapsed > 0 else 0
            
            if detections:
                print(f"🔥 Fire/Smoke detection for camera {camera_id}: {len(detections)} detections, "
                      f"temporal_conf={temporal_confidence:.2f}, level={alert_level.value}, "
                      f"{elapsed:.3f}s ({fps:.1f} FPS)")
            
            # Emit signal with results (BGR image)
            self.detection_result.emit(camera_id, annotated_frame, detections, alert_info)
            
        except Exception as e:
            print(f"❌ Fire/Smoke detection error for camera {camera_id}: {e}")

    def _draw_detection_box(self, frame, detection):
        """Draw bounding box for fire/smoke detection"""
        x1, y1, x2, y2 = detection['bbox']
        confidence = detection['confidence']
        detection_type = detection['type']
        
        # Color coding: Red for fire, Gray for smoke
        if detection_type == 'fire':
            color = (0, 0, 255)  # Red
            label = f"🔥 FIRE {confidence:.2f}"
        else:
            color = (128, 128, 128)  # Gray
            label = f"💨 SMOKE {confidence:.2f}"
        
        # Draw thicker box for high confidence detections
        thickness = 3 if confidence > 0.7 else 2
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Draw label background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        label_size = cv2.getTextSize(label, font, font_scale, 2)[0]
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), 2)

    def _draw_alert_info(self, frame, alert_info):
        """Draw alert information on frame"""
        if alert_info['fire_count'] > 0 or alert_info['smoke_count'] > 0:
            h, w = frame.shape[:2]
            
            # Alert banner
            banner_height = 60
            cv2.rectangle(frame, (0, 0), (w, banner_height), (0, 0, 255), -1)
            
            # Alert text
            alert_text = "🚨 FIRE/SMOKE DETECTED! 🚨"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            text_size = cv2.getTextSize(alert_text, font, font_scale, 2)[0]
            text_x = (w - text_size[0]) // 2
            text_y = (banner_height + text_size[1]) // 2
            
            cv2.putText(frame, alert_text, (text_x, text_y), font, font_scale, (255, 255, 255), 2)
            
            # Detection counts
            count_text = f"Fire: {alert_info['fire_count']} | Smoke: {alert_info['smoke_count']}"
            count_size = cv2.getTextSize(count_text, font, 0.5, 1)[0]
            count_x = w - count_size[0] - 10
            count_y = h - 20
            
            cv2.rectangle(frame, (count_x - 5, count_y - count_size[1] - 5), 
                         (count_x + count_size[0] + 5, count_y + 5), (0, 0, 0), -1)
            cv2.putText(frame, count_text, (count_x, count_y), font, 0.5, (255, 255, 255), 1)

    def _handle_alert(self, camera_id, alert_info, alert_level):
        """Handle fire/smoke alert with alert level"""
        current_time = time.time()
        
        # Apply level-specific cooldown
        cooldown_duration = self.alert_cooldown_duration
        if alert_level == AlertLevel.CRITICAL:
            cooldown_duration = self.snapshot_config.get('critical_cooldown_seconds', 30)
        elif alert_level == AlertLevel.WARNING:
            cooldown_duration = self.snapshot_config.get('warning_cooldown_seconds', 15)
        
        # Check cooldown
        if (camera_id in self.alert_cooldown and 
            current_time - self.alert_cooldown[camera_id] < cooldown_duration):
            return
        
        # Update cooldown
        self.alert_cooldown[camera_id] = current_time
        
        # Emit alert signal with alert level
        if alert_info.get('alert_type'):
            self.fire_alert.emit(
                camera_id, 
                alert_info['alert_type'], 
                alert_info.get('temporal_confidence', alert_info.get('max_confidence', 0.0)),
                alert_level.value
            )
            
            # Play alert sound only for WARNING and CRITICAL
            if self.alert_sound_enabled and alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
                self._play_alert_sound(alert_info['alert_type'])
            
            print(f"🚨 {alert_level.value} ALERT: {alert_info['alert_type'].upper()} detected on camera {camera_id} "
                  f"(temporal_confidence: {alert_info.get('temporal_confidence', 0.0):.2f})")

    def _play_alert_sound(self, alert_type):
        """Play alert sound"""
        if not self.sound_initialized:
            return
        
        try:
            # You can add custom sound files here
            sound_files = {
                'fire': 'fire_alarm.wav',
                'smoke': 'smoke_alarm.wav'
            }
            
            sound_file = sound_files.get(alert_type)
            if sound_file and os.path.exists(sound_file):
                pygame.mixer.Sound(sound_file).play()
            else:
                # Generate beep sound as fallback
                frequency = 1000 if alert_type == 'fire' else 800
                duration = 0.5
                sample_rate = 22050
                frames = int(duration * sample_rate)
                
                # Create stereo array (2 channels)
                arr = np.zeros((frames, 2), dtype=np.int16)
                
                for i in range(frames):
                    sample = int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
                    arr[i, 0] = sample  # Left channel
                    arr[i, 1] = sample  # Right channel
            
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
                
        except Exception as e:
            print(f"⚠️ Could not play alert sound: {e}")

    def set_confidence_threshold(self, threshold):
        """Set detection confidence threshold"""
        self.confidence_threshold = max(0.1, min(1.0, threshold))
        print(f"🎯 Fire/Smoke confidence threshold set to {self.confidence_threshold}")

    def set_alert_sound_enabled(self, enabled):
        """Enable/disable alert sounds"""
        self.alert_sound_enabled = enabled
        print(f"🔊 Alert sounds {'enabled' if enabled else 'disabled'}")

    def reset_alert_cooldown(self, camera_id):
        """Reset alert cooldown for a camera"""
        if camera_id in self.alert_cooldown:
            self.alert_cooldown[camera_id] = 0
    
    def _capture_evidence_snapshot(self, camera_id, frame, detections, alert_level, confidence, is_night):
        """
        Capture evidence snapshot for WARNING or CRITICAL alerts.
        
        Args:
            camera_id: Camera identifier
            frame: Annotated frame with detections
            detections: List of detection dicts
            alert_level: Alert level string (WARNING/CRITICAL)
            confidence: Temporal confidence score
            is_night: Whether night mode was active
        """
        try:
            # Create camera-specific directory
            camera_snapshot_dir = self.snapshot_dir / camera_id
            camera_snapshot_dir.mkdir(exist_ok=True)
            
            # Generate timestamp-based filename
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Save frame
            frame_filename = f"{timestamp_str}_{alert_level}.jpg"
            frame_path = camera_snapshot_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)
            
            # Prepare metadata
            summary = self.confidence_engine.get_detection_summary(camera_id)
            metadata = {
                "camera_id": camera_id,
                "timestamp": timestamp.isoformat(),
                "alert_level": alert_level,
                "confidence_score": confidence,
                "temporal_detections": summary.get('detections_in_window', 0),
                "window_size": summary.get('window_size', 0),
                "detections": [
                    {
                        "bbox": list(det['bbox']),
                        "confidence": det['confidence'],
                        "type": det['type'],
                        "class_id": det['class_id']
                    }
                    for det in detections
                ],
                "is_night_mode": is_night,
                "rules_applied": ["bbox_size", "movement_consistency"]
            }
            
            # Save metadata JSON
            metadata_filename = f"{timestamp_str}_{alert_level}.json"
            metadata_path = camera_snapshot_dir / metadata_filename
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📸 Evidence snapshot captured: {frame_path.name} (level={alert_level}, conf={confidence:.2f})")
            
            # Cleanup old snapshots
            self._cleanup_old_snapshots(camera_id)
            
        except Exception as e:
            print(f"⚠️ Failed to capture evidence snapshot for camera {camera_id}: {e}")
    
    def _cleanup_old_snapshots(self, camera_id):
        """
        Clean up old snapshots based on retention policy.
        
        Args:
            camera_id: Camera identifier
        """
        try:
            camera_snapshot_dir = self.snapshot_dir / camera_id
            if not camera_snapshot_dir.exists():
                return
            
            # Get retention settings
            retention_days = self.snapshot_config.get('snapshot_retention_days', 30)
            max_snapshots = self.snapshot_config.get('max_snapshots_per_camera', 1000)
            
            # Get all snapshot files (both .jpg and .json)
            snapshot_files = sorted(
                camera_snapshot_dir.glob("*.jpg"),
                key=lambda p: p.stat().st_mtime
            )
            
            # Delete by age
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            for snapshot_file in snapshot_files:
                file_time = datetime.fromtimestamp(snapshot_file.stat().st_mtime)
                if file_time < cutoff_time:
                    # Delete both image and metadata
                    snapshot_file.unlink()
                    metadata_file = snapshot_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            # Delete by count (keep only most recent)
            snapshot_files = sorted(
                camera_snapshot_dir.glob("*.jpg"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(snapshot_files) > max_snapshots:
                for old_file in snapshot_files[max_snapshots:]:
                    old_file.unlink()
                    metadata_file = old_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                        
        except Exception as e:
            print(f"⚠️ Failed to cleanup snapshots for camera {camera_id}: {e}")


class FireSmokeDetectionThread(BaseWorker):
    """Thread for running fire/smoke detection in background"""
    
    def __init__(self, detector, camera_id):
        super().__init__(f"FireDetection_{camera_id}")
        self.detector = detector
        self.camera_id = camera_id
        
    def work(self):
        """Main thread loop - called by BaseWorker.run()"""
        print(f"🧵 Starting fire/smoke detection thread for camera {self.camera_id}")
        
        while self.is_running() and self.detector.is_detection_enabled(self.camera_id):
            # Check if there's a frame to process
            if (self.camera_id in self.detector.detection_queue and 
                len(self.detector.detection_queue[self.camera_id]) > 0):
                
                # Get the latest frame
                frame = self.detector.detection_queue[self.camera_id].pop(0)
                
                # Process the frame
                self.detector._process_detection(self.camera_id, frame)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.02)  # Slightly longer sleep for fire detection
            
        print(f"🛑 Fire/smoke detection thread for camera {self.camera_id} stopped")
