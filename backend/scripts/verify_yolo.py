import os
import cv2
import numpy as np
from ultralytics import YOLO

def main():
    model_path = os.path.join(os.path.dirname(__file__), "weights", "yolov11n-face.pt")
    print(f"Loading YOLOv11n-face from: {model_path}")
    model = YOLO(model_path)
    print(f"Model loaded successfully! Task: {model.task}")

    # 1. Blank image test
    blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
    results_blank = model.predict(blank_img, conf=0.25, verbose=False)
    boxes_blank = len(results_blank[0].boxes)
    print(f"Test 1 (Blank image): {boxes_blank} faces detected (Expected 0) -> {'PASS' if boxes_blank == 0 else 'FAIL'}")

    # 2. Real classroom photo test
    test_img_path = r"c:\Users\kr293\Downloads\1\1102479110244549611024702-e4bda462-5944-4af9-b11024af-f4df6c11024ae1102464_11024.jpg"
    if os.path.exists(test_img_path):
        img = cv2.imread(test_img_path)
        if img is not None:
            results = model.predict(img, conf=0.35, verbose=False)
            boxes = results[0].boxes
            print(f"Test 2 (Classroom Photo {img.shape}): {len(boxes)} faces detected!")
            for i, box in enumerate(boxes[:5]):
                xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
                conf = round(float(box.conf[0]), 3)
                print(f"   Face #{i+1}: BBox={xyxy}, Conf={conf}")
    else:
        print(f"Note: Test image {test_img_path} not found.")

if __name__ == "__main__":
    main()
