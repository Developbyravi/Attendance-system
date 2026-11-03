import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Computes Cosine Similarity between two L2-normalized vectors."""
    if not emb1 or not emb2 or len(emb1) != len(emb2):
        return 0.0
    v1 = np.array(emb1, dtype=np.float32)
    v2 = np.array(emb2, dtype=np.float32)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    dot = float(np.dot(v1, v2))
    return float(np.clip(dot / (norm1 * norm2), -1.0, 1.0))

class FaceMatchingEngine:
    """
    Robust Face Matching and Disambiguation Engine.
    - Prevents self-conflict across duplicate accounts of the same student.
    - Accurately discriminates distinct identities using Cosine Similarity & margin checks.
    - Handles classroom multi-face deduplication.
    """
    def __init__(
        self,
        threshold: float = settings.FACE_MATCH_THRESHOLD,
        ambiguity_threshold: float = settings.FACE_AMBIGUITY_THRESHOLD
    ):
        self.threshold = threshold
        self.ambiguity_threshold = ambiguity_threshold

    def match_face(
        self,
        query_embedding: Optional[List[float]],
        enrolled_student_map: Dict[int, Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compares query face vector against enrolled division student templates.
        Returns:
            status: "recognized" | "ambiguous" | "unknown"
            similarity: float
            student: Dict or None
            ambiguity_details: Dict (if ambiguous)
        """
        if query_embedding is None or len(query_embedding) == 0:
            return {"status": "unknown", "similarity": 0.0, "student": None}

        active_thresh = threshold if threshold is not None else self.threshold
        norm_query = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(norm_query)
        if q_norm == 0:
            return {"status": "unknown", "similarity": 0.0, "student": None}
        norm_query = norm_query / q_norm

        scores = []
        for sid, student_data in enrolled_student_map.items():
            embeddings = student_data.get("embeddings", [])
            if not embeddings:
                continue

            max_score = 0.0
            for emb in embeddings:
                try:
                    emb_arr = np.array(emb, dtype=np.float32)
                    e_norm = np.linalg.norm(emb_arr)
                    if e_norm > 0:
                        score = float(np.dot(norm_query, emb_arr / e_norm))
                        if score > max_score:
                            max_score = score
                except Exception:
                    continue

            scores.append((max_score, student_data["student"]))

        if not scores:
            return {"status": "unknown", "similarity": 0.0, "student": None}

        scores.sort(key=lambda x: x[0], reverse=True)
        top_1_score, top_1_student = scores[0]

        if top_1_score < active_thresh:
            return {
                "status": "unknown",
                "similarity": round(top_1_score, 3),
                "confidence": round(top_1_score, 3),
                "student": None
            }

        # Consolidate candidates: If candidate 2 represents the exact same student/name as candidate 1,
        # merge them so a student does not declare ambiguity against themselves.
        top_name = (top_1_student.get("name") or "").strip().lower()
        competing_candidates = []
        for sc, st in scores:
            if sc >= active_thresh and (top_1_score - sc) < self.ambiguity_threshold:
                cand_name = (st.get("name") or "").strip().lower()
                # Check if this candidate is genuinely a distinct student
                competing_candidates.append({
                    "student": st,
                    "similarity": round(sc, 3),
                    "is_same_person": (cand_name == top_name)
                })

        # Distinct candidates with different names
        distinct_competing = [c for c in competing_candidates if not c.get("is_same_person")]

        if len(distinct_competing) > 0:
            top_2 = distinct_competing[0]
            diff = top_1_score - top_2["similarity"]
            return {
                "status": "ambiguous",
                "similarity": round(top_1_score, 3),
                "confidence": round(top_1_score, 3),
                "student": top_1_student,
                "ambiguity_details": {
                    "primary_candidate": top_1_student,
                    "primary_similarity": round(top_1_score, 3),
                    "secondary_candidate": top_2["student"],
                    "secondary_similarity": round(top_2["similarity"], 3),
                    "margin": round(diff, 4),
                    "candidates": [c for c in competing_candidates]
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
        parsed_detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Orchestrates multi-face recognition, ambiguity filtering, and duplicate resolution.
        """
        recognized_map: Dict[int, Dict[str, Any]] = {}
        ambiguous_list: List[Dict[str, Any]] = []
        unknown_list: List[Dict[str, Any]] = []
        duplicate_list: List[Dict[str, Any]] = []
        assigned_student_ids: set[int] = set()

        # 1. Recognized faces
        recognized = [d for d in parsed_detections if d.get("match_status") == "recognized"]
        recognized.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        for rec in recognized:
            st = rec.get("student")
            if not st:
                unknown_list.append(rec)
                continue
            sid = st["id"]
            if sid not in assigned_student_ids:
                assigned_student_ids.add(sid)
                recognized_map[sid] = rec
            else:
                rec["match_status"] = "duplicate"
                duplicate_list.append(rec)

        # 2. Ambiguous faces
        ambiguous = [d for d in parsed_detections if d.get("match_status") == "ambiguous"]
        for amb in ambiguous:
            details = amb.get("ambiguity_details", {})
            candidates = details.get("candidates", [])
            unassigned = [c for c in candidates if c.get("student", {}).get("id") not in assigned_student_ids]

            if len(unassigned) == 1:
                best = unassigned[0]
                sid = best["student"]["id"]
                assigned_student_ids.add(sid)
                amb["match_status"] = "recognized"
                amb["student"] = best["student"]
                amb["similarity"] = best["similarity"]
                recognized_map[sid] = amb
            else:
                ambiguous_list.append(amb)

        # 3. Unknown faces
        unknown = [d for d in parsed_detections if d.get("match_status") == "unknown"]
        unknown_list.extend(unknown)

        return {
            "recognized": recognized_map,
            "ambiguous": ambiguous_list,
            "unknown": unknown_list,
            "duplicates": duplicate_list
        }

