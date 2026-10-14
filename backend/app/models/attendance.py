from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.enums import AttendanceType


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # CHECK_IN or CHECK_OUT
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    qr_token = Column(String(255), nullable=True)
    is_valid = Column(Boolean, default=True, nullable=False)
    violation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment = relationship("Assignment", back_populates="attendance_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "qr_token": self.qr_token,
            "is_valid": self.is_valid,
            "violation_reason": self.violation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
