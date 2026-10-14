from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=2)
    start_time: str = Field(..., description="Format HH:MM")
    end_time: str = Field(..., description="Format HH:MM")
    grace_period_minutes: int = 15

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Time must be in 24-hour HH:MM format, e.g. 08:00, 22:00")
        return v


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    grace_period_minutes: Optional[int] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Time must be in 24-hour HH:MM format, e.g. 08:00, 22:00")
        return v


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: str
    end_time: str
    grace_period_minutes: int
    is_overnight: bool
    duration_hours: float
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
