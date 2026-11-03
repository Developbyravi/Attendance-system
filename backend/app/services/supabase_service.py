import os
import uuid
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    """
    Centralized Supabase integration service for:
    - PostgreSQL database interactions / synchronization
    - Storage bucket operations (classroom-images, student-enrollments)
    - Auth & session management
    - Audit log recording
    - Graceful offline/local mode fallback when credentials are unconfigured or unavailable
    """
    _instance: Optional['SupabaseService'] = None

    def __init__(self):
        self.url = settings.SUPABASE_URL.strip()
        # Prefer service role key for authoritative backend operations if configured, else anon key
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY.strip() or settings.SUPABASE_KEY.strip()
        self.client = None
        self._is_configured = False
        self._initialize_client()

    def _initialize_client(self):
        """Attempts to initialize Supabase client if valid URL and key are provided."""
        if not self.url or not self.key or "your-project-ref" in self.url:
            logger.info("Supabase credentials not configured or set to placeholder. Operating in local mode.")
            self._is_configured = False
            return

        try:
            from supabase import create_client, Client
            self.client: Optional[Client] = create_client(self.url, self.key)
            self._is_configured = True
            logger.info(f"Supabase client initialized successfully for '{self.url}'.")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Operating in local mode.")
            self.client = None
            self._is_configured = False

    @classmethod
    def get_instance(cls) -> 'SupabaseService':
        if cls._instance is None:
            cls._instance = SupabaseService()
        return cls._instance

    @property
    def is_configured(self) -> bool:
        return self._is_configured and self.client is not None

    def upload_classroom_image(self, lecture_id: int, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Uploads teacher-uploaded classroom photo to Supabase Storage bucket 'classroom-images'.
        Falls back to local file storage if Supabase is unconfigured.
        """
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        storage_path = f"lecture_{lecture_id}/{uuid.uuid4().hex[:12]}{ext}"
        bucket_name = settings.SUPABASE_STORAGE_BUCKET_CLASSROOM

        if self.is_configured:
            try:
                response = self.client.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                public_url = self.client.storage.from_(bucket_name).get_public_url(storage_path)
                return {
                    "storage": "supabase",
                    "bucket": bucket_name,
                    "path": storage_path,
                    "url": public_url
                }
            except Exception as e:
                logger.error(f"Supabase Storage upload failed: {e}. Falling back to local storage.")

        # Local storage fallback
        local_dir = os.path.join(settings.STORAGE_DIR, f"classroom_lecture_{lecture_id}")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, f"{uuid.uuid4().hex[:12]}{ext}")
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        return {
            "storage": "local",
            "bucket": "local",
            "path": local_path,
            "url": f"/storage/classroom/{os.path.basename(local_path)}"
        }

    def upload_student_enrollment_image(self, student_id: int, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Uploads student face enrollment photo to Supabase Storage bucket 'student-enrollments'.
        Falls back to local sanitized storage if Supabase is unconfigured.
        """
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        storage_path = f"student_{student_id}/{uuid.uuid4().hex[:12]}{ext}"
        bucket_name = settings.SUPABASE_STORAGE_BUCKET_STUDENTS

        if self.is_configured:
            try:
                self.client.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                public_url = self.client.storage.from_(bucket_name).get_public_url(storage_path)
                return {
                    "storage": "supabase",
                    "bucket": bucket_name,
                    "path": storage_path,
                    "url": public_url
                }
            except Exception as e:
                logger.error(f"Supabase Storage upload failed: {e}. Falling back to local storage.")

        # Local storage fallback
        local_path = os.path.join(settings.STORAGE_DIR, f"student_{student_id}_{uuid.uuid4().hex[:10]}{ext}")
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        return {
            "storage": "local",
            "bucket": "local",
            "path": local_path,
            "url": f"/storage/student/{os.path.basename(local_path)}"
        }

    def log_audit_event(
        self,
        user_id: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None,
        db_session=None
    ):
        """
        Records an audit event in Supabase and/or local database.
        """
        payload = {
            "user_id": str(user_id),
            "role": role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "details": json.dumps(details or {}),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # 1. Supabase Audit Log Table
        if self.is_configured:
            try:
                self.client.table("audit_logs").insert(payload).execute()
            except Exception as e:
                logger.warning(f"Failed to write audit log to Supabase: {e}")

        # 2. Local Database Session
        if db_session:
            try:
                from app.models.audit_log import AuditLogModel
                log_record = AuditLogModel(
                    user_id=str(user_id),
                    role=role,
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    details=json.dumps(details or {})
                )
                db_session.add(log_record)
                db_session.commit()
            except Exception as e:
                logger.warning(f"Failed to write local audit log: {e}")

    # ── LIVE SUPABASE DATA RETRIEVAL & SYNCHRONIZATION ─────────────────────────

    def get_admin_stats(self) -> Dict[str, Any]:
        """
        Calculates genuine institution-wide statistics directly from Supabase tables:
        - total_students: active registered students
        - total_teachers: active faculty members
        - today_checkins: daily check-ins for current date
        - today_lectures: lecture sessions for current date
        - pending_flagged_cases: unfinalized attendances with FLAGGED status
        - overall_attendance_rate: finalized present / total finalized (or None if no finalized records)
        """
        if not self.is_configured:
            return {
                "total_students": 0,
                "total_teachers": 0,
                "today_checkins": 0,
                "today_lectures": 0,
                "overall_attendance_rate": None,
                "pending_flagged_cases": 0
            }

        today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            # 1. Total active registered students in Supabase
            res_stu = self.client.table("students").select("id", count="exact").eq("is_active", True).execute()
            total_students = res_stu.count if res_stu.count is not None else 0

            # 2. Total active faculty in Supabase
            res_tea = self.client.table("teachers").select("id", count="exact").eq("is_active", True).execute()
            total_teachers = res_tea.count if res_tea.count is not None else 0

            # 3. Real daily RFID check-ins for today in Supabase
            res_chk = self.client.table("daily_checkins").select("id", count="exact").eq("date", today_iso).execute()
            today_checkins = res_chk.count if res_chk.count is not None else 0

            # 4. Actual lecture sessions scheduled for today in Supabase
            res_lec = self.client.table("lecture_sessions").select("id", count="exact").eq("date", today_iso).execute()
            today_lectures = res_lec.count if res_lec.count is not None else 0

            # 5. Review pending flagged attendances in Supabase
            res_flg = self.client.table("lecture_attendances").select("id", count="exact").eq("status", "FLAGGED").execute()
            pending_flagged = res_flg.count if res_flg.count is not None else 0

            # 6. Overall attendance rate from finalized records in Supabase
            res_fin_all = self.client.table("lecture_attendances").select("id", count="exact").eq("finalized", True).execute()
            total_finalized = res_fin_all.count if res_fin_all.count is not None else 0

            if total_finalized > 0:
                res_fin_pres = self.client.table("lecture_attendances").select("id", count="exact").eq("finalized", True).eq("status", "PRESENT").execute()
                present_finalized = res_fin_pres.count if res_fin_pres.count is not None else 0
                overall_rate = round((present_finalized / total_finalized) * 100, 1)
            else:
                overall_rate = None

            return {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "today_checkins": today_checkins,
                "today_lectures": today_lectures,
                "overall_attendance_rate": overall_rate,
                "pending_flagged_cases": pending_flagged
            }
        except Exception as e:
            logger.error(f"Error querying live admin stats from Supabase: {e}")
            raise

    def get_students(self, division: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch students directly from Supabase table 'students'."""
        if not self.is_configured:
            return []
        try:
            query = self.client.table("students").select("*")
            if division:
                query = query.eq("division", division)
            if search:
                query = query.or_(f"name.ilike.%{search}%,roll_no.ilike.%{search}%,email.ilike.%{search}%")
            res = query.order("id", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error querying students from Supabase: {e}")
            return []

    def sync_student(self, student_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Inserts or updates a student in Supabase."""
        if not self.is_configured:
            return None
        try:
            clean_payload = {k: v for k, v in student_payload.items() if v is not None}
            res = self.client.table("students").upsert(clean_payload, on_conflict="roll_no").execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error syncing student to Supabase: {e}")
            return None

    def sync_rfid_uid(self, student_id: int, rfid_uid: Optional[str]) -> bool:
        """Updates RFID UID for student in Supabase."""
        if not self.is_configured:
            return False
        try:
            self.client.table("students").update({"rfid_uid": rfid_uid or ""}).eq("id", student_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating RFID UID in Supabase: {e}")
            return False

    def get_teachers(self, department: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch faculty directly from Supabase table 'teachers'."""
        if not self.is_configured:
            return []
        try:
            query = self.client.table("teachers").select("*")
            if department:
                query = query.eq("department", department)
            if search:
                query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
            res = query.order("id", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error querying teachers from Supabase: {e}")
            return []

    def sync_teacher(self, teacher_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Inserts or updates faculty member in Supabase."""
        if not self.is_configured:
            return None
        try:
            clean_payload = {k: v for k, v in teacher_payload.items() if v is not None}
            res = self.client.table("teachers").upsert(clean_payload).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error syncing teacher to Supabase: {e}")
            return None

    def get_divisions(self) -> List[Dict[str, Any]]:
        """Fetch divisions directly from Supabase table 'divisions'."""
        if not self.is_configured:
            return []
        try:
            res = self.client.table("divisions").select("*").order("name").execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error querying divisions from Supabase: {e}")
            return []

    def sync_division(self, division_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Inserts a division record into Supabase."""
        if not self.is_configured:
            return None
        try:
            res = self.client.table("divisions").insert(division_payload).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error syncing division to Supabase: {e}")
            return None

    def get_daily_checkins(self, date_val: str, division: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch daily RFID check-ins directly from Supabase."""
        if not self.is_configured:
            return []
        try:
            query = self.client.table("daily_checkins").select("*, students(name, roll_no, division)").eq("date", date_val)
            res = query.order("first_scan_time", desc=True).execute()
            records = []
            for item in res.data or []:
                student_info = item.get("students") or {}
                if division and student_info.get("division") != division:
                    continue
                records.append({
                    "id": item.get("id"),
                    "student_id": item.get("student_id"),
                    "student_name": student_info.get("name", "Unknown"),
                    "roll_number": student_info.get("roll_no", ""),
                    "division_name": f"Division {student_info.get('division', '')}",
                    "rfid_uid": item.get("rfid_uid"),
                    "device_id": item.get("device_id") or "GATE-01",
                    "check_in_time": item.get("first_scan_time"),
                    "is_verified": True
                })
            return records
        except Exception as e:
            logger.error(f"Error querying daily check-ins from Supabase: {e}")
            return []

    def sync_daily_checkin(self, checkin_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Inserts or updates a daily RFID check-in in Supabase."""
        if not self.is_configured:
            return None
        try:
            res = self.client.table("daily_checkins").upsert(
                checkin_payload,
                on_conflict="student_id,date"
            ).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error syncing daily checkin to Supabase: {e}")
            return None


supabase_service = SupabaseService.get_instance()

def get_supabase_service() -> SupabaseService:
    return supabase_service
