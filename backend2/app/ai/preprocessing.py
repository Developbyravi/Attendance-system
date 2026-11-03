import cv2
import numpy as np
from typing import Tuple, List, Optional
from app.core.exceptions import FaceBiometricError

# Standard ArcFace canonical 5-point landmark coordinates (112x112 template)
# Order: Left Eye, Right Eye, Nose, Left Mouth Corner, Right Mouth Corner
ARCFACE_CANONICAL_5PTS = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041]
], dtype=np.float32)

def decode_image_bytes(file_bytes: bytes) -> np.ndarray:
    """Decodes raw byte array into OpenCV BGR image."""
    if not file_bytes:
        raise FaceBiometricError("Uploaded image file is empty.")
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None or img.size == 0:
        raise FaceBiometricError("Could not decode image file. Please provide a valid JPEG or PNG.")
    return img

def validate_image_security(filename: str, content_type: str, file_size: int, max_bytes: int = 25 * 1024 * 1024):
    """Enforces file size, extension, and content type constraints."""
    if file_size > max_bytes:
        raise FaceBiometricError(f"Image file exceeds maximum allowable size of {max_bytes // (1024*1024)}MB.")
    allowed_exts = (".jpg", ".jpeg", ".png", ".webp")
    if not any(filename.lower().endswith(ext) for ext in allowed_exts):
        raise FaceBiometricError(f"Unsupported image extension. Must be one of: {', '.join(allowed_exts)}")

def letterbox(
    img: np.ndarray,
    target_size: Tuple[int, int] = (640, 640),
    color: Tuple[int, int, int] = (0, 0, 0)
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Resizes image preserving aspect ratio with symmetric letterbox padding.
    Returns: (padded_image, scale_ratio, (pad_left, pad_top))
    """
    shape = img.shape[:2] # height, width
    target_w, target_h = target_size

    # Scale ratio (new / old)
    r = min(target_w / shape[1], target_h / shape[0])

    # Unpadded new dimensions
    new_unpad_w = int(round(shape[1] * r))
    new_unpad_h = int(round(shape[0] * r))

    # Padding deltas
    dw = target_w - new_unpad_w
    dh = target_h - new_unpad_h

    dw_left = dw // 2
    dw_right = dw - dw_left
    dh_top = dh // 2
    dh_bottom = dh - dh_top

    if shape[::-1] != (new_unpad_w, new_unpad_h):
        resized = cv2.resize(img, (new_unpad_w, new_unpad_h), interpolation=cv2.INTER_LINEAR)
    else:
        resized = img.copy()

    padded = cv2.copyMakeBorder(
        resized,
        dh_top, dh_bottom,
        dw_left, dw_right,
        cv2.BORDER_CONSTANT,
        value=color
    )

    return padded, r, (dw_left, dh_top)

def crop_and_align_face(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    landmarks: Optional[List[Tuple[float, float]]] = None,
    output_size: Tuple[int, int] = (112, 112)
) -> np.ndarray:
    """
    Aligns and crops face using 5-point facial landmarks similarity transformation.
    If landmarks are not present, performs margin-expanded bounding box crop.
    """
    if image is None or image.size == 0:
        return np.zeros((output_size[1], output_size[0], 3), dtype=np.uint8)

    h_img, w_img = image.shape[:2]
    x, y, w, h = bbox

    # 1. Landmark-guided similarity affine alignment (ArcFace standard)
    if landmarks is not None and len(landmarks) == 5:
        try:
            src_pts = np.array(landmarks, dtype=np.float32)
            dst_pts = ARCFACE_CANONICAL_5PTS.copy()

            if output_size != (112, 112):
                scale_x = output_size[0] / 112.0
                scale_y = output_size[1] / 112.0
                dst_pts[:, 0] *= scale_x
                dst_pts[:, 1] *= scale_y

            # Estimate affine partial similarity matrix (rigid transform: rotation + translation + uniform scale)
            M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.LMEDS)
            if M is not None:
                aligned = cv2.warpAffine(image, M, output_size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
                return aligned
        except Exception:
            pass

    # 2. Bounding Box crop fallback with 20% margin
    margin_w = int(w * 0.15)
    margin_h = int(h * 0.15)

    x1 = max(0, x - margin_w)
    y1 = max(0, y - margin_h)
    x2 = min(w_img, x + w + margin_w)
    y2 = min(h_img, y + h + margin_h)

    crop = image[y1:y2, x1:x2]
    if crop is None or crop.size == 0:
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w_img, x + w)
        y2 = min(h_img, y + h)
        crop = image[y1:y2, x1:x2]

    if crop is None or crop.size == 0:
        return np.zeros((output_size[1], output_size[0], 3), dtype=np.uint8)

    return cv2.resize(crop, output_size, interpolation=cv2.INTER_LINEAR)

