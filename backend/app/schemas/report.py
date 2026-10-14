from typing import Optional, Dict, Any
from datetime import date
from pydantic import BaseModel
from app.models.enums import ReportType


class ReportGenerateRequest(BaseModel):
    site_id: Optional[int] = None
    date_range_start: date
    date_range_end: date
    report_type: ReportType = ReportType.COMPLIANCE


class ReportResponse(BaseModel):
    id: int
    site_id: Optional[int] = None
    site_name: str
    date_range_start: str
    date_range_end: str
    generated_by: str
    report_type: str
    data: Dict[str, Any]
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
