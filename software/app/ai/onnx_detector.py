import cv2
import numpy as np
try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False

class ONNXDetector:
    """
    Optimized YOLOv8 Detector utilizing ONNX Runtime for high-performance inference.
    Supports GPU (CUDA, TensorRT) and CPU runtimes dynamically.
    """
    def __init__(self, model_path: str, use_gpu: bool = True):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.session = None
        self.input_name = None
        self.input_height = 640
        self.input_width = 640
        
        if not HAS_ORT:
            print("Warning: onnxruntime not found. ONNXDetector is disabled.")
            return

        self._initialize_session()

    def _initialize_session(self):
        providers = []
        if self.use_gpu:
            available = ort.get_available_providers()
            if 'TensorrtExecutionProvider' in available:
                providers.append('TensorrtExecutionProvider')
            if 'CUDAExecutionProvider' in available:
                providers.append('CUDAExecutionProvider')
                
        providers.append('CPUExecutionProvider')
        print(f"🤖 Initializing ONNX Runtime session with providers: {providers}")
        
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            inputs = self.session.get_inputs()
            self.input_name = inputs[0].name
            shape = inputs[0].shape
            
            # Extract width & height (standard YOLO input size is 640x640)
            if len(shape) == 4:
                self.input_height = shape[2] if isinstance(shape[2], int) else 640
                self.input_width = shape[3] if isinstance(shape[3], int) else 640
            print(f"✅ ONNX Session loaded successfully. Input shape: {shape}")
        except Exception as e:
            print(f"❌ Failed to load ONNX session: {e}")

    def preprocess(self, frame_bgr: np.ndarray):
        """Convert BGR frame to normalized float32 BCHW input tensor."""
        h, w = frame_bgr.shape[:2]
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (self.input_width, self.input_height))
        
        # Scale to 0.0 - 1.0
        img_normalized = img_resized.astype(np.float32) / 255.0
        
        # Transpose HWC -> CHW
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        
        # Add batch dimension BCHW
        img_expanded = np.expand_dims(img_transposed, axis=0)
        return img_expanded, h, w

    def postprocess(self, outputs, orig_h, orig_w, conf_threshold=0.5):
        """Decode output predictions from YOLOv8 model representation."""
        # YOLOv8 outputs shape: [1, classes + 4, boxes]
        predictions = outputs[0][0]
        predictions = np.transpose(predictions)
        
        boxes = []
        confidences = []
        class_ids = []
        
        # Rescale scale factors
        scale_x = orig_w / self.input_width
        scale_y = orig_h / self.input_height
        
        for pred in predictions:
            # Box coords: xc, yc, w, h
            box = pred[:4]
            scores = pred[4:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            if confidence >= conf_threshold:
                xc, yc, w, h = box
                x1 = int((xc - w / 2) * scale_x)
                y1 = int((yc - h / 2) * scale_y)
                x2 = int((xc + w / 2) * scale_x)
                y2 = int((yc + h / 2) * scale_y)
                
                boxes.append([x1, y1, x2, y2])
                confidences.append(float(confidence))
                class_ids.append(int(class_id))
                
        # NMS to suppress overlapping boxes
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, 0.45)
        
        detections = []
        if len(indices) > 0:
            for idx in indices.flatten():
                detections.append({
                    "bbox": boxes[idx],
                    "confidence": confidences[idx],
                    "class_id": class_ids[idx]
                })
        return detections

    def detect(self, frame_bgr: np.ndarray, conf_threshold=0.5):
        """Run full preprocessing, inference, and postprocessing pipeline on a frame."""
        if self.session is None:
            return []
            
        input_tensor, orig_h, orig_w = self.preprocess(frame_bgr)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        return self.postprocess(outputs, orig_h, orig_w, conf_threshold)
