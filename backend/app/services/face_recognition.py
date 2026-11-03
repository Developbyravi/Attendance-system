import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.services.face_embedding import get_face_embedder
from app.services.face_detector import get_face_detector

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """
    Real Classroom Face Recognition Service.
    Singleton service loaded once on application startup.
    Provides:
    - 512-d normalized embedding generation (ArcFace-MobileFaceNet)
    - Cosine similarity evaluation
    - Separation of detector confidence vs face identity similarity
    - Ambiguity checking (distinguishes near-tie candidates)
    - Multi-face query matching & duplicate detection resolution
    """
    _instance: Optional['FaceRecognitionService'] = None

    def __init__(self):
        self.embedder = get_face_embedder()
        self.detector = get_face_detector()
        self.model_name = settings.MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.threshold = settings.FACE_RECOGNITION_THRESHOLD
        self.ambiguity_threshold = settings.FACE_AMBIGUITY_THRESHOLD
        self.is_loaded = True

    @classmethod
    def get_instance(cls) -> 'FaceRecognitionService':
        if cls._instance is None:
            cls._instance = FaceRecognitionService()
        return cls._instance

    def get_model_info(self) -> Dict[str, Any]:
        """
        Exposes current model metadata and threshold config for API status checks.
        """
        detector_name = "InsightFace SCRFD-10G" if "SCRFD" in type(self.detector).__name__ else type(self.detector).__name__
        return {
            "model": self.model_name,
            "embedding_dimension": self.dimension,
            "detector": detector_name,
            "recognition_threshold": self.threshold,
            "ambiguity_threshold": self.ambiguity_threshold,
            "status": "loaded" if self.is_loaded else "unloaded"
        }

    def generate_embedding(self, face_image: np.ndarray) -> List[float]:
        """
        Generates normalized 512-d embedding vector.
        """
        return self.embedder.generate_embedding(face_image)

    def compare_embeddings(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Computes Cosine Similarity between two L2-normalized vectors.
        Result range: [-1.0, 1.0] (1.0 = identical face).
        """
        if emb1 is None or emb2 is None or len(emb1) == 0 or len(emb2) == 0 or len(emb1) != len(emb2):
            return 0.0

        v1 = np.array(emb1, dtype=np.float32)
        v2 = np.array(emb2, dtype=np.float32)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        dot_product = float(np.dot(v1, v2))
        cosine_sim = dot_product / (norm1 * norm2)
        return float(np.clip(cosine_sim, -1.0, 1.0))

    def match_face(
        self,
        query_embedding: Optional[List[float]],
        enrolled_student_map: Dict[int, Dict[str, Any]],
        threshold: Optional[float] = None,
        excluded_student_ids: Optional[set[int]] = None
    ) -> Dict[str, Any]:
        """
        Compares query face vector against all enrolled embeddings per student.
        - Evaluates top candidates to check for ambiguity within ambiguity_threshold.
        - Never forces an unknown face to match if similarity < threshold.
        - Safely handles failed or empty embedding vectors.
        - Returns:
            status: "recognized" | "ambiguous" | "unknown"
            similarity: float
            confidence: float (alias for backward compatibility)
            student: Dict or None
        """
        if query_embedding is None or len(query_embedding) == 0:
            return {
                "status": "unknown",
                "similarity": 0.0,
                "confidence": 0.0,
                "student": None,
                "error": "embedding_extraction_failed"
            }

        cutoff_threshold = threshold if threshold is not None else self.threshold

        scores: List[Tuple[float, Dict[str, Any]]] = []

        for student_id, data in enrolled_student_map.items():
            if excluded_student_ids and student_id in excluded_student_ids:
                continue

            embeddings_list: List[List[float]] = data.get("embeddings", [])
            
            student_max_score = 0.0
            for emb in embeddings_list:
                sim = self.compare_embeddings(query_embedding, emb)
                if sim > student_max_score:
                    student_max_score = sim

            scores.append((student_max_score, data["student"]))

        # Sort descending by similarity
        scores.sort(key=lambda x: x[0], reverse=True)

        if not scores or scores[0][0] < cutoff_threshold:
            best_score = scores[0][0] if scores else 0.0
            return {
                "status": "unknown",
                "similarity": round(max(best_score, 0.0), 3),
                "confidence": round(max(best_score, 0.0), 3),
                "student": None
            }

        top_1_score, top_1_student = scores[0]

        # Eligible competing candidates must meet cutoff_threshold AND be within ambiguity_threshold of top-1
        competing_candidates = [
            {"student": s, "similarity": round(sc, 3)}
            for sc, s in scores
            if sc >= cutoff_threshold and (top_1_score - sc) < self.ambiguity_threshold
        ]

        if len(competing_candidates) > 1:
            top_2_score, top_2_student = scores[1]
            diff = top_1_score - top_2_score
            return {
                "status": "ambiguous",
                "similarity": round(top_1_score, 3),
                "confidence": round(top_1_score, 3),
                "student": top_1_student,
                "ambiguity_details": {
                    "primary_candidate": top_1_student,
                    "primary_similarity": round(top_1_score, 3),
                    "secondary_candidate": top_2_student,
                    "secondary_similarity": round(top_2_score, 3),
                    "margin": round(diff, 4),
                    "candidates": competing_candidates
                }
            }

        return {
            "status": "recognized",
            "similarity": round(top_1_score, 3),
            "confidence": round(top_1_score, 3),
            "student": top_1_student
        }

    def process_classroom_detections(
        self,
        detected_faces: List[Dict[str, Any]], # [{"bbox": ..., "conf": ..., "face_crop": ...}]
        enrolled_student_map: Dict[int, Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Processes all detected faces from a classroom image independently:
        - Extracts embeddings safely (handling failures gracefully)
        - Matches against division student enrollments
        - Prevents two different faces from being assigned to the same student
        - Deduplicates repeated detections of the same student
        - Disambiguates candidate overlaps across multiple faces
        - Segregates recognized, ambiguous, unknown, and duplicate faces
        """
        recognized_map: Dict[int, Dict[str, Any]] = {} # student_id -> best match
        ambiguous_list: List[Dict[str, Any]] = []
        unknown_list: List[Dict[str, Any]] = []
        duplicate_list: List[Dict[str, Any]] = []
        assigned_student_ids: set[int] = set()

        parsed_detections: List[Dict[str, Any]] = []

        for item in detected_faces:
            crop = item.get("face_crop")
            detector_conf = item.get("conf", 1.0)
            bbox = item.get("bbox")

            query_vec = item.get("embedding")
            if query_vec is None:
                if crop is not None and getattr(crop, "size", 0) > 0:
                    try:
                        query_vec = self.generate_embedding(crop)
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for face crop: {e}")
                        query_vec = None
                else:
                    try:
                        query_vec = self.generate_embedding(crop)
                    except Exception:
                        query_vec = None


            match_res = self.match_face(query_vec, enrolled_student_map, threshold=threshold)

            sim_val = match_res.get("similarity")
            if sim_val is None:
                sim_val = match_res.get("confidence", 0.0)

            record = {
                "bbox": bbox,
                "detector_confidence": detector_conf,
                "landmarks": item.get("landmarks"),
                "similarity": sim_val,
                "confidence": sim_val,
                "match_status": match_res.get("status", "unknown"),
                "student": match_res.get("student")
            }
            if "ambiguity_details" in match_res:
                record["ambiguity_details"] = match_res["ambiguity_details"]

            parsed_detections.append(record)

        # 1. Process recognized matches first, sorted by similarity descending
        recognized_candidates = [d for d in parsed_detections if d["match_status"] == "recognized"]
        recognized_candidates.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        for rec in recognized_candidates:
            st = rec.get("student")
            if not st:
                unknown_list.append(rec)
                continue
            sid = st["id"]
            if sid not in assigned_student_ids:
                assigned_student_ids.add(sid)
                recognized_map[sid] = rec
            else:
                # Same student already recognized on a higher-confidence face -> duplicate detection
                rec["match_status"] = "duplicate"
                duplicate_list.append(rec)

        # 2. Process ambiguous detections, filtering candidates against already assigned identities
        ambiguous_candidates = [d for d in parsed_detections if d["match_status"] == "ambiguous"]
        for amb in ambiguous_candidates:
            details = amb.get("ambiguity_details", {})
            candidates = details.get("candidates", [])
            # Filter out candidates already assigned to other distinct faces
            unassigned_candidates = [c for c in candidates if c.get("student", {}).get("id") not in assigned_student_ids]

            if len(unassigned_candidates) == 1:
                # Ambiguity is resolved: the competing candidate is assigned to another face
                resolved = unassigned_candidates[0]
                resolved_st = resolved["student"]
                sid = resolved_st["id"]
                if sid not in assigned_student_ids:
                    assigned_student_ids.add(sid)
                    amb["match_status"] = "recognized"
                    amb["student"] = resolved_st
                    amb["similarity"] = resolved["similarity"]
                    amb["confidence"] = resolved["similarity"]
                    amb["resolved_student"] = resolved_st
                    amb["resolved_similarity"] = resolved["similarity"]
                    recognized_map[sid] = amb
                else:
                    amb["match_status"] = "duplicate"
                    duplicate_list.append(amb)
            elif len(unassigned_candidates) == 0:
                # All competing candidates already assigned to other faces -> duplicate detection
                amb["match_status"] = "duplicate"
                duplicate_list.append(amb)
            else:
                # Still ambiguous among remaining unassigned candidates
                amb["ambiguity_details"]["candidates"] = unassigned_candidates
                ambiguous_list.append(amb)

        # 3. Process unknown detections
        unknown_candidates = [d for d in parsed_detections if d["match_status"] == "unknown"]
        for unk in unknown_candidates:
            unknown_list.append(unk)

        return {
            "recognized": recognized_map,
            "ambiguous": ambiguous_list,
            "unknown": unknown_list,
            "duplicates": duplicate_list
        }


face_recognition_service = FaceRecognitionService.get_instance()

def get_face_recognition_service() -> FaceRecognitionService:
    return face_recognition_service
