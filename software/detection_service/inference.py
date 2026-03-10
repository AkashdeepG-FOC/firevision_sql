from ultralytics import YOLO
import torch
import os

class YoloEngine:
    def __init__(self, model_path="custom_model.pt"):
        # Load from software/custom_model.pt
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(parent_dir, model_path)
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.model = YOLO(full_path)
            self.model.to(self.device)
            print(f"Loaded YOLO model on {self.device} from {full_path}")
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
            self.model = None

    def predict_batch(self, frames):
        """
        Runs batch inference on a list of cv2 frames.
        Returns a list of results (list of detection dicts for each frame).
        """
        if not self.model or not frames:
            return [[] for _ in frames]
            
        try:
            # Batch prediction
            results = self.model(frames, verbose=False)
            
            batch_output = []
            for result in results:
                detections = []
                if result.boxes is not None:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        label = self.model.names[cls_id]
                        # Assume the model predicts fire & smoke
                        detections.append({
                            "label": label.lower(),
                            "confidence": conf,
                            "box": [x1, y1, x2, y2]
                        })
                batch_output.append(detections)
            return batch_output
        except Exception as e:
            print(f"Error during batch prediction: {e}")
            return [[] for _ in frames]
