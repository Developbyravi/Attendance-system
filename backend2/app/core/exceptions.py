from typing import Any, Optional
from fastapi import HTTPException, status

class SmartAttendException(HTTPException):
    """Base HTTP exception for SmartAttend backend."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
        error_code: Optional[str] = None,
        data: Optional[Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code or "ERROR"
        self.data = data

class EntityNotFoundError(SmartAttendException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with identifier '{identifier}' was not found.",
            error_code="NOT_FOUND"
        )

class DuplicateEntityError(SmartAttendException):
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity_name} with {field} '{value}' already exists.",
            error_code="CONFLICT"
        )

class AuthenticationError(SmartAttendException):
    def __init__(self, detail: str = "Invalid credentials or session expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )

class AuthorizationError(SmartAttendException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )

class SessionFinalizedError(SmartAttendException):
    def __init__(self, session_id: Any):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lecture session #{session_id} is FINALIZED and immutable.",
            error_code="SESSION_FINALIZED"
        )

class FaceBiometricError(SmartAttendException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="BIOMETRIC_ERROR"
        )

