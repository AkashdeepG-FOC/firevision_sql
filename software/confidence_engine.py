"""
AI Confidence & Decision Engine for Fire Detection

Provides temporal analysis, multi-stage alerting, and false positive suppression
to dramatically reduce false alarms and improve detection reliability.

Features:
- Temporal confidence voting (sliding window)
- Multi-stage alerts (INFO → WARNING → CRITICAL)
- False positive suppression rules
- Day/Night behavior adaptation
- Alert hysteresis and cooldown
- Evidence tracking for explainability
"""

import time
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class AlertLevel(Enum):
    """Alert severity levels with increasing evidence requirements"""
    NONE = "NONE"
    INFO = "INFO"           # Low confidence, monitoring
    WARNING = "WARNING"     # Likely fire, notify operator
    CRITICAL = "CRITICAL"   # Confirmed fire, trigger alarms


@dataclass
class DetectionEvidence:
    """Single-frame detection evidence"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    confidence: float
    detection_type: str  # 'fire' or 'smoke'
    class_id: int
    timestamp: float
    frame_index: int = 0
    
    def bbox_area(self) -> int:
        """Calculate bounding box area"""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)
    
    def bbox_center_distance(self, other: 'DetectionEvidence') -> float:
        """Calculate distance between bbox centers"""
        dx = self.center[0] - other.center[0]
        dy = self.center[1] - other.center[1]
        return np.sqrt(dx*dx + dy*dy)


@dataclass
class CameraConfidenceState:
    """Temporal confidence state for a single camera"""
    camera_id: str
    detection_history: deque = field(default_factory=lambda: deque(maxlen=10))
    current_alert_level: AlertLevel = AlertLevel.NONE
    last_alert_time: float = 0.0
    last_critical_time: float = 0.0
    last_warning_time: float = 0.0
    frames_since_detection: int = 0
    frames_at_current_level: int = 0
    total_frames_processed: int = 0
    is_night_mode: bool = False
    
    # Hysteresis tracking
    consecutive_low_confidence_frames: int = 0
    last_high_confidence_time: float = 0.0


class TemporalConfidenceEngine:
    """
    Main confidence engine that analyzes detection patterns over time
    to reduce false positives and provide multi-stage alerting.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the confidence engine.
        
        Args:
            config_manager: ConfigManager instance for loading settings
        """
        self.config_manager = config_manager
        self.camera_states: Dict[str, CameraConfidenceState] = {}
        
        # Load configuration
        self._load_config()
        
        print("✅ Temporal Confidence Engine initialized")
    
    def _load_config(self):
        """Load configuration from ConfigManager"""
        if self.config_manager:
            config = self.config_manager.get_config('confidence_engine', {})
        else:
            config = {}
        
        # Temporal Analysis
        self.temporal_window_size = config.get('temporal_window_size', 5)
        self.min_detections_for_warning = config.get('min_detections_for_warning', 3)
        self.min_detections_for_critical = config.get('min_detections_for_critical', 5)
        
        # Alert Thresholds
        self.info_confidence_threshold = config.get('info_confidence_threshold', 0.4)
        self.warning_confidence_threshold = config.get('warning_confidence_threshold', 0.6)
        self.critical_confidence_threshold = config.get('critical_confidence_threshold', 0.75)
        
        # False Positive Suppression
        self.min_bbox_area = config.get('min_bbox_area', 1000)
        self.min_bbox_width = config.get('min_bbox_width', 30)
        self.min_bbox_height = config.get('min_bbox_height', 30)
        self.max_bbox_movement = config.get('max_bbox_movement', 50)
        self.min_flicker_stability = config.get('min_flicker_stability', 0.7)
        self.enable_color_validation = config.get('enable_color_validation', True)
        self.min_fire_color_ratio = config.get('min_fire_color_ratio', 0.3)
        
        # Day/Night Behavior
        self.day_confidence_multiplier = config.get('day_confidence_multiplier', 1.0)
        self.night_confidence_multiplier = config.get('night_confidence_multiplier', 0.85)
        self.night_temporal_window_size = config.get('night_temporal_window_size', 7)
        
        # Alert Hysteresis
        self.critical_cooldown_seconds = config.get('critical_cooldown_seconds', 30)
        self.warning_cooldown_seconds = config.get('warning_cooldown_seconds', 15)
        self.downgrade_stability_frames = config.get('downgrade_stability_frames', 10)
        
        print(f"🔧 Confidence Engine Config: Window={self.temporal_window_size}, "
              f"Thresholds=({self.info_confidence_threshold}/{self.warning_confidence_threshold}/"
              f"{self.critical_confidence_threshold})")
    
    def reload_config(self):
        """Reload configuration from ConfigManager"""
        print("🔄 Reloading Confidence Engine configuration...")
        self._load_config()
    
    def _get_or_create_state(self, camera_id: str) -> CameraConfidenceState:
        """Get or create confidence state for a camera"""
        if camera_id not in self.camera_states:
            # Set appropriate window size based on config
            window_size = self.temporal_window_size
            state = CameraConfidenceState(camera_id=camera_id)
            state.detection_history = deque(maxlen=window_size)
            self.camera_states[camera_id] = state
        return self.camera_states[camera_id]
    
    def set_night_mode(self, camera_id: str, is_night: bool):
        """
        Set night mode for a camera, adjusting temporal window size.
        
        Args:
            camera_id: Camera identifier
            is_night: True if night mode detected
        """
        state = self._get_or_create_state(camera_id)
        
        if state.is_night_mode != is_night:
            state.is_night_mode = is_night
            
            # Adjust window size for night mode
            new_window_size = self.night_temporal_window_size if is_night else self.temporal_window_size
            
            # Create new deque with updated size, preserving recent history
            old_history = list(state.detection_history)
            state.detection_history = deque(old_history[-new_window_size:], maxlen=new_window_size)
            
            print(f"🌙 Camera {camera_id}: Night mode {'enabled' if is_night else 'disabled'}, "
                  f"window size={new_window_size}")
    
    def add_detection(self, camera_id: str, detections: List[Dict], 
                     frame_timestamp: float, is_night: bool = False) -> Tuple[float, AlertLevel]:
        """
        Add new frame detections and calculate temporal confidence.
        
        Args:
            camera_id: Camera identifier
            detections: List of detection dicts from YOLO
            frame_timestamp: Timestamp of the frame
            is_night: Whether this is night mode
            
        Returns:
            Tuple of (confidence_score, alert_level)
        """
        state = self._get_or_create_state(camera_id)
        state.total_frames_processed += 1
        
        # Update night mode if changed
        if state.is_night_mode != is_night:
            self.set_night_mode(camera_id, is_night)
        
        # Convert detections to evidence objects
        evidence_list = []
        for det in detections:
            evidence = DetectionEvidence(
                bbox=det['bbox'],
                center=det['center'],
                confidence=det['confidence'],
                detection_type=det['type'],
                class_id=det['class_id'],
                timestamp=frame_timestamp,
                frame_index=state.total_frames_processed
            )
            
            # Apply false positive rules
            if self._passes_false_positive_rules(evidence, state):
                evidence_list.append(evidence)
        
        # Add to history (empty list if no valid detections)
        state.detection_history.append(evidence_list)
        
        # Update frames since detection counter
        if evidence_list:
            state.frames_since_detection = 0
        else:
            state.frames_since_detection += 1
        
        # Calculate temporal confidence and alert level
        confidence_score = self._calculate_temporal_confidence(state)
        new_alert_level = self._determine_alert_level(state, confidence_score, frame_timestamp)
        
        # Handle alert level transitions
        if new_alert_level != state.current_alert_level:
            self._handle_alert_transition(state, new_alert_level, frame_timestamp)
        else:
            state.frames_at_current_level += 1
        
        return confidence_score, state.current_alert_level
    
    def _passes_false_positive_rules(self, evidence: DetectionEvidence, 
                                     state: CameraConfidenceState) -> bool:
        """
        Apply false positive suppression rules.
        
        Args:
            evidence: Detection evidence to evaluate
            state: Camera state for temporal checks
            
        Returns:
            True if detection passes all enabled rules
        """
        # Rule 1: Minimum bounding box size
        x1, y1, x2, y2 = evidence.bbox
        width = x2 - x1
        height = y2 - y1
        area = evidence.bbox_area()
        
        if area < self.min_bbox_area:
            return False
        
        if width < self.min_bbox_width or height < self.min_bbox_height:
            return False
        
        # Rule 2: Movement consistency (check against recent detections)
        if len(state.detection_history) > 0:
            recent_detections = [d for frame in state.detection_history for d in frame]
            
            if recent_detections:
                # Find closest previous detection
                min_distance = float('inf')
                for prev_det in recent_detections[-5:]:  # Check last 5 detections
                    distance = evidence.bbox_center_distance(prev_det)
                    min_distance = min(min_distance, distance)
                
                # If movement is too large, might be a different object
                if min_distance > self.max_bbox_movement:
                    # Allow if confidence is very high
                    if evidence.confidence < 0.8:
                        return False
        
        # Rule 3: Flicker stability (implicit - handled by temporal voting)
        # Objects that flicker in/out will have lower temporal confidence
        
        return True
    
    def _calculate_temporal_confidence(self, state: CameraConfidenceState) -> float:
        """
        Calculate temporal confidence score based on detection history.
        
        Args:
            state: Camera confidence state
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not state.detection_history:
            return 0.0
        
        # Count frames with detections
        frames_with_detections = sum(1 for frame in state.detection_history if frame)
        total_frames = len(state.detection_history)
        
        if total_frames == 0:
            return 0.0
        
        # Detection frequency score
        detection_frequency = frames_with_detections / total_frames
        
        # Average confidence of recent detections
        all_confidences = [det.confidence for frame in state.detection_history 
                          for det in frame]
        
        if not all_confidences:
            return 0.0
        
        avg_confidence = np.mean(all_confidences)
        max_confidence = np.max(all_confidences)
        
        # Bbox consistency score (lower variance = more stable)
        bbox_consistency = self._calculate_bbox_consistency(state)
        
        # Class stability (all same type = more stable)
        class_stability = self._calculate_class_stability(state)
        
        # Weighted combination
        temporal_score = (
            detection_frequency * 0.35 +  # How often detected
            avg_confidence * 0.30 +        # Average confidence
            max_confidence * 0.15 +        # Peak confidence
            bbox_consistency * 0.10 +      # Position stability
            class_stability * 0.10         # Type consistency
        )
        
        # Apply day/night multiplier
        if state.is_night_mode:
            temporal_score *= self.night_confidence_multiplier
        else:
            temporal_score *= self.day_confidence_multiplier
        
        return min(1.0, temporal_score)
    
    def _calculate_bbox_consistency(self, state: CameraConfidenceState) -> float:
        """Calculate how consistent bounding box positions are"""
        all_centers = [det.center for frame in state.detection_history for det in frame]
        
        if len(all_centers) < 2:
            return 1.0  # Perfect consistency if only one detection
        
        # Calculate variance in center positions
        centers_array = np.array(all_centers)
        variance = np.var(centers_array, axis=0).mean()
        
        # Convert variance to consistency score (lower variance = higher consistency)
        # Normalize by max expected movement
        consistency = 1.0 / (1.0 + variance / (self.max_bbox_movement ** 2))
        
        return consistency
    
    def _calculate_class_stability(self, state: CameraConfidenceState) -> float:
        """Calculate how consistent detection types are"""
        all_types = [det.detection_type for frame in state.detection_history for det in frame]
        
        if not all_types:
            return 0.0
        
        # Count most common type
        type_counts = {}
        for t in all_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        
        most_common_count = max(type_counts.values())
        stability = most_common_count / len(all_types)
        
        return stability
    
    def _determine_alert_level(self, state: CameraConfidenceState, 
                               confidence_score: float, current_time: float) -> AlertLevel:
        """
        Determine alert level based on temporal confidence and detection count.
        
        Args:
            state: Camera confidence state
            confidence_score: Calculated temporal confidence
            current_time: Current timestamp
            
        Returns:
            Appropriate alert level
        """
        # Count recent detections
        frames_with_detections = sum(1 for frame in state.detection_history if frame)
        
        # Check cooldown periods
        time_since_critical = current_time - state.last_critical_time
        time_since_warning = current_time - state.last_warning_time
        
        # CRITICAL: Sustained high confidence detections
        if (frames_with_detections >= self.min_detections_for_critical and
            confidence_score >= self.critical_confidence_threshold):
            # Respect cooldown
            if time_since_critical < self.critical_cooldown_seconds:
                return AlertLevel.WARNING  # Downgrade during cooldown
            return AlertLevel.CRITICAL
        
        # WARNING: Moderate confidence or detection count
        if (frames_with_detections >= self.min_detections_for_warning and
            confidence_score >= self.warning_confidence_threshold):
            # Respect cooldown
            if time_since_warning < self.warning_cooldown_seconds:
                return AlertLevel.INFO  # Downgrade during cooldown
            return AlertLevel.WARNING
        
        # INFO: Low confidence detections
        if confidence_score >= self.info_confidence_threshold:
            return AlertLevel.INFO
        
        # NONE: No significant detections
        return AlertLevel.NONE
    
    def _handle_alert_transition(self, state: CameraConfidenceState, 
                                 new_level: AlertLevel, current_time: float):
        """
        Handle alert level transitions with hysteresis.
        
        Args:
            state: Camera confidence state
            new_level: New alert level
            current_time: Current timestamp
        """
        old_level = state.current_alert_level
        
        # Apply hysteresis for downgrades
        if new_level.value < old_level.value:  # Downgrade
            state.consecutive_low_confidence_frames += 1
            
            # Require sustained low confidence before downgrading
            if state.consecutive_low_confidence_frames < self.downgrade_stability_frames:
                return  # Don't downgrade yet
        else:
            # Reset hysteresis counter on upgrade or same level
            state.consecutive_low_confidence_frames = 0
        
        # Update state
        state.current_alert_level = new_level
        state.frames_at_current_level = 0
        
        # Update timestamps
        if new_level == AlertLevel.CRITICAL:
            state.last_critical_time = current_time
            state.last_alert_time = current_time
        elif new_level == AlertLevel.WARNING:
            state.last_warning_time = current_time
            state.last_alert_time = current_time
        
        print(f"🚨 Camera {state.camera_id}: Alert level changed {old_level.value} → {new_level.value}")
    
    def get_confidence_score(self, camera_id: str) -> float:
        """Get current temporal confidence score for a camera"""
        if camera_id not in self.camera_states:
            return 0.0
        
        state = self.camera_states[camera_id]
        return self._calculate_temporal_confidence(state)
    
    def get_alert_level(self, camera_id: str) -> AlertLevel:
        """Get current alert level for a camera"""
        if camera_id not in self.camera_states:
            return AlertLevel.NONE
        
        return self.camera_states[camera_id].current_alert_level
    
    def get_detection_summary(self, camera_id: str) -> Dict:
        """
        Get detailed detection summary for a camera.
        
        Returns:
            Dictionary with detection statistics and evidence
        """
        if camera_id not in self.camera_states:
            return {
                'camera_id': camera_id,
                'alert_level': AlertLevel.NONE.value,
                'confidence_score': 0.0,
                'frames_processed': 0,
                'detections_in_window': 0
            }
        
        state = self.camera_states[camera_id]
        confidence = self._calculate_temporal_confidence(state)
        
        frames_with_detections = sum(1 for frame in state.detection_history if frame)
        total_detections = sum(len(frame) for frame in state.detection_history)
        
        return {
            'camera_id': camera_id,
            'alert_level': state.current_alert_level.value,
            'confidence_score': confidence,
            'frames_processed': state.total_frames_processed,
            'detections_in_window': frames_with_detections,
            'total_detections': total_detections,
            'window_size': len(state.detection_history),
            'is_night_mode': state.is_night_mode,
            'frames_at_current_level': state.frames_at_current_level,
            'frames_since_detection': state.frames_since_detection
        }
    
    def reset_camera(self, camera_id: str):
        """Reset confidence state for a camera"""
        if camera_id in self.camera_states:
            del self.camera_states[camera_id]
            print(f"🔄 Reset confidence state for camera {camera_id}")
    
    def reset_all(self):
        """Reset all camera states"""
        self.camera_states.clear()
        print("🔄 Reset all camera confidence states")
