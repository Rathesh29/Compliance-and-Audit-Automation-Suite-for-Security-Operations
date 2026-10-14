from typing import List, Optional
from pydantic import BaseModel
from app.models.enums import ViolationType, ViolationSeverity, ExceptionStatus


class ComplianceViolationItem(BaseModel):
    type: str
    severity: str = "MEDIUM"
    message: str


class ComplianceCheckResult(BaseModel):
    compliant: bool
    violations: List[ComplianceViolationItem] = []


class ExceptionResolveRequest(BaseModel):
    resolution_notes: str


class ComplianceExceptionResponse(BaseModel):
    id: int
    assignment_id: int
    violation_type: str
    severity: str
    status: str
    detected_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    site_name: Optional[str] = None
    guard_name: Optional[str] = None
    guard_email: Optional[str] = None
    shift_name: Optional[str] = None
    date: Optional[str] = None

    class Config:
        from_attributes = True
