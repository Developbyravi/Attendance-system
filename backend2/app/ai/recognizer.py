import logging
import threading
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings
from app.ai.detector import SCRFD10GFaceDetector
from app.ai.embedding import ArcFaceMobileFaceNetEmbedder
from app.ai.matching import FaceMatchingEngine, cosine_similarity
from app.ai.preprocessing import crop_and_align_face

logger = logging.getLogger(__name__)

class FaceRecognitionPipeline:
    """
    Unified AI Face Recognition Pipeline for SmartAttend.
    Coordinates:
    - InsightFace SCRFD-10G Face Detection & 5-point Keypoints
    - Canonical 112x112 Affine Landmark Alignment
    - ArcFace-MobileFaceNet 512-D L2-Normalized Feature Vector Embedding
    - Disambiguated Cosine Similarity Matching & Multi-Face Deduplication
    """
    _instance: Optional['FaceRecognitionPipeline'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.detector = SCRFD10GFaceDetector.get_instance()
        self.embedder = ArcFaceMobileFaceNetEmbedder(dimension=settings.EMBEDDING_DIMENSION)
        self.matcher = FaceMatchingEngine(
            threshold=settings.FACE_MATCH_THRESHOLD,
            ambiguity_threshold=settings.FACE_AMBIGUITY_THRESHOLD
        )
        self.model_name = settings.FACE_RECOGNITION_MODEL
        self.detector_name = settings.FACE_DETECTOR_MODEL

    @classmethod
    def get_instance(cls) -> 'FaceRecognitionPipeline':
        with cls._lock:
            if cls._instance is None:
                cls._instance = FaceRecognitionPipeline()
            return cls._instance

    def get_model_info(self) -> Dict[str, Any]:
        """Reports AI engine diagnostic metadata for health endpoints."""
        return {
            "model": self.model_name,
            "detector": self.detector_name,
            "detector_loaded": self.detector.session is not None,
            "active_provider": self.detector.active_provider,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "recognition_threshold": settings.FACE_MATCH_THRESHOLD,
            "ambiguity_threshold": settings.FACE_AMBIGUITY_THRESHOLD,
            "status": "loaded"
        }

    def detect_and_align(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects all faces in an image and aligns them to standard 112x112 crops.
        """
        raw_detections = self.detector.detect_faces_with_landmarks(image)
        items = []
        for det in raw_detections:
            bbox = det["bbox"]
            landmarks = det.get("landmarks")
            crop = crop_and_align_face(image, bbox, landmarks=landmarks)
            items.append({
                "bbox": bbox,
                "conf": det["conf"],
                "landmarks": landmarks,
                "face_crop": crop
            })
        return items

    def generate_embedding(self, face_crop: np.ndarray) -> List[float]:
        """Generates 512-D L2-normalized embedding vector from face crop."""
        return self.embedder.generate_embedding(face_crop)

    def compare_embeddings(self, emb1: List[float], emb2: List[float]) -> float:
        """Evaluates Cosine Similarity between two embeddings."""
        return cosine_similarity(emb1, emb2)

    def identify_classroom_faces(
        self,
        image: np.ndarray,
        enrolled_student_map: Dict[int, Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end classroom photograph processing pipeline.
        1. Detects faces & 5 landmarks via SCRFD-10G.
        2. Aligns faces to 112x112 via affine transformation.
        3. Extracts ArcFace embeddings.
        4. Matches against enrolled division templates.
        5. Returns structured categorized detections.
        """
        aligned_items = self.detect_and_align(image)
        parsed_detections: List[Dict[str, Any]] = []

        for item in aligned_items:
            crop = item["face_crop"]
            embedding = self.generate_embedding(crop)
            match_res = self.matcher.match_face(embedding, enrolled_student_map, threshold=threshold)

            record = {
                "bbox": item["bbox"],
                "detector_confidence": item["conf"],
                "landmarks": item["landmarks"],
                "embedding": embedding,
                "similarity": match_res.get("similarity", 0.0),
                "confidence": match_res.get("similarity", 0.0),
                "match_status": match_res.get("status", "unknown"),
                "student": match_res.get("student")
            }
            if "ambiguity_details" in match_res:
                record["ambiguity_details"] = match_res["ambiguity_details"]

            parsed_detections.append(record)

        processed = self.matcher.process_classroom_detections(parsed_detections)
        processed["detected_items"] = parsed_detections
        return processed

