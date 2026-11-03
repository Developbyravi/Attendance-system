import numpy as np
from app.ai.detector import SCRFD10GFaceDetector
from app.ai.preprocessing import letterbox, crop_and_align_face

def test_scrfd_detector_initialization():
    detector = SCRFD10GFaceDetector.get_instance()
    assert detector is not None
    assert detector.active_provider in ["CPUExecutionProvider", "CUDAExecutionProvider"]

def test_letterbox_aspect_ratio_preservation():
    # Create test image 800x600 (height 600, width 800)
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    padded, scale, (pad_w, pad_h) = letterbox(img, target_size=(640, 640))

    assert padded.shape == (640, 640, 3)
    assert scale == 640 / 800 # 0.8
    assert pad_h == (640 - int(600 * 0.8)) // 2 # 80

def test_crop_and_align_face():
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    # White rectangle in center simulating face
    img[100:300, 100:300] = 255

    crop = crop_and_align_face(img, (100, 100, 200, 200), landmarks=None, output_size=(112, 112))
    assert crop.shape == (112, 112, 3)

