from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.database.session import Base
from app.models.enums import NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    recipient_role = Column(String(50), default="SUPERVISOR", nullable=False)
    recipient_user_id = Column(Integer, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    data = Column(JSON, default=dict)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "recipient_role": self.recipient_role,
            "recipient_user_id": self.recipient_user_id,
            "title": self.title,
            "message": self.message,
            "data": self.data or {},
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
