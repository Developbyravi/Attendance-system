import os
import logging
import threading
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np
import onnxruntime as ort

from app.config import settings
from app.ai.preprocessing import letterbox

logger = logging.getLogger(__name__)

def distance2bbox(points: np.ndarray, distance: np.ndarray, max_shape: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """Decodes SCRFD distance offsets into (x1, y1, x2, y2) coordinates."""
    x1 = points[:, 0] - distance[:, 0]
    y1 = points[:, 1] - distance[:, 1]
    x2 = points[:, 0] + distance[:, 2]
    y2 = points[:, 1] + distance[:, 3]
    if max_shape is not None:
        x1 = np.clip(x1, 0, max_shape[1])
        y1 = np.clip(y1, 0, max_shape[0])
        x2 = np.clip(x2, 0, max_shape[1])
        y2 = np.clip(y2, 0, max_shape[0])
    return np.stack([x1, y1, x2, y2], axis=-1)

def distance2kps(points: np.ndarray, distance: np.ndarray, max_shape: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """Decodes SCRFD distance offsets into 5-point facial keypoints."""
    preds = []
    for i in range(0, distance.shape[1], 2):
        px = points[:, i % 2] + distance[:, i]
        py = points[:, i % 2 + 1] + distance[:, i + 1]
        if max_shape is not None:
            px = np.clip(px, 0, max_shape[1])
            py = np.clip(py, 0, max_shape[0])
        preds.append(px)
        preds.append(py)
    return np.stack(preds, axis=-1)

def nms_bboxes(dets: np.ndarray, thresh: float) -> List[int]:
    """Applies Non-Maximum Suppression on bounding boxes."""
    if len(dets) == 0:
        return []
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]

    return keep

class SCRFD10GFaceDetector:
    """
    InsightFace SCRFD-10G High-Performance Face Detector.
    Uses ONNX Runtime with automatic hardware acceleration detection.
    Supports multi-scale FPN (strides 8, 16, 32), 5-point landmarks,
    and overlapping tiled inference for dense classroom photographs.
    """
    _instance: Optional['SCRFD10GFaceDetector'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.model_path = settings.resolved_scrfd_path
        self.conf_threshold = settings.FACE_DETECTION_THRESHOLD
        self.nms_threshold = 0.40
        self.input_size = (settings.TILE_SIZE, settings.TILE_SIZE)
        self.enable_tiled_inference = settings.ENABLE_TILED_INFERENCE
        self.tile_size = settings.TILE_SIZE
        self.tile_overlap = settings.TILE_OVERLAP

        self.input_mean = 127.5
        self.input_std = 128.0
        self.feat_strides = [8, 16, 32]
        self.num_anchors = 2
        self.use_kps = True

        self.session = None
        self.active_provider = "CPUExecutionProvider"
        self._center_cache: Dict[Tuple[int, int, int], np.ndarray] = {}
        self._inference_lock = threading.Lock()
        self.fallback_detector = None

        self._initialize_session()

    @classmethod
    def get_instance(cls) -> 'SCRFD10GFaceDetector':
        with cls._lock:
            if cls._instance is None:
                cls._instance = SCRFD10GFaceDetector()
            return cls._instance

    def _initialize_session(self):
        if not os.path.exists(self.model_path):
            logger.warning(f"SCRFD weights not found at '{self.model_path}'. Setting up OpenCV fallback.")
            self._setup_fallback()
            return

        try:
            available_providers = ort.get_available_providers()
            providers = ["CPUExecutionProvider"]
            if settings.INFERENCE_DEVICE.lower() == "cuda" and "CUDAExecutionProvider" in available_providers:
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = min(4, os.cpu_count() or 1)

            self.session = ort.InferenceSession(self.model_path, sess_options=sess_options, providers=providers)
            self.active_provider = self.session.get_providers()[0]
            logger.info(f"Initialized SCRFD-10G ONNX session with provider: {self.active_provider}")
        except Exception as e:
            logger.error(f"Failed to load ONNX runtime for SCRFD-10G: {e}. Fallback enabled.")
            self._setup_fallback()

    def _setup_fallback(self):
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.fallback_detector = cv2.CascadeClassifier(cascade_path)
        except Exception:
            self.fallback_detector = None

    def _forward_single_image(
        self,
        image_bgr: np.ndarray,
        conf_thresh: float
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Performs raw single-image feedforward and postprocessing."""
        h_orig, w_orig = image_bgr.shape[:2]
        padded_img, det_scale, (pad_w, pad_h) = letterbox(image_bgr, target_size=self.input_size)

        blob = cv2.dnn.blobFromImage(
            padded_img,
            1.0 / self.input_std,
            self.input_size,
            (self.input_mean, self.input_mean, self.input_mean),
            swapRB=True
        )

        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: blob})

        scores_list = []
        bboxes_list = []
        kpss_list = []

        num_outputs = len(outputs)
        has_kps = (num_outputs == 9)
        target_w, target_h = self.input_size

        for idx, stride in enumerate(self.feat_strides):
            if has_kps:
                score_out = outputs[idx]
                bbox_out = outputs[idx + 3]
                kps_out = outputs[idx + 6]
            else:
                score_out = outputs[idx]
                bbox_out = outputs[idx + 3]
                kps_out = None

            score = score_out.reshape(-1, 1)
            bbox = bbox_out * stride
            kps = (kps_out * stride) if kps_out is not None else None

            feat_h, feat_w = target_h // stride, target_w // stride
            key = (feat_h, feat_w, stride)
            if key not in self._center_cache:
                anchor_centers = np.stack(np.mgrid[:feat_h, :feat_w][::-1], axis=-1).astype(np.float32)
                anchor_centers = (anchor_centers * stride).reshape((-1, 2))
                if self.num_anchors > 1:
                    anchor_centers = np.stack([anchor_centers] * self.num_anchors, axis=1).reshape((-1, 2))
                self._center_cache[key] = anchor_centers
            anchor_centers = self._center_cache[key]

            pos_inds = np.where(score.reshape(-1) >= conf_thresh)[0]
            if len(pos_inds) == 0:
                continue

            bboxes = distance2bbox(anchor_centers[pos_inds], bbox[pos_inds])
            scores = score[pos_inds]
            scores_list.append(scores)
            bboxes_list.append(bboxes)

            if kps is not None:
                kpss = distance2kps(anchor_centers[pos_inds], kps[pos_inds])
                kpss_list.append(kpss)

        if not scores_list:
            return np.empty((0, 5), dtype=np.float32), (np.empty((0, 5, 2), dtype=np.float32) if has_kps else None)

        scores_all = np.vstack(scores_list)
        bboxes_all = np.vstack(bboxes_list)

        # Rescale bboxes to original unpadded image coordinates
        bboxes_all[:, 0] = (bboxes_all[:, 0] - pad_w) / det_scale
        bboxes_all[:, 1] = (bboxes_all[:, 1] - pad_h) / det_scale
        bboxes_all[:, 2] = (bboxes_all[:, 2] - pad_w) / det_scale
        bboxes_all[:, 3] = (bboxes_all[:, 3] - pad_h) / det_scale

        bboxes_all[:, 0] = np.clip(bboxes_all[:, 0], 0, w_orig)
        bboxes_all[:, 1] = np.clip(bboxes_all[:, 1], 0, h_orig)
        bboxes_all[:, 2] = np.clip(bboxes_all[:, 2], 0, w_orig)
        bboxes_all[:, 3] = np.clip(bboxes_all[:, 3], 0, h_orig)

        dets = np.hstack([bboxes_all, scores_all])

        kpss_all = None
        if has_kps and kpss_list:
            kpss_raw = np.vstack(kpss_list)
            kpss_raw[:, 0::2] = (kpss_raw[:, 0::2] - pad_w) / det_scale
            kpss_raw[:, 1::2] = (kpss_raw[:, 1::2] - pad_h) / det_scale
            kpss_all = kpss_raw.reshape((-1, 5, 2))

        return dets, kpss_all

    def detect_faces_with_landmarks(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects faces in classroom photographs with 5 facial landmarks.
        Uses overlapping tiled window inference on large images.
        """
        if image is None or image.size == 0:
            return []

        conf_thresh = conf_threshold if conf_threshold is not None else self.conf_threshold

        if self.session is None:
            return self._detect_fallback(image)

        h_img, w_img = image.shape[:2]

        with self._inference_lock:
            use_tiled = self.enable_tiled_inference and (w_img > 1000 or h_img > 1000)

            all_dets_list = []
            all_kps_list = []

            # 1. Base full-frame inference
            dets_base, kps_base = self._forward_single_image(image, conf_thresh)
            if len(dets_base) > 0:
                all_dets_list.append(dets_base)
                if kps_base is not None:
                    all_kps_list.append(kps_base)

            # 2. Overlapping tiled inference for high-res classroom scenes
            if use_tiled:
                stride_w = int(self.tile_size * (1.0 - self.tile_overlap))
                stride_h = int(self.tile_size * (1.0 - self.tile_overlap))

                x_steps = list(range(0, max(1, w_img - self.tile_size), stride_w))
                if x_steps[-1] + self.tile_size < w_img:
                    x_steps.append(w_img - self.tile_size)

                y_steps = list(range(0, max(1, h_img - self.tile_size), stride_h))
                if y_steps[-1] + self.tile_size < h_img:
                    y_steps.append(h_img - self.tile_size)

                for y0 in y_steps:
                    for x0 in x_steps:
                        tile = image[y0:y0 + self.tile_size, x0:x0 + self.tile_size]
                        tile_dets, tile_kps = self._forward_single_image(tile, conf_thresh)
                        if len(tile_dets) > 0:
                            tile_dets[:, 0] += x0
                            tile_dets[:, 1] += y0
                            tile_dets[:, 2] += x0
                            tile_dets[:, 3] += y0
                            all_dets_list.append(tile_dets)

                            if tile_kps is not None and len(tile_kps) > 0:
                                tile_kps_mapped = tile_kps.copy()
                                tile_kps_mapped[:, :, 0] += x0
                                tile_kps_mapped[:, :, 1] += y0
                                all_kps_list.append(tile_kps_mapped)

            if not all_dets_list:
                return []

            combined_dets = np.vstack(all_dets_list)
            combined_kps = np.vstack(all_kps_list) if all_kps_list else None

            # Global NMS across full-frame and tiled detections
            keep_indices = nms_bboxes(combined_dets, self.nms_threshold)

            results: List[Dict[str, Any]] = []
            for idx in keep_indices:
                x1, y1, x2, y2, score = combined_dets[idx]
                w = int(round(x2 - x1))
                h = int(round(y2 - y1))
                x = int(round(x1))
                y = int(round(y1))

                # Geometric validation: reject zero or inverted boxes
                if w < 10 or h < 10:
                    continue

                landmarks = None
                if combined_kps is not None and idx < len(combined_kps):
                    kps_pts = combined_kps[idx] # (5, 2)
                    landmarks = [(float(pt[0]), float(pt[1])) for pt in kps_pts]

                results.append({
                    "bbox": (x, y, w, h),
                    "conf": float(round(score, 4)),
                    "landmarks": landmarks,
                    "xyxy": (float(x1), float(y1), float(x2), float(y2))
                })

            return results

    def _detect_fallback(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """OpenCV Haar cascade fallback."""
        if self.fallback_detector is None:
            return []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.fallback_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        results = []
        for (x, y, w, h) in faces:
            results.append({
                "bbox": (int(x), int(y), int(w), int(h)),
                "conf": 1.0,
                "landmarks": None,
                "xyxy": (float(x), float(y), float(x + w), float(y + h))
            })
        return results
