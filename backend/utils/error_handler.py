"""Centralized error handling for the application."""

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any

class AlarmBlockError(HTTPException):
    """Base exception class for AlarmBlock application."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.extra = extra or {}

class ValidationError(AlarmBlockError):
    """Raised when input validation fails."""
    def __init__(self, message: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            extra=extra
        )

class HardwareError(AlarmBlockError):
    """Raised when hardware operations fail."""
    def __init__(self, message: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            extra=extra
        )

async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Validation Error",
            "message": exc.detail,
            "extra": exc.extra
        }
    )

async def handle_hardware_error(request: Request, exc: HardwareError) -> JSONResponse:
    """Handle HardwareError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Hardware Error",
            "message": exc.detail,
            "extra": exc.extra
        }
    )
