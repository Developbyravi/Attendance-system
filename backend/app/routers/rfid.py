import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.student import StudentModel
from app.schemas.rfid import (
    StartAssignmentRequest,
    AssignmentSessionResponse,
    ConfirmAssignmentRequest,
    DeactivateCardRequest,
    DeviceRfidScanPayload
)
from sqlalchemy.exc import IntegrityError
from app.services.rfid_assignment_manager import get_rfid_assignment_manager
from app.services.supabase_service import get_supabase_service
from app.core.security import get_current_admin, verify_device_authenticated, verify_device_or_teacher, get_current_user

router = APIRouter(prefix="/api/rfid", tags=["RFID Hardware & Card Assignment"])

@router.post(
    "/assignment/start",
    response_model=AssignmentSessionResponse,
    summary="Initiate RFID Card Assignment Mode (Admin Only)"
)
def start_card_assignment(
    req: StartAssignmentRequest,
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Authorized Administrator selects a registered student and initiates card assignment mode.
    Sets up a pending scan session on the target hardware reader gateway.
    """
    student = db.query(StudentModel).filter(StudentModel.id == req.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{req.student_id}' not found."
        )

    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign card to inactive student '{student.name}'."
        )

    assignment_mgr = get_rfid_assignment_manager()
    session = assignment_mgr.start_session(
        student_id=student.id,
        student_name=student.name,
        roll_no=student.roll_no,
        department=student.department,
        division=student.division or "A",
        admin_id=str(current_admin["user_id"]),
        current_rfid_uid=student.rfid_uid,
        device_id=req.device_id or "GATE-READER-01",
        mode=req.mode or "ASSIGN",
        timeout_seconds=req.timeout_seconds or 60
    )

    return session.to_dict()

@router.get(
    "/assignment/session/{session_id}",
    response_model=AssignmentSessionResponse,
    summary="Poll Pending Assignment State (Admin Only)"
)
def get_assignment_session_status(
    session_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Polls the real-time status of an RFID assignment session (PENDING_SCAN, SCANNED, EXPIRED, CONFIRMED).
    """
    assignment_mgr = get_rfid_assignment_manager()
    session = assignment_mgr.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment session '{session_id}' not found."
        )

    return session.to_dict()

@router.post(
    "/assignment/cancel",
    summary="Cancel Pending Card Assignment Session (Admin Only)"
)
def cancel_assignment_session(
    payload: Dict[str, str],
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Cancels an ongoing card assignment session before card tap.
    """
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    assignment_mgr = get_rfid_assignment_manager()
    session = assignment_mgr.cancel_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Assignment session not found.")

    return {"status": "cancelled", "session_id": session_id}

@router.post(
    "/assignment/confirm",
    summary="Confirm Real Scanned UID Association (Admin Only)"
)
def confirm_card_assignment(
    req: ConfirmAssignmentRequest,
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Admin confirms the scanned physical card UID and binds it to the student.
    Enforces UID uniqueness at database level and rejects already-assigned cards.
    Emits an audit log.
    """
    assignment_mgr = get_rfid_assignment_manager()
    session = assignment_mgr.get_session(req.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment session not found or expired."
        )

    if session.status != "SCANNED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm assignment session with status '{session.status}'. Must be 'SCANNED'."
        )

    normalized_uid = req.rfid_uid.strip().upper()
    if session.scanned_uid and normalized_uid != session.scanned_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submitted UID '{normalized_uid}' does not match real reader scan '{session.scanned_uid}'."
        )

    student = db.query(StudentModel).filter(StudentModel.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    # Enforce UID Uniqueness: reject if card is assigned to another active student
    conflict_student = db.query(StudentModel).filter(
        (StudentModel.rfid_uid == normalized_uid) | (StudentModel.rfid_uid == req.rfid_uid.strip()),
        StudentModel.id != student.id,
        StudentModel.is_active == True
    ).first()

    if conflict_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"RFID Card UID '{normalized_uid}' is already assigned to active student '{conflict_student.name}' (Roll: {conflict_student.roll_no}, Division: {conflict_student.division}). Duplicate card assignment is forbidden."
        )

    old_rfid = student.rfid_uid
    is_replacement = bool(old_rfid and not old_rfid.startswith("PENDING") and not old_rfid.startswith("DEACTIVATED"))

    # Update database with integrity check
    try:
        student.rfid_uid = normalized_uid
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database constraint violation: RFID Card UID '{normalized_uid}' is already registered to another student."
        )

    # Mark session confirmed
    session.status = "CONFIRMED"

    # Emit audit log event
    action = "REPLACE_RFID_CARD" if is_replacement else "ASSIGN_RFID_CARD"
    supabase_service = get_supabase_service()
    supabase_service.sync_rfid_uid(student.id, normalized_uid)
    supabase_service.log_audit_event(
        user_id=str(current_admin["user_id"]),
        role="ADMIN",
        action=action,
        entity_type="STUDENT",
        entity_id=str(student.id),
        details={
            "student_id": student.id,
            "roll_no": student.roll_no,
            "student_name": student.name,
            "old_rfid_uid": old_rfid,
            "new_rfid_uid": normalized_uid,
            "action_type": action,
            "reason": req.reason or ("Card replacement" if is_replacement else "Initial card issuance"),
            "session_id": req.session_id,
            "reader_device": session.device_id
        },
        db_session=db
    )

    return {
        "status": "success",
        "action": action,
        "student_id": student.id,
        "roll_no": student.roll_no,
        "student_name": student.name,
        "rfid_uid": normalized_uid,
        "previous_rfid_uid": old_rfid,
        "session_id": req.session_id
    }

@router.post(
    "/deactivate",
    summary="Deactivate Assigned RFID Card (Admin Only)"
)
def deactivate_card(
    req: DeactivateCardRequest,
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Deactivates or unbinds an RFID card from an active student account.
    Logs an authorized audit event.
    """
    student = db.query(StudentModel).filter(StudentModel.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if not student.rfid_uid or student.rfid_uid.startswith("DEACTIVATED") or student.rfid_uid.startswith("PENDING"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student does not have an active assigned RFID card to deactivate."
        )

    deactivated_uid = student.rfid_uid
    student.rfid_uid = f"DEACTIVATED-{uuid.uuid4().hex[:6].upper()}"
    db.commit()
    db.refresh(student)

    # Emit audit log event
    supabase_service = get_supabase_service()
    supabase_service.sync_rfid_uid(student.id, student.rfid_uid)
    supabase_service.log_audit_event(
        user_id=str(current_admin["user_id"]),
        role="ADMIN",
        action="DEACTIVATE_RFID_CARD",
        entity_type="STUDENT",
        entity_id=str(student.id),
        details={
            "student_id": student.id,
            "roll_no": student.roll_no,
            "deactivated_uid": deactivated_uid,
            "reason": req.reason or "Card reported lost/decommissioned by Administrator"
        },
        db_session=db
    )

    return {
        "status": "success",
        "action": "DEACTIVATE_RFID_CARD",
        "student_id": student.id,
        "roll_no": student.roll_no,
        "deactivated_rfid_uid": deactivated_uid
    }

@router.post(
    "/scan",
    summary="Ingest Physical RFID Card Tap from ESP8266 RC522 Reader"
)
def ingest_device_rfid_scan(
    payload: DeviceRfidScanPayload,
    auth_device: Dict[str, Any] = Depends(verify_device_authenticated),
    db: Session = Depends(get_db)
):
    """
    Endpoint called by ESP8266 / NodeMCU + RC522 reader over Wi-Fi.
    If an admin card assignment session is actively PENDING_SCAN on this device,
    captures the UID into the assignment session WITHOUT marking daily attendance.
    Otherwise, informs reader or forwards to daily attendance.
    """
    normalized_uid = payload.rfid_uid.strip().upper()
    device_id = payload.device_id or "GATE-READER-01"

    assignment_mgr = get_rfid_assignment_manager()
    captured_session = assignment_mgr.record_scan(normalized_uid, device_id)

    if captured_session:
        return {
            "status": "assignment_captured",
            "mode": "assignment",
            "rfid_uid": normalized_uid,
            "session_id": captured_session.session_id,
            "student_name": captured_session.student_name,
            "roll_no": captured_session.roll_no,
            "message": f"Card {normalized_uid} captured for student {captured_session.student_name}. Awaiting admin confirmation."
        }

    # If explicit assignment mode requested but no session found
    if payload.mode == "assignment":
        raise HTTPException(
            status_code=404,
            detail="No card assignment mode is actively pending on this reader. Initiate assignment from Admin Portal first."
        )

    # Default attendance check-in path
    student = db.query(StudentModel).filter(
        (StudentModel.rfid_uid == normalized_uid) | (StudentModel.rfid_uid == payload.rfid_uid)
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Card UID '{normalized_uid}' is not registered. Please register at Campus Administration."
        )

    return {
        "status": "recognized",
        "mode": "attendance",
        "student_name": student.name,
        "roll_number": student.roll_no,
        "rfid_uid": normalized_uid
    }
