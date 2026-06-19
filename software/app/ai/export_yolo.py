import sys
import os
try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics is required for exporting models.")
    sys.exit(1)

def export_model(weights_path: str):
    if not os.path.exists(weights_path):
        print(f"Error: Weights file '{weights_path}' not found.")
        sys.exit(1)
        
    print(f"🔄 Loading YOLOv8 model from {weights_path}...")
    model = YOLO(weights_path)
    
    print("⚡ Exporting to ONNX format (optimized & simplified)...")
    # Export options: format='onnx', simplify=True (reduces graph complexity)
    # opset=12 is widely supported by ONNX execution providers
    exported_file = model.export(format="onnx", simplify=True, opset=12)
    
    print(f"✅ ONNX model successfully saved to: {exported_file}")

if __name__ == "__main__":
    # By default, export standard yolov8n.pt if no argument provided
    weights = sys.argv[1] if len(sys.argv) > 1 else "yolov8n.pt"
    export_model(weights)
