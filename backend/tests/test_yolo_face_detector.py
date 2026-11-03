import os
import cv2
import numpy as np
import pytest
from app.services.face_detector import YOLOv11nFaceDetector, get_face_detector, BaseFaceDetector

def test_yolo_detector_singleton():
    d1 = get_face_detector()
    d2 = get_face_detector()
    assert isinstance(d1, BaseFaceDetector)
    assert d1 is d2

def test_yolo_detector_blank_image():
    detector = get_face_detector()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    boxes = detector.detect_faces(blank)
    assert len(boxes) == 0

def test_yolo_detector_empty_or_invalid_inputs():
    detector = get_face_detector()
    assert detector.detect_faces(None) == []
    assert detector.detect_faces(np.array([])) == []
    # Tiny 5x5 image
    tiny = np.zeros((5, 5, 3), dtype=np.uint8)
    assert detector.detect_faces(tiny) == []

def test_yolo_detector_multi_face_real_image():
    zidane_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Lib", "site-packages", "ultralytics", "assets", "zidane.jpg")
    if not os.path.exists(zidane_path):
        pytest.skip("zidane.jpg test asset not found")

    img = cv2.imread(zidane_path)
    assert img is not None

    detector = get_face_detector()
    detections = detector.detect_faces_with_conf(img)
    
    # Should detect face on zidane.jpg
    assert len(detections) >= 1
    for (bbox, conf) in detections:
        x, y, w, h = bbox
        assert x >= 0 and y >= 0
        assert w > 0 and h > 0
        assert x + w <= img.shape[1]
        assert y + h <= img.shape[0]
        assert 0.0 <= conf <= 1.0
        assert conf >= 0.50 # Real faces should have high confidence

def test_yolo_detector_oversized_image_handling():
    detector = get_face_detector()
    # Create an oversized image (e.g. 4500x100) to test dimension downscaling guard
    oversized = np.zeros((100, 4500, 3), dtype=np.uint8)
    boxes = detector.detect_faces(oversized)
    assert isinstance(boxes, list)
