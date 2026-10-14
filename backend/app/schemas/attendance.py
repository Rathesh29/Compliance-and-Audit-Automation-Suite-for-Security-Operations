from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    assignment_id: int
    latitude: float
    longitude: float
    qr_token: str


class CheckOutRequest(BaseModel):
    assignment_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    qr_token: Optional[str] = None


class AttendanceLogResponse(BaseModel):
    id: int
    assignment_id: int
    type: str
    timestamp: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    qr_token: Optional[str] = None
    is_valid: bool
    violation_reason: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceStatusResponse(BaseModel):
    assignment_id: int
    status: str
    site_name: str
    shift_name: str
    date: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    duration_hours: Optional[float] = None
    violations: List[str] = []
