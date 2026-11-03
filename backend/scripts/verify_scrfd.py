import os
import sys
import time
import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.face_detector import get_face_detector, SCRFD10GFaceDetector, YOLOv11nFaceDetector

def run_benchmark():
    print("================================================================")
    print("   AIoT SmartAttend - SCRFD-10G vs YOLOv11n-face Benchmark     ")
    print("================================================================")

    # 1. Initialize Detectors
    print("\n[1] Initializing Detectors...")
    t0 = time.perf_counter()
    scrfd_detector = SCRFD10GFaceDetector.get_instance()
    t_scrfd_init = (time.perf_counter() - t0) * 1000
    print(f"  -> SCRFD-10G loaded in {t_scrfd_init:.1f}ms (Engine: ONNX Runtime, Provider: {scrfd_detector.active_provider})")

    t0 = time.perf_counter()
    yolo_detector = YOLOv11nFaceDetector.get_instance()
    t_yolo_init = (time.perf_counter() - t0) * 1000
    print(f"  -> YOLOv11n-face loaded in {t_yolo_init:.1f}ms (Device: {yolo_detector.device})")

    # 2. Synthetic Test: Blank / Noise Images
    print("\n[2] Edge Cases: Blank and Degenerate Images...")
    blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
    assert scrfd_detector.detect_faces(blank_img) == [], "SCRFD failed blank image test"
    assert scrfd_detector.detect_faces(None) == [], "SCRFD failed None image test"
    assert scrfd_detector.detect_faces(np.array([])) == [], "SCRFD failed empty array test"
    print("  -> All edge case tests PASSED (0 false positives on blank/empty frames).")

    # 3. Test on Benchmark Images
    test_assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "Lib", "site-packages", "ultralytics", "assets")
    benchmark_images = ["zidane.jpg", "bus.jpg"]

    for img_name in benchmark_images:
        img_path = os.path.join(test_assets_dir, img_name)
        if not os.path.exists(img_path):
            continue

        img = cv2.imread(img_path)
        print(f"\n[3] Evaluating on '{img_name}' (Resolution: {img.shape[1]}x{img.shape[0]}):")

        # Benchmark SCRFD
        t0 = time.perf_counter()
        scrfd_results = scrfd_detector.detect_faces_with_landmarks(img, conf_threshold=0.35)
        t_scrfd = (time.perf_counter() - t0) * 1000

        # Benchmark YOLO
        t0 = time.perf_counter()
        yolo_results = yolo_detector.detect_faces_with_conf(img, conf_threshold=0.35)
        t_yolo = (time.perf_counter() - t0) * 1000

        print(f"  SCRFD-10G: {len(scrfd_results)} faces detected in {t_scrfd:.1f}ms")
        for i, det in enumerate(scrfd_results):
            lm_info = f"5 landmarks: eyes=[{det['landmarks'][0]}, {det['landmarks'][1]}], nose={det['landmarks'][2]}" if det.get('landmarks') else "no landmarks"
            print(f"     Face #{i+1}: conf={det['conf']:.3f}, bbox={det['bbox']}, {lm_info}")

        print(f"  YOLOv11n : {len(yolo_results)} faces detected in {t_yolo:.1f}ms (No landmarks)")
        for i, (bbox, conf) in enumerate(yolo_results):
            print(f"     Face #{i+1}: conf={conf:.3f}, bbox={bbox}")

    # 4. Multi-Scale & Small Face Test
    print("\n[4] Stress Test: Distant / Back-Row Small Faces...")
    # Create an image simulating back-row students (e.g. tiny 24x24 face in large 1920x1080 canvas)
    canvas = np.full((1080, 1920, 3), 180, dtype=np.uint8) # Classroom wall background
    zidane_img = cv2.imread(os.path.join(test_assets_dir, "zidane.jpg"))
    if zidane_img is not None:
        # Extract a small face patch (e.g. 28x32 pixels) and place in distant corner
        face_patch = zidane_img[96:276, 913:1057] # Real face
        tiny_face = cv2.resize(face_patch, (30, 35))
        # Place in back-row position
        canvas[200:235, 1500:1530] = tiny_face
        # Place another at mid-distance (55x65)
        mid_face = cv2.resize(face_patch, (55, 65))
        canvas[400:465, 800:855] = mid_face

        t0 = time.perf_counter()
        scrfd_small = scrfd_detector.detect_faces_with_landmarks(canvas, conf_threshold=0.30)
        t_scrfd_canvas = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        yolo_small = yolo_detector.detect_faces_with_conf(canvas, conf_threshold=0.30)
        t_yolo_canvas = (time.perf_counter() - t0) * 1000

        print(f"  Classroom Canvas (1920x1080) with 30px & 55px faces:")
        print(f"  -> SCRFD-10G detected {len(scrfd_small)} faces in {t_scrfd_canvas:.1f}ms")
        for i, det in enumerate(scrfd_small):
            print(f"     Detected Face #{i+1}: bbox={det['bbox']}, conf={det['conf']:.3f}")
        print(f"  -> YOLOv11n detected {len(yolo_small)} faces in {t_yolo_canvas:.1f}ms")
        for i, (bbox, conf) in enumerate(yolo_small):
            print(f"     Detected Face #{i+1}: bbox={bbox}, conf={conf:.3f}")

    print("\n================================================================")
    print("   Benchmark & Verification Summary Completed Successfully!     ")
    print("================================================================")

if __name__ == "__main__":
    run_benchmark()

