import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.student import StudentModel
from app.models.user import UserModel
from app.models.face_embedding import FaceEmbeddingModel
from app.core.security import get_password_hash
from app.core.exceptions import EntityNotFoundError, DuplicateEntityError, FaceBiometricError
from app.ai.preprocessing import decode_image_bytes, crop_and_align_face, validate_image_security
from app.ai.detector import SCRFD10GFaceDetector
from app.ai.embedding import ArcFaceMobileFaceNetEmbedder
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

class StudentService:
    @staticmethod
    def get_all(
        db: Session,
        division_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[StudentModel]:
        q = db.query(StudentModel).filter(StudentModel.is_active == True)

        if division_id:
            clean_div = division_id.replace("Division ", "").replace("Div ", "").strip()
            q = q.filter(
                or_(
                    StudentModel.division == clean_div,
                    StudentModel.division == f"Div {clean_div}",
                    StudentModel.division == f"Division {clean_div}"
                )
            )

        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    StudentModel.name.ilike(pattern),
                    StudentModel.roll_no.ilike(pattern),
                    StudentModel.email.ilike(pattern)
                )
            )

        return q.order_by(StudentModel.id.asc()).all()

    @staticmethod
    def get_by_id(db: Session, student_id: int) -> StudentModel:
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            raise EntityNotFoundError("Student", student_id)
        return student

    @staticmethod
    def create(db: Session, data: Dict[str, Any]) -> StudentModel:
        # Check email uniqueness
        email = data.get("email", "").strip().lower()
        if db.query(StudentModel).filter(StudentModel.email == email).first():
            raise DuplicateEntityError("Student", "email", email)

        # Check roll_no uniqueness
        roll_no = data.get("roll_no", "").strip()
        if db.query(StudentModel).filter(StudentModel.roll_no == roll_no).first():
            raise DuplicateEntityError("Student", "roll_no", roll_no)

        # Check RFID card uniqueness if provided
        rfid_uid = data.get("rfid_uid")
        if rfid_uid:
            clean_rfid = rfid_uid.strip().upper()
            if db.query(StudentModel).filter(StudentModel.rfid_uid == clean_rfid).first():
                raise DuplicateEntityError("Student", "rfid_uid", clean_rfid)

        # Provision UserModel credentials if not existing
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            password = data.get("password") or "Student@123"
            user = UserModel(
                email=email,
                username=roll_no,
                full_name=data.get("name", "Student"),
                hashed_password=get_password_hash(password),
                role="STUDENT",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        clean_div = (data.get("division") or "A").replace("Div ", "").replace("Division ", "").strip()
        student = StudentModel(
            user_id=user.id,
            roll_no=roll_no,
            name=data.get("name", "").strip(),
            email=email,
            department=data.get("department", "Computer Science & Engineering"),
            year=data.get("year", "3rd Year"),
            division=clean_div,
            rfid_uid=rfid_uid.strip().upper() if rfid_uid else None,
            face_enrolled=False,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update(db: Session, student_id: int, data: Dict[str, Any]) -> StudentModel:
        student = StudentService.get_by_id(db, student_id)

        for field in ["name", "department", "year", "division", "is_active"]:
            if field in data and data[field] is not None:
                setattr(student, field, data[field])

        if "email" in data and data["email"]:
            new_email = data["email"].strip().lower()
            if new_email != student.email:
                if db.query(StudentModel).filter(StudentModel.email == new_email).first():
                    raise DuplicateEntityError("Student", "email", new_email)
                student.email = new_email

        if "rfid_uid" in data:
            rfid = data["rfid_uid"]
            if rfid:
                clean_rfid = rfid.strip().upper()
                if clean_rfid != student.rfid_uid:
                    if db.query(StudentModel).filter(StudentModel.rfid_uid == clean_rfid).first():
                        raise DuplicateEntityError("Student", "rfid_uid", clean_rfid)
                    student.rfid_uid = clean_rfid
            else:
                student.rfid_uid = None

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def deactivate(db: Session, student_id: int) -> StudentModel:
        student = StudentService.get_by_id(db, student_id)
        student.is_active = False
        if student.user:
            student.user.is_active = False
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def enroll_face(
        db: Session,
        student_id: int,
        file_bytes: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes single-person face enrollment image:
        - Validates that exactly one face is visible.
        - Rejects photos with multiple faces.
        - Generates 512-d ArcFace embedding.
        - Persists embedding and sets face_enrolled = True.
        """
        student = StudentService.get_by_id(db, student_id)

        # 1. Decode image
        validate_image_security(filename or "face.jpg", "image/jpeg", len(file_bytes))
        img = decode_image_bytes(file_bytes)

        # 2. Detect face and keypoints using SCRFD-10G
        detector = SCRFD10GFaceDetector.get_instance()
        detections = detector.detect_faces_with_landmarks(img, conf_threshold=0.50)

        if len(detections) == 0:
            raise FaceBiometricError("No face detected in enrollment image. Please ensure good lighting and face camera directly.")

        if len(detections) > 1:
            raise FaceBiometricError(f"Multiple faces ({len(detections)}) detected. Enrollment photograph must contain exactly one face.")

        det = detections[0]
        bbox = det["bbox"]
        landmarks = det.get("landmarks")

        # 3. Align face to 112x112 ArcFace template
        aligned_crop = crop_and_align_face(img, bbox, landmarks=landmarks)

        # 4. Generate 512-D L2-normalized embedding
        embedder = ArcFaceMobileFaceNetEmbedder()
        emb_vector = embedder.generate_embedding(aligned_crop)

        # 5. Save photo to storage
        storage = get_storage_service()
        saved_img = storage.save_student_image(student.id, file_bytes, filename)

        # 6. Save face embedding record
        embedding_rec = FaceEmbeddingModel(
            student_id=student.id,
            embedding_list=emb_vector,
            image_reference=saved_img["url"],
            quality_score=float(det.get("conf", 1.0))
        )
        db.add(embedding_rec)
        student.face_enrolled = True
        db.commit()

        warnings = []
        if det.get("conf", 1.0) < 0.65:
            warnings.append("Low face detection confidence. Ensure room is well-lit for optimal recognition.")

        return {
            "student_id": student.id,
            "images_processed": 1,
            "faces_detected": 1,
            "successful_embeddings": 1,
            "status": "success",
            "quality_warnings": warnings
        }

