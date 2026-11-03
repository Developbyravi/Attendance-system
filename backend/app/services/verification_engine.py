from typing import List, Dict, Any, Optional

class VerificationEngine:
    """
    Core RFID + AI Cross-Verification Engine for Per-Lecture Attendance.
    Cross-references AI classroom face recognition against today's Daily RFID Check-ins
    filtered strictly by the target lecture's division.
    """

    @staticmethod
    def compute_lecture_verification_matrix(
        division_students: List[Dict[str, Any]],
        daily_checked_in_student_ids: set[int],
        ai_recognized_map: Dict[int, float], # { student_id: confidence }
        unknown_faces_list: Optional[List[Dict[str, Any]]] = None,
        auto_mark_absent: bool = False
    ) -> Dict[str, Any]:
        """
        Computes lecture attendance matrix for all active students in the lecture's division.
        If auto_mark_absent is False (default for active lectures), undetected students
        without RFID check-ins remain PENDING (unverified) until lecture finalization
        or teacher review, preventing premature absence marking from a single photograph.
        """
        results = []
        verified_present_count = 0
        rfid_only_count = 0
        ai_only_count = 0
        absent_count = 0
        pending_count = 0

        for student in division_students:
            sid = student["id"]
            has_rfid = sid in daily_checked_in_student_ids
            has_ai = sid in ai_recognized_map
            ai_conf = ai_recognized_map.get(sid, 0.0)

            if has_rfid and has_ai:
                status = "PRESENT"
                source = "RFID_AND_AI"
                verified_present_count += 1
            elif has_rfid and not has_ai:
                status = "FLAGGED"
                source = "RFID_ONLY"
                rfid_only_count += 1
            elif not has_rfid and has_ai:
                status = "FLAGGED"
                source = "AI_ONLY"
                ai_only_count += 1
            else:
                if auto_mark_absent:
                    status = "ABSENT"
                    source = "ABSENT"
                    absent_count += 1
                else:
                    status = "PENDING"
                    source = "UNVERIFIED"
                    pending_count += 1

            results.append({
                "student_id": sid,
                "student_name": student["name"],
                "roll_no": student["roll_no"],
                "department": student.get("department", ""),
                "division": student.get("division", ""),
                "status": status,
                "verification_source": source,
                "ai_confidence": round(ai_conf, 3) if has_ai else None,
                "rfid_checked_in": has_rfid,
                "ai_detected": has_ai,
                "teacher_action": None,
                "finalized": False
            })

        unknown_count = len(unknown_faces_list) if unknown_faces_list else 0

        return {
            "daily_rfid_checked_in": len(daily_checked_in_student_ids.intersection({s["id"] for s in division_students})),
            "ai_detected_count": len(ai_recognized_map),
            "verified_present": verified_present_count,
            "rfid_only": rfid_only_count,
            "ai_only": ai_only_count,
            "absent": absent_count,
            "pending": pending_count,
            "unknown_faces": unknown_count,
            "results": results
        }
