from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.enums import AssignmentStatus


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(50), default=AssignmentStatus.SCHEDULED.value, nullable=False)
    compliance_violations = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="assignments")
    site = relationship("Site", back_populates="assignments")
    shift = relationship("Shift", back_populates="assignments")
    attendance_logs = relationship("AttendanceLog", back_populates="assignment", cascade="all, delete-orphan", order_by="AttendanceLog.timestamp")
    compliance_exceptions = relationship("ComplianceException", back_populates="assignment", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "site_id": self.site_id,
            "shift_id": self.shift_id,
            "date": self.date.isoformat() if isinstance(self.date, (date, datetime)) else str(self.date),
            "status": self.status,
            "compliance_violations": self.compliance_violations or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_name": self.user.name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "site_name": self.site.name if self.site else None,
            "shift_name": self.shift.name if self.shift else None,
            "shift_start": self.shift.start_time if self.shift else None,
            "shift_end": self.shift.end_time if self.shift else None,
        }
