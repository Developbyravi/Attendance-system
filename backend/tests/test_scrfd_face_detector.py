import os
import cv2
import numpy as np
import pytest
from app.services.face_detector import SCRFD10GFaceDetector, get_face_detector, BaseFaceDetector

def test_scrfd_detector_singleton():
    d1 = get_face_detector()
    d2 = get_face_detector()
    assert isinstance(d1, BaseFaceDetector)
    assert d1 is d2
    assert isinstance(d1, SCRFD10GFaceDetector)

def test_scrfd_detector_blank_image():
    detector = get_face_detector()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    boxes = detector.detect_faces(blank)
    assert len(boxes) == 0

def test_scrfd_detector_empty_or_invalid_inputs():
    detector = get_face_detector()
    assert detector.detect_faces(None) == []
    assert detector.detect_faces(np.array([])) == []
    # Tiny 5x5 image
    tiny = np.zeros((5, 5, 3), dtype=np.uint8)
    assert detector.detect_faces(tiny) == []

def test_scrfd_detector_multi_face_real_image():
    zidane_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Lib", "site-packages", "ultralytics", "assets", "zidane.jpg")
    if not os.path.exists(zidane_path):
        pytest.skip("zidane.jpg test asset not found")

    img = cv2.imread(zidane_path)
    assert img is not None

    detector = get_face_detector()
    detections = detector.detect_faces_with_conf(img)
    
    assert len(detections) >= 2
    for (bbox, conf) in detections:
        x, y, w, h = bbox
        assert x >= 0 and y >= 0
        assert w > 0 and h > 0
        assert x + w <= img.shape[1] + 1
        assert y + h <= img.shape[0] + 1
        assert 0.0 <= conf <= 1.0
        assert conf >= 0.50

def test_scrfd_detector_landmarks_extracted():
    zidane_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Lib", "site-packages", "ultralytics", "assets", "zidane.jpg")
    if not os.path.exists(zidane_path):
        pytest.skip("zidane.jpg test asset not found")

    img = cv2.imread(zidane_path)
    detector = get_face_detector()
    results = detector.detect_faces_with_landmarks(img)

    assert len(results) >= 2
    for item in results:
        assert "bbox" in item
        assert "conf" in item
        assert "landmarks" in item
        landmarks = item["landmarks"]
        assert landmarks is not None
        assert len(landmarks) == 5 # 5 facial points: left eye, right eye, nose, left mouth, right mouth
        for (lx, ly) in landmarks:
            assert 0 <= lx <= img.shape[1]
            assert 0 <= ly <= img.shape[0]

def test_scrfd_detector_oversized_image_handling():
    detector = get_face_detector()
    oversized = np.zeros((100, 4500, 3), dtype=np.uint8)
    boxes = detector.detect_faces(oversized)
    assert isinstance(boxes, list)
    assert len(boxes) == 0

def test_scrfd_detector_tiled_inference():
    # Test tiled inference logic on 1280x720 zidane image
    zidane_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Lib", "site-packages", "ultralytics", "assets", "zidane.jpg")
    if not os.path.exists(zidane_path):
        pytest.skip("zidane.jpg test asset not found")

    img = cv2.imread(zidane_path)
    detector = SCRFD10GFaceDetector.get_instance()
    results = detector.detect_faces_with_landmarks(img, conf_threshold=0.35)
    assert len(results) >= 2

