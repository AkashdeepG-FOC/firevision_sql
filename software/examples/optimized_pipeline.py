import cv2
import time
import threading
import queue
import numpy as np
from ultralytics import YOLO

class CameraStreamThread:
    """
    A dedicated thread for continuously capturing frames from a camera (webcam or RTSP).
    This ensures that cv2.VideoCapture.read() doesn't block the AI inference, and 
    vice-versa, preventing lag and RTSP stream corruption dropping.
    """
    def __init__(self, camera_id, source):
        self.camera_id = camera_id
        self.source = source
        self.capture = cv2.VideoCapture(source)
        
        # A queue of size 1 ensures we ONLY ever process the absolutely newest frame. 
        # Older frames are dropped if inference is still running.
        self.frame_queue = queue.Queue(maxsize=1)
        self.running = True
        
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        
    def start(self):
        self.thread.start()
        
    def _capture_loop(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print(f"Warning: Camera {self.camera_id} disconnected. Reconnecting...")
                time.sleep(1)
                self.capture = cv2.VideoCapture(self.source)
                continue
                
            # If the queue is full (AI is busy), drop the old frame to make room for this new one.
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Put the newest frame into the queue
            self.frame_queue.put(frame)
            
            # Small sleep to prevent CPU spinning when pulling frames extremely fast
            time.sleep(0.005)

    def stop(self):
        self.running = False
        self.thread.join()
        if self.capture.isOpened():
            self.capture.release()

class AIDetectionWorker:
    """
    A dedicated thread that pulls the latest frame from the CameraStreamThread queue,
    resizes it, and runs YOLO inference at a controlled interval (e.g., 1 second).
    """
    def __init__(self, model_path, camera_streams, detection_interval=1.0):
        self.model = YOLO(model_path)
        self.camera_streams = camera_streams  # List of CameraStreamThread objects
        
        # Optimization: run detection every exactly N seconds instead of every frame.
        self.detection_interval = detection_interval 
        self.last_detection_time = {stream.camera_id: 0 for stream in camera_streams}
        
        # Cache the latest bounding boxes so we can draw them even when skipping inference
        self.cached_detections = {stream.camera_id: [] for stream in camera_streams}
        
        self.running = True
        self.thread = threading.Thread(target=self._inference_loop, daemon=True)
    
    def start(self):
        self.thread.start()
        
    def _inference_loop(self):
        while self.running:
            current_time = time.time()
            
            for stream in self.camera_streams:
                # 1. Skip frames logic based on time
                if current_time - self.last_detection_time[stream.camera_id] >= self.detection_interval:
                    if not stream.frame_queue.empty():
                        frame = stream.frame_queue.get()
                        
                        # 2. Resize frame before detection to reduce computation (e.g., 640x640)
                        original_h, original_w = frame.shape[:2]
                        # Resizing down for performance
                        resized_frame = cv2.resize(frame, (640, 640))
                        
                        # 3. Process AI without changing the existing model
                        results = self.model(resized_frame, verbose=False)
                        
                        # 4. Map the bounding boxes back to the original image dimensions
                        mapped_boxes = []
                        for result in results:
                            boxes = result.boxes
                            if boxes is not None:
                                for box in boxes:
                                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                                    confidence = float(box.conf[0])
                                    class_id = int(box.cls[0])
                                    
                                    # Scale coordinates back up
                                    scale_x = original_w / 640
                                    scale_y = original_h / 640
                                    mapped_box = [
                                        int(x1 * scale_x), int(y1 * scale_y),
                                        int(x2 * scale_x), int(y2 * scale_y),
                                        confidence, class_id
                                    ]
                                    mapped_boxes.append(mapped_box)
                        
                        # Cache the new results
                        self.cached_detections[stream.camera_id] = mapped_boxes
                        self.last_detection_time[stream.camera_id] = current_time
                        
            # Sleep so the worker doesn't spin endlessly during intervals
            time.sleep(0.01)
            
    def stop(self):
        self.running = False
        self.thread.join()

def display_results(camera_streams, ai_worker):
    """
    Main loop purely for displaying the cached results onto the fresh frames.
    Because cv2.imshow runs here (main thread), it doesn't interrupt the AI or camera capturing.
    """
    while True:
        for stream in camera_streams:
            if not stream.frame_queue.empty():
                # We peek/grab the latest frame without emptying it if needed, 
                # but it's okay to just get it. 
                # Wait, the AI worker dequeues it. Instead, we can let the Display loop use the most recent frame
                # Or we can put the display logic in the CameraStream loop itself to broadcast.
                # For simplicity, we just safely grab a copy if it's there.
                frame = stream.frame_queue.queue[0] if not stream.frame_queue.empty() else None
                
                if frame is not None:
                    display_frame = frame.copy()
                    
                    # Get cached detections and draw them (illusion of real-time tracking)
                    detections = ai_worker.cached_detections[stream.camera_id]
                    for det in detections:
                        x1, y1, x2, y2, conf, cls = det
                        
                        color = (0, 0, 255) if cls == 0 else (128, 128, 128) # Red for Fire, Grey for Smoke
                        label = f"Class {cls}: {conf:.2f}"
                        
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(display_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
                    cv2.imshow(f"Camera {stream.camera_id}", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == "__main__":
    print("Setting up optimized FireVision multi-camera pipeline...")
    
    # Example sources: 0 for webcam, "rtsp://..." for IP cameras
    cam1 = CameraStreamThread(camera_id="Cam1", source=0)
    # cam2 = CameraStreamThread(camera_id="Cam2", source=1)
    
    camera_streams = [cam1] # Add cam2 here if used

    # Start camera threads
    for stream in camera_streams:
        stream.start()

    # Wait for the cameras to warm up and fetch at least one frame
    time.sleep(2)

    # Initialize YOLO Model Path (e.g., your custom fire model)
    MODEL_PATH = "yolov8n.pt"  
    
    # Initialize UI worker that computes 1 result per exactly 1.0 seconds
    ai_worker = AIDetectionWorker(model_path=MODEL_PATH, camera_streams=camera_streams, detection_interval=1.0)
    ai_worker.start()

    print("Pipeline running. Press 'q' to stop.")
    try:
        display_results(camera_streams, ai_worker)
    finally:
        # Cleanup
        ai_worker.stop()
        for stream in camera_streams:
            stream.stop()
        cv2.destroyAllWindows()
