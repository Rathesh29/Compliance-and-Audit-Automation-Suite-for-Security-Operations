from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field
from app.models.enums import AssignmentStatus
from app.schemas.compliance import ComplianceViolationItem


class AssignmentCreate(BaseModel):
    user_id: int
    site_id: int
    shift_id: int
    date: date
    override_violations: bool = False
    override_reason: Optional[str] = None


class AssignmentUpdate(BaseModel):
    site_id: Optional[int] = None
    shift_id: Optional[int] = None
    date: Optional[date] = None
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(BaseModel):
    id: int
    user_id: int
    site_id: int
    shift_id: int
    date: str
    status: str
    compliance_violations: List[Dict[str, Any]] = []
    created_at: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    site_name: Optional[str] = None
    shift_name: Optional[str] = None
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None

    class Config:
        from_attributes = True


class AssignmentValidateRequest(BaseModel):
    user_id: int
    site_id: int
    shift_id: int
    date: date
