# yolo_detector.py
from ultralytics import YOLO
import cv2
import numpy as np
import os

# Load the model once at module level
MODEL_PATH = os.path.join("models", "yolov8n.pt")  # Ensure this model is present
model = YOLO(MODEL_PATH)

# Detect only 'person' class (class ID 0 in COCO)
def detect_humans(frame):
    """
    Runs YOLOv8 on the given frame and returns a list of person detections.

    Returns:
        List[Dict]: [{ "box": (x1, y1, x2, y2), "confidence": 0.85 }, ...]
    """
    results = model.predict(source=frame, conf=0.4, classes=[0], verbose=False)

    boxes = []
    if results:
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0].item())
                boxes.append({
                    "box": (x1, y1, x2, y2),
                    "confidence": confidence
                })

    return boxes
