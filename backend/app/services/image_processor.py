import io
import os
import uuid
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List, Optional, Dict, Any
from app.schemas.face import QualityCheckResult
from app.services.face_detector import get_face_detector

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

def validate_image_file_security(filename: str, content_type: str, file_size: int):
    """
    Security validation for uploaded file format, extension, and file size.
    """
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError(f"Invalid file extension '{ext}'. Only .jpg, .jpeg, .png, and .webp are allowed.")

    if content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Invalid image format '{content_type}'.")

def decode_image_bytes(file_bytes: bytes) -> np.ndarray:
    """
    Safely decodes image bytes into OpenCV BGR numpy array.
    """
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img.verify()

        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Corrupted image file; OpenCV failed to decode.")
        return img
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image data: {str(e)}")

def validate_image_quality_and_faces(img: np.ndarray) -> QualityCheckResult:
    """
    Validates resolution, blur, brightness, and enforces EXACTLY ONE FACE per enrollment image.
    """
    h, w = img.shape[:2]
    warnings: List[str] = []

    if h < 80 or w < 80:
        return QualityCheckResult(
            is_valid=False,
            faces_detected=0,
            brightness=0,
            blur_score=0,
            error_message=f"Image resolution too low ({w}x{h}). Minimum required resolution is 80x80 pixels."
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    brightness = float(np.mean(gray))
    if brightness < 35:
        warnings.append("Low image brightness; face may be poorly lit.")
    elif brightness > 225:
        warnings.append("High image brightness; face may be overexposed.")

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < 25.0:
        warnings.append("Image appears blurry; results may be less accurate.")

    detector = get_face_detector()
    faces = detector.detect_faces(img)
    face_count = len(faces)

    if face_count == 0:
        return QualityCheckResult(
            is_valid=False,
            faces_detected=0,
            brightness=brightness,
            blur_score=blur_score,
            error_message="No face detected in the image. Please upload a clear photo with a single visible face.",
            warnings=warnings
        )

    if face_count > 1:
        return QualityCheckResult(
            is_valid=False,
            faces_detected=face_count,
            brightness=brightness,
            blur_score=blur_score,
            error_message=f"Multiple faces detected ({face_count}). Enrollment requires exactly one face per image to prevent enrolling the wrong person.",
            warnings=warnings
        )

    # Exactly 1 face found
    return QualityCheckResult(
        is_valid=True,
        faces_detected=1,
        brightness=brightness,
        blur_score=blur_score,
        bbox=faces[0],
        warnings=warnings
    )

ARCFACE_REF_PTS = np.array([
    [38.2946, 51.6963],  # left eye
    [73.5318, 51.6963],  # right eye
    [56.0252, 71.7366],  # nose
    [41.5493, 92.3655],  # left mouth
    [70.7299, 92.3655]   # right mouth
], dtype=np.float32)

def crop_and_align_face(
    img: np.ndarray,
    bbox: Tuple[int, int, int, int],
    landmarks: Optional[List[Tuple[float, float]]] = None
) -> np.ndarray:
    """
    Crops and aligns face region.
    - If 5-point facial landmarks are available (from SCRFD-10G), applies ArcFace 112x112 similarity transform.
    - If landmarks are unavailable, degenerate, or alignment fails, applies aspect-padded bounding box crop.
    """
    if img is None or img.size == 0:
        return np.zeros((112, 112, 3), dtype=np.uint8)

    # 1. Try 5-point similarity transform alignment if landmarks provided
    if landmarks is not None and len(landmarks) == 5:
        try:
            src_pts = np.array(landmarks, dtype=np.float32)
            M, inliers = cv2.estimateAffinePartial2D(src_pts, ARCFACE_REF_PTS)
            if M is not None:
                aligned = cv2.warpAffine(img, M, (112, 112), borderValue=0.0)
                if aligned is not None and aligned.size > 0:
                    return aligned
        except Exception:
            pass

    # 2. Fallback: Padded Bounding Box Crop
    h, w = img.shape[:2]
    x, y, bw, bh = bbox

    pad_x = int(bw * 0.15)
    pad_y = int(bh * 0.15)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w, x + bw + pad_x)
    y2 = min(h, y + bh + pad_y)

    face_crop = img[y1:y2, x1:x2]
    if face_crop is None or face_crop.size == 0:
        return np.zeros((112, 112, 3), dtype=np.uint8)
    return face_crop

def save_sanitized_student_image(file_bytes: bytes, student_id: int, storage_dir: str) -> str:
    """
    Saves image with sanitized random filename outside source code directory.
    """
    os.makedirs(storage_dir, exist_ok=True)
    filename = f"student_{student_id}_{uuid.uuid4().hex[:10]}.jpg"
    filepath = os.path.join(storage_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    return filepath

def extract_all_face_crops_with_conf(img: np.ndarray, conf_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Extracts all faces from a classroom photograph with detector confidences, 5-point landmarks, and aligned crops.
    """
    detector = get_face_detector()
    if hasattr(detector, 'detect_faces_with_landmarks'):
        detections = detector.detect_faces_with_landmarks(img, conf_threshold=conf_threshold)
        results = []
        for item in detections:
            bbox = item["bbox"]
            conf = item["conf"]
            landmarks = item.get("landmarks")
            crop = crop_and_align_face(img, bbox, landmarks=landmarks)
            if crop is not None and crop.size > 0:
                results.append({
                    "bbox": bbox,
                    "conf": conf,
                    "landmarks": landmarks,
                    "xyxy": item.get("xyxy"),
                    "face_crop": crop
                })
        return results
    elif hasattr(detector, 'detect_faces_with_conf'):
        detections = detector.detect_faces_with_conf(img, conf_threshold=conf_threshold)
        results = []
        for bbox, conf in detections:
            crop = crop_and_align_face(img, bbox)
            if crop is not None and crop.size > 0:
                results.append({
                    "bbox": bbox,
                    "conf": conf,
                    "landmarks": None,
                    "face_crop": crop
                })
        return results
    else:
        boxes = detector.detect_faces(img)
        results = []
        for bbox in boxes:
            crop = crop_and_align_face(img, bbox)
            if crop is not None and crop.size > 0:
                results.append({
                    "bbox": bbox,
                    "conf": 1.0,
                    "landmarks": None,
                    "face_crop": crop
                })
        return results

def draw_detection_overlay(img: np.ndarray, detected_boxes: List[Dict[str, Any]]) -> np.ndarray:
    """
    Draws visually distinct bounding boxes and identification labels on a classroom image.
    Color coding:
      - recognized: Green (46, 204, 113)
      - ambiguous: Amber (0, 165, 255)
      - unknown: Red (40, 40, 230)
      - duplicate: Purple (180, 80, 180)
    """
    if img is None or img.size == 0:
        return img

    annotated = img.copy()
    h_img, w_img = annotated.shape[:2]

    color_map = {
        "recognized": (46, 204, 113),  # Green
        "ambiguous":  (0, 165, 255),   # Amber
        "unknown":    (40, 40, 230),   # Red
        "duplicate":  (180, 80, 180)   # Purple
    }

    for box_info in detected_boxes:
        bbox = box_info.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x, y, w, h = [int(v) for v in bbox]
        x1 = max(0, min(x, w_img - 1))
        y1 = max(0, min(y, h_img - 1))
        x2 = max(0, min(x + w, w_img - 1))
        y2 = max(0, min(y + h, h_img - 1))

        status = box_info.get("match_status", "unknown")
        color = color_map.get(status, (40, 40, 230))

        # Draw main bounding box
        thickness = max(2, int(min(h_img, w_img) / 400))
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        # Build label text
        name = box_info.get("student_name")
        sim = box_info.get("similarity")
        conf = box_info.get("detector_confidence")

        if status == "recognized" and name:
            sim_str = f"{sim:.2f}" if sim is not None else ""
            label = f"{name} ({sim_str})" if sim_str else name
        elif status == "ambiguous":
            label = "AMBIGUOUS"
        elif status == "duplicate":
            label = f"DUP: {name}" if name else "DUPLICATE"
        else:
            conf_str = f"{conf:.2f}" if conf is not None else ""
            label = f"UNKNOWN ({conf_str})" if conf_str else "UNKNOWN"

        # Text size & background badge
        font_scale = max(0.4, min(h_img, w_img) / 1200)
        font_thick = max(1, int(font_scale * 1.5))
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

        badge_y1 = max(0, y1 - th - 6)
        badge_y2 = y1
        badge_x2 = min(w_img - 1, x1 + tw + 8)

        # Draw background rectangle for badge
        cv2.rectangle(annotated, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
        # Draw white text
        cv2.putText(
            annotated,
            label,
            (x1 + 4, badge_y2 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            font_thick,
            cv2.LINE_AA
        )

    return annotated

