from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SiteComplianceRules(BaseModel):
    max_daily_hours: float = 12.0
    minimum_rest_hours: float = 8.0
    max_weekly_hours: float = 60.0
    allow_overtime: bool = False
    require_qr: bool = True
    require_gps: bool = True
    late_threshold_minutes: int = 10


class SiteCreate(BaseModel):
    name: str = Field(..., min_length=2)
    location_name: str
    latitude: float
    longitude: float
    radius_meters: float = 150.0
    compliance_rules: Optional[Dict[str, Any]] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[float] = None
    compliance_rules: Optional[Dict[str, Any]] = None


class SiteResponse(BaseModel):
    id: int
    name: str
    location_name: str
    latitude: float
    longitude: float
    radius_meters: float
    qr_token: str
    compliance_rules: Dict[str, Any]
    compliance_score: float
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SiteQRResponse(BaseModel):
    site_id: int
    site_name: str
    qr_token: str
    qr_code_base64: str
