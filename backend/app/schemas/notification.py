from typing import Optional, Dict, Any
from pydantic import BaseModel


class NotificationCreate(BaseModel):
    type: str
    recipient_role: str = "SUPERVISOR"
    recipient_user_id: Optional[int] = None
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: int
    type: str
    recipient_role: str
    recipient_user_id: Optional[int] = None
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
