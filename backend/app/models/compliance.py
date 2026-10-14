from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.enums import ExceptionStatus, ViolationSeverity


class ComplianceException(Base):
    __tablename__ = "compliance_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    violation_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), default=ViolationSeverity.MEDIUM.value, nullable=False)
    status = Column(String(50), default=ExceptionStatus.OPEN.value, nullable=False, index=True)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="compliance_exceptions")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "status": self.status,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "site_name": self.assignment.site.name if self.assignment and self.assignment.site else None,
            "guard_name": self.assignment.user.name if self.assignment and self.assignment.user else None,
            "guard_email": self.assignment.user.email if self.assignment and self.assignment.user else None,
            "shift_name": self.assignment.shift.name if self.assignment and self.assignment.shift else None,
            "date": str(self.assignment.date) if self.assignment else None,
        }
