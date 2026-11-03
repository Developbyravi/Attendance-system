import os
import logging
import threading
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

class BaseFaceDetector(ABC):
    @abstractmethod
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image.
        Returns a list of bounding boxes as (x, y, width, height).
        """
        pass

    def detect_faces_with_conf(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Detect faces with confidence scores.
        Returns list of ((x, y, w, h), confidence_score).
        Default implementation wraps detect_faces with 1.0 confidence.
        """
        boxes = self.detect_faces(image)
        return [(b, 1.0) for b in boxes]

    def detect_faces_with_landmarks(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect faces with confidence scores and facial landmarks (if supported).
        Returns list of dicts:
        {
            "bbox": (x, y, w, h),
            "conf": float,
            "landmarks": [(x1, y1), ..., (x5, y5)] or None,
            "xyxy": (x1, y1, x2, y2)
        }
        """
        results = self.detect_faces_with_conf(image, conf_threshold=conf_threshold)
        items = []
        for bbox, conf in results:
            x, y, w, h = bbox
            items.append({
                "bbox": bbox,
                "conf": conf,
                "landmarks": None,
                "xyxy": (float(x), float(y), float(x + w), float(y + h))
            })
        return items


class OpenCVHaarFaceDetector(BaseFaceDetector):
    """
    OpenCV Face Detector with safe cascade initialization and fallback contour face detection.
    Used as a fallback if neural net weights are missing or during lightweight testing.
    """
    def __init__(self):
        self.cascade = None
        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data'):
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.cascade = cv2.CascadeClassifier(cascade_path)
                if self.cascade.empty():
                    self.cascade = None
            except Exception as e:
                logger.warning(f"Failed to load OpenCV Haar Cascade: {e}")
                self.cascade = None

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if image is None or image.size == 0:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # 1. Try Haar Cascade if loaded
        if self.cascade is not None:
            try:
                faces = self.cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(30, 30)
                )
                if len(faces) > 0:
                    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
            except Exception:
                pass

        # 2. Robust Skin-Color Fallback
        if len(image.shape) == 3:
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            lower_skin = np.array([0, 133, 77], dtype=np.uint8)
            upper_skin = np.array([255, 173, 127], dtype=np.uint8)
            mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h_img, w_img = image.shape[:2]
            min_area = (h_img * w_img) * 0.03

            valid_boxes = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(h) / w if w > 0 else 0
                    if 0.6 <= aspect_ratio <= 1.8:
                        valid_boxes.append((int(x), int(y), int(w), int(h)))

            if len(valid_boxes) > 0:
                return valid_boxes

        return []

    def detect_faces_with_conf(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Tuple[Tuple[int, int, int, int], float]]:
        boxes = self.detect_faces(image)
        return [(b, 0.85) for b in boxes]


class YOLOv11nFaceDetector(BaseFaceDetector):
    """
    Pretrained YOLOv11n-face model detector (Ultralytics).
    Preserved for benchmarking, comparison, and fallback.
    """
    _instance: Optional['YOLOv11nFaceDetector'] = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        imgsz: Optional[int] = None,
        device: Optional[str] = None
    ):
        resolved_path = model_path or settings.YOLO_MODEL_PATH
        if not os.path.isabs(resolved_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            candidate1 = os.path.join(backend_dir, resolved_path)
            candidate2 = os.path.abspath(resolved_path)
            candidate3 = os.path.join(backend_dir, "weights", "yolov11n-face.pt")
            if os.path.exists(candidate1):
                resolved_path = candidate1
            elif os.path.exists(candidate2):
                resolved_path = candidate2
            elif os.path.exists(candidate3):
                resolved_path = candidate3
        self.model_path = resolved_path
        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.YOLO_CONFIDENCE_THRESHOLD
        self.iou_threshold = iou_threshold if iou_threshold is not None else settings.YOLO_IOU_THRESHOLD
        self.imgsz = imgsz or settings.YOLO_INFERENCE_SIZE

        if device:
            self.device = device
        else:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() and settings.YOLO_DEVICE.lower() == "cuda" else "cpu"
            except Exception:
                self.device = "cpu"

        self.model = None
        self.fallback_detector = OpenCVHaarFaceDetector()
        self._inference_lock = threading.Lock()
        self._initialize_model()

    def _initialize_model(self):
        """Loads YOLO weights once."""
        if not os.path.exists(self.model_path):
            logger.warning(
                f"YOLOv11n-face weights not found at '{self.model_path}'. "
                f"Falling back to OpenCVHaarFaceDetector."
            )
            return

        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLOv11n-face model from '{self.model_path}' on device '{self.device}'...")
            self.model = YOLO(self.model_path)
            logger.info("YOLOv11n-face model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model from '{self.model_path}': {e}. Using fallback detector.")
            self.model = None

    @classmethod
    def get_instance(cls) -> 'YOLOv11nFaceDetector':
        with cls._lock:
            if cls._instance is None:
                cls._instance = YOLOv11nFaceDetector()
            return cls._instance

    def detect_faces_with_conf(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Runs YOLOv11n-face inference on image and returns list of ((x, y, w, h), conf).
        """
        if image is None or image.size == 0:
            return []

        h_img, w_img = image.shape[:2]
        if h_img < 20 or w_img < 20:
            return []

        max_dim = settings.MAX_IMAGE_DIMENSION
        if h_img > max_dim or w_img > max_dim:
            scale = max_dim / max(h_img, w_img)
            new_w = max(1, int(w_img * scale))
            new_h = max(1, int(h_img * scale))
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h_img, w_img = new_h, new_w

        if self.model is None:
            return self.fallback_detector.detect_faces_with_conf(image)

        conf = conf_threshold if conf_threshold is not None else self.conf_threshold

        try:
            with self._inference_lock:
                results = self.model.predict(
                    image,
                    conf=conf,
                    iou=self.iou_threshold,
                    imgsz=self.imgsz,
                    device=self.device,
                    verbose=False
                )

            if not results or len(results) == 0:
                return []

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return []

            detected: List[Tuple[Tuple[int, int, int, int], float]] = []
            for b in boxes:
                xyxy = b.xyxy[0].cpu().numpy()
                score = float(b.conf[0].cpu().numpy())

                x1, y1, x2, y2 = xyxy
                x = int(round(x1))
                y = int(round(y1))
                w = int(round(x2 - x1))
                h = int(round(y2 - y1))

                x = max(0, min(x, w_img - 1))
                y = max(0, min(y, h_img - 1))
                w = max(1, min(w, w_img - x))
                h = max(1, min(h, h_img - y))

                if w > 5 and h > 5:
                    detected.append(((x, y, w, h), round(score, 4)))

            return detected

        except Exception as e:
            logger.error(f"Error during YOLO inference: {e}. Attempting fallback detector.")
            return self.fallback_detector.detect_faces_with_conf(image)

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        detections = self.detect_faces_with_conf(image)
        return [b for (b, _score) in detections]


class SCRFD10GFaceDetector(BaseFaceDetector):
    """
    InsightFace SCRFD-10G High-Performance Face Detector with 5 Facial Keypoints.
    
    Features & Architectural Advantages:
    - ONNX Runtime engine with CPU baseline & automatic CUDA hardware detection.
    - 3-scale Feature Pyramid Network (Strides 8, 16, 32) optimized for multi-face
      classroom environments (detects small & back-row faces down to 10px).
    - Aspect-ratio preserving letterbox / padding without image distortion.
    - 5-point facial landmarks extraction (left eye, right eye, nose, left mouth, right mouth).
    - Overlapping tiled window inference for ultra-high-resolution classroom photographs.
    - Strict IoU-based Non-Maximum Suppression (NMS) and geometric bounding box validation.
    - Thread-safe singleton inference with dynamic grid anchor caching.
    - Graceful fallback to YOLO / OpenCV Haar detectors if weights are missing.
    """
    _instance: Optional['SCRFD10GFaceDetector'] = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        nms_threshold: Optional[float] = None,
        input_size: Optional[Tuple[int, int]] = None,
        min_face_size: Optional[int] = None,
        enable_tiled_inference: Optional[bool] = None,
        tile_size: Optional[int] = None,
        tile_overlap: Optional[float] = None,
        device: Optional[str] = None
    ):
        resolved_path = model_path or settings.SCRFD_MODEL_PATH
        if not os.path.isabs(resolved_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            candidate1 = os.path.join(backend_dir, resolved_path)
            candidate2 = os.path.abspath(resolved_path)
            candidate3 = os.path.join(backend_dir, "weights", "scrfd_10g_bnkps.onnx")
            if os.path.exists(candidate1):
                resolved_path = candidate1
            elif os.path.exists(candidate2):
                resolved_path = candidate2
            elif os.path.exists(candidate3):
                resolved_path = candidate3
        self.model_path = resolved_path

        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.SCRFD_CONFIDENCE_THRESHOLD
        self.nms_threshold = nms_threshold if nms_threshold is not None else settings.SCRFD_NMS_THRESHOLD
        size_val = settings.SCRFD_INPUT_SIZE if hasattr(settings, 'SCRFD_INPUT_SIZE') else 640
        self.input_size = input_size or (size_val, size_val)
        self.min_face_size = min_face_size if min_face_size is not None else getattr(settings, 'SCRFD_MIN_FACE_SIZE', 10)
        self.enable_tiled_inference = enable_tiled_inference if enable_tiled_inference is not None else getattr(settings, 'SCRFD_ENABLE_TILED_INFERENCE', True)
        self.tile_size = tile_size or getattr(settings, 'SCRFD_TILE_SIZE', 640)
        self.tile_overlap = tile_overlap or getattr(settings, 'SCRFD_TILE_OVERLAP', 0.25)
        self.requested_device = device or getattr(settings, 'SCRFD_DEVICE', 'cpu')

        # Model configuration parameters
        self.input_mean = 127.5
        self.input_std = 128.0
        self.fmc = 3
        self.feat_strides = [8, 16, 32]
        self.num_anchors = 2
        self.use_kps = True

        self.session = None
        self.active_provider = "CPUExecutionProvider"
        self._center_cache: Dict[Tuple[int, int, int], np.ndarray] = {}
        self._inference_lock = threading.Lock()
        self.fallback_detector = None

        self._initialize_session()

    def _initialize_session(self):
        """Initializes ONNX Runtime session with optimal execution providers."""
        if not os.path.exists(self.model_path):
            logger.warning(
                f"SCRFD-10G ONNX weights not found at '{self.model_path}'. "
                f"Falling back to YOLOv11n / OpenCV Haar detector."
            )
            self._setup_fallback()
            return

        try:
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            providers = []
            if self.requested_device.lower() == "cuda" and "CUDAExecutionProvider" in available_providers:
                providers.append("CUDAExecutionProvider")
                self.active_provider = "CUDAExecutionProvider"
            providers.append("CPUExecutionProvider")

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = max(1, os.cpu_count() // 2 if os.cpu_count() else 4)

            logger.info(f"Loading SCRFD-10G model from '{self.model_path}' with providers {providers}...")
            self.session = ort.InferenceSession(self.model_path, sess_options, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]
            logger.info(f"SCRFD-10G model loaded successfully. Provider: {self.session.get_providers()[0]}")

        except Exception as e:
            logger.error(f"Failed to initialize SCRFD-10G ONNX session: {e}. Activating fallback detector.")
            self.session = None
            self._setup_fallback()

    def _setup_fallback(self):
        """Initializes fallback detector hierarchy."""
        try:
            self.fallback_detector = YOLOv11nFaceDetector.get_instance()
        except Exception:
            self.fallback_detector = OpenCVHaarFaceDetector()

    @classmethod
    def get_instance(cls) -> 'SCRFD10GFaceDetector':
        with cls._lock:
            if cls._instance is None:
                cls._instance = SCRFD10GFaceDetector()
            return cls._instance

    def _generate_anchor_centers(self, feat_h: int, feat_w: int, stride: int) -> np.ndarray:
        """
        Generates or fetches cached grid anchor reference coordinates for a given feature map.
        """
        key = (feat_h, feat_w, stride)
        if key in self._center_cache:
            return self._center_cache[key]

        anchor_centers = np.stack(np.mgrid[:feat_h, :feat_w][::-1], axis=-1).astype(np.float32)
        anchor_centers = (anchor_centers * stride).reshape((-1, 2))
        if self.num_anchors > 1:
            anchor_centers = np.stack([anchor_centers] * self.num_anchors, axis=1).reshape((-1, 2))

        if len(self._center_cache) < 128:
            self._center_cache[key] = anchor_centers

        return anchor_centers

    def _forward_window(
        self,
        img_window: np.ndarray,
        target_size: Tuple[int, int],
        conf_threshold: float
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Runs SCRFD-10G ONNX inference on a single image window (or tile) with aspect-ratio preservation.
        Returns:
            bboxes: (N, 4) in [x1, y1, x2, y2] coordinates relative to window
            scores: (N, 1) in [0.0, 1.0]
            kpss: (N, 5, 2) in [(x, y), ...] coordinates relative to window
        """
        h_win, w_win = img_window.shape[:2]
        target_w, target_h = target_size

        im_ratio = float(h_win) / w_win
        model_ratio = float(target_h) / target_w
        if im_ratio > model_ratio:
            new_h = target_h
            new_w = int(new_h / im_ratio)
        else:
            new_w = target_w
            new_h = int(new_w * im_ratio)

        det_scale = float(new_h) / h_win
        resized = cv2.resize(img_window, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        det_img = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        det_img[:new_h, :new_w, :] = resized

        blob = cv2.dnn.blobFromImage(
            det_img,
            1.0 / self.input_std,
            (target_w, target_h),
            (self.input_mean, self.input_mean, self.input_mean),
            swapRB=True
        )

        with self._inference_lock:
            net_outs = self.session.run(self.output_names, {self.input_name: blob})

        scores_list = []
        bboxes_list = []
        kpss_list = []

        for idx, stride in enumerate(self.feat_strides):
            scores = net_outs[idx]
            bbox_preds = net_outs[idx + self.fmc] * stride
            kps_preds = net_outs[idx + self.fmc * 2] * stride if self.use_kps else None

            feat_h = target_h // stride
            feat_w = target_w // stride
            anchor_centers = self._generate_anchor_centers(feat_h, feat_w, stride)

            pos_inds = np.where(scores >= conf_threshold)[0]
            if len(pos_inds) == 0:
                continue

            x1 = anchor_centers[:, 0] - bbox_preds[:, 0]
            y1 = anchor_centers[:, 1] - bbox_preds[:, 1]
            x2 = anchor_centers[:, 0] + bbox_preds[:, 2]
            y2 = anchor_centers[:, 1] + bbox_preds[:, 3]
            bboxes = np.stack([x1, y1, x2, y2], axis=-1)

            scores_list.append(scores[pos_inds])
            bboxes_list.append(bboxes[pos_inds] / det_scale)

            if self.use_kps and kps_preds is not None:
                kpss = []
                for k in range(5):
                    kx = anchor_centers[:, 0] + kps_preds[:, k * 2]
                    ky = anchor_centers[:, 1] + kps_preds[:, k * 2 + 1]
                    kpss.append(kx)
                    kpss.append(ky)
                kpss_arr = np.stack(kpss, axis=-1).reshape((-1, 5, 2))
                kpss_list.append(kpss_arr[pos_inds] / det_scale)

        if not bboxes_list:
            kps_empty = np.empty((0, 5, 2), dtype=np.float32) if self.use_kps else None
            return np.empty((0, 4), dtype=np.float32), np.empty((0, 1), dtype=np.float32), kps_empty

        all_bboxes = np.vstack(bboxes_list).astype(np.float32, copy=False)
        all_scores = np.vstack(scores_list).astype(np.float32, copy=False)
        all_kpss = np.vstack(kpss_list).astype(np.float32, copy=False) if self.use_kps else None

        return all_bboxes, all_scores, all_kpss

    @staticmethod
    def _nms(bboxes: np.ndarray, scores: np.ndarray, thresh: float) -> List[int]:
        """
        Strict Non-Maximum Suppression (NMS) to eliminate duplicate detections.
        """
        if len(bboxes) == 0:
            return []

        x1 = bboxes[:, 0]
        y1 = bboxes[:, 1]
        x2 = bboxes[:, 2]
        y2 = bboxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.ravel().argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
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

    def detect_faces_with_landmarks(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects faces in classroom images with bounding boxes, confidence, and 5 facial keypoints.
        Includes high-resolution preservation and overlapping tiled inference for small/distant faces.
        """
        if image is None or image.size == 0:
            return []

        h_img, w_img = image.shape[:2]
        if h_img < 20 or w_img < 20:
            return []

        # Enforce maximum dimension safeguard
        max_dim = settings.MAX_IMAGE_DIMENSION
        if h_img > max_dim or w_img > max_dim:
            scale = max_dim / max(h_img, w_img)
            new_w = max(1, int(w_img * scale))
            new_h = max(1, int(h_img * scale))
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h_img, w_img = new_h, new_w

        if self.session is None:
            if self.fallback_detector is not None:
                return self.fallback_detector.detect_faces_with_landmarks(image, conf_threshold=conf_threshold)
            return []

        conf_thresh = conf_threshold if conf_threshold is not None else self.conf_threshold

        all_boxes_list = []
        all_scores_list = []
        all_kpss_list = []

        # 1. Global image inference (captures foreground & medium/large faces)
        global_boxes, global_scores, global_kpss = self._forward_window(
            image, self.input_size, conf_thresh
        )
        if len(global_boxes) > 0:
            all_boxes_list.append(global_boxes)
            all_scores_list.append(global_scores)
            if global_kpss is not None:
                all_kpss_list.append(global_kpss)

        # 2. Overlapping Tiled Inference for Large/Classroom Images (Detects small distant back-row faces)
        # Slices high-resolution image into tiles (tile_size x tile_size) with 25% overlap
        use_tiling = self.enable_tiled_inference and (w_img > 900 or h_img > 900)
        if use_tiling:
            tile_w = min(self.tile_size, w_img)
            tile_h = min(self.tile_size, h_img)
            step_x = max(64, int(tile_w * (1.0 - self.tile_overlap)))
            step_y = max(64, int(tile_h * (1.0 - self.tile_overlap)))

            x_steps = list(range(0, w_img - tile_w + 1, step_x))
            if not x_steps or x_steps[-1] != w_img - tile_w:
                x_steps.append(max(0, w_img - tile_w))

            y_steps = list(range(0, h_img - tile_h + 1, step_y))
            if not y_steps or y_steps[-1] != h_img - tile_h:
                y_steps.append(max(0, h_img - tile_h))

            # Limit total tiles to prevent latency spikes on enormous images
            max_tiles = 16
            tile_count = 0

            for y_off in y_steps:
                if tile_count >= max_tiles:
                    break
                for x_off in x_steps:
                    if tile_count >= max_tiles:
                        break
                    tile_crop = image[y_off:y_off + tile_h, x_off:x_off + tile_w]
                    t_boxes, t_scores, t_kpss = self._forward_window(
                        tile_crop, (tile_w, tile_h), conf_thresh
                    )

                    if len(t_boxes) > 0:
                        # Translate tile coordinates to global image coordinates
                        t_boxes_global = t_boxes.copy()
                        t_boxes_global[:, [0, 2]] += x_off
                        t_boxes_global[:, [1, 3]] += y_off
                        all_boxes_list.append(t_boxes_global)
                        all_scores_list.append(t_scores)

                        if t_kpss is not None:
                            t_kpss_global = t_kpss.copy()
                            t_kpss_global[:, :, 0] += x_off
                            t_kpss_global[:, :, 1] += y_off
                            all_kpss_list.append(t_kpss_global)

                    tile_count += 1

        if not all_boxes_list:
            return []

        merged_boxes = np.vstack(all_boxes_list)
        merged_scores = np.vstack(all_scores_list)
        merged_kpss = np.vstack(all_kpss_list) if all_kpss_list else None

        # 3. Apply Unified NMS across global + tiled detections to eliminate duplicates
        keep = self._nms(merged_boxes, merged_scores, self.nms_threshold)
        if not keep:
            return []

        final_boxes = merged_boxes[keep]
        final_scores = merged_scores[keep]
        final_kpss = merged_kpss[keep] if merged_kpss is not None else None

        results: List[Dict[str, Any]] = []

        for i in range(len(final_boxes)):
            x1, y1, x2, y2 = final_boxes[i]
            score = float(final_scores[i, 0])

            # Geometry & Boundary Clamping
            x1_clamped = max(0, min(float(x1), float(w_img - 1)))
            y1_clamped = max(0, min(float(y1), float(h_img - 1)))
            x2_clamped = max(0, min(float(x2), float(w_img)))
            y2_clamped = max(0, min(float(y2), float(h_img)))

            bw = x2_clamped - x1_clamped
            bh = y2_clamped - y1_clamped

            # Minimum face size & aspect ratio sanity checks
            if bw < self.min_face_size or bh < self.min_face_size:
                continue

            aspect_ratio = bh / bw if bw > 0 else 0
            if aspect_ratio < 0.4 or aspect_ratio > 3.0:
                continue

            kps_list = None
            if final_kpss is not None and i < len(final_kpss):
                raw_kps = final_kpss[i]
                kps_list = [
                    (float(max(0, min(raw_kps[k, 0], w_img - 1))), float(max(0, min(raw_kps[k, 1], h_img - 1))))
                    for k in range(5)
                ]

            x_int = int(round(x1_clamped))
            y_int = int(round(y1_clamped))
            w_int = int(round(bw))
            h_int = int(round(bh))

            results.append({
                "bbox": (x_int, y_int, w_int, h_int),
                "conf": round(score, 4),
                "landmarks": kps_list,
                "xyxy": (float(x1_clamped), float(y1_clamped), float(x2_clamped), float(y2_clamped))
            })

        # Sort detections descending by confidence
        results.sort(key=lambda item: item["conf"], reverse=True)
        return results

    def detect_faces_with_conf(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        BaseFaceDetector contract: returns list of ((x, y, w, h), conf).
        """
        detections = self.detect_faces_with_landmarks(image, conf_threshold=conf_threshold)
        return [(d["bbox"], d["conf"]) for d in detections]

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        BaseFaceDetector contract: returns list of (x, y, w, h) bounding boxes.
        """
        detections = self.detect_faces_with_conf(image)
        return [b for (b, _score) in detections]


def get_face_detector(backend: Optional[str] = None) -> BaseFaceDetector:
    """
    Returns the singleton face detector.
    - Defaults to SCRFD-10G ('SCRFD') with graceful fallback to YOLO / OpenCV Haar.
    - Allows explicit selection of 'YOLO' or 'SCRFD' for benchmarking.
    """
    target_backend = (backend or settings.DETECTOR_BACKEND).upper()

    if target_backend == "YOLO":
        return YOLOv11nFaceDetector.get_instance()

    # Default: SCRFD-10G
    scrfd_instance = SCRFD10GFaceDetector.get_instance()
    if scrfd_instance.session is not None:
        return scrfd_instance

    # If SCRFD weights are missing or failed, fallback to YOLO if available
    logger.warning("SCRFD session inactive; falling back to YOLO detector.")
    return YOLOv11nFaceDetector.get_instance()
