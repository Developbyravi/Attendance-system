import cv2
import numpy as np
from typing import List, Dict, Any

def draw_detection_overlay(image: np.ndarray, detected_boxes: List[Dict[str, Any]]) -> np.ndarray:
    """
    Renders clean, color-coded bounding boxes and student badges onto classroom photo.
    Colors:
    - GREEN (0, 220, 50): Recognized
    - AMBER (0, 200, 255): Ambiguous / Needs Review
    - BLUE (240, 150, 0): Unknown Face
    - PURPLE (200, 50, 180): Duplicate Face Detection
    """
    if image is None or image.size == 0:
        return image

    canvas = image.copy()
    h_img, w_img = canvas.shape[:2]

    color_map = {
        "recognized": (50, 220, 50),     # Bright Green
        "ambiguous": (0, 200, 255),       # Amber / Yellow
        "unknown": (240, 150, 0),         # Cool Blue
        "duplicate": (200, 50, 180)       # Purple
    }

    for item in detected_boxes:
        bbox = item.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        x, y, w, h = bbox
        status = item.get("match_status", "unknown")
        color = color_map.get(status, (200, 200, 200))

        # 1. Bounding box
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w_img - 1, x + w), min(h_img - 1, y + h)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

        # 2. Text Label
        name = item.get("student_name")
        roll = item.get("roll_no")
        sim = item.get("similarity")

        if status == "recognized" and name:
            sim_str = f" {int(sim * 100)}%" if sim is not None else ""
            label = f"{name} ({roll}){sim_str}"
        elif status == "ambiguous":
            label = f"FLAGGED ({int(sim * 100)}%)" if sim else "FLAGGED"
        elif status == "duplicate":
            label = f"DUP: {name or 'Face'}"
        else:
            conf = item.get("detector_confidence", 1.0)
            label = f"Unknown ({int(conf * 100)}%)"

        # Text banner background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        thickness = 1
        (txt_w, txt_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        badge_y1 = max(0, y1 - txt_h - 6)
        badge_y2 = y1
        badge_x2 = min(w_img - 1, x1 + txt_w + 8)

        cv2.rectangle(canvas, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
        cv2.putText(canvas, label, (x1 + 4, badge_y2 - 4), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

    return canvas

