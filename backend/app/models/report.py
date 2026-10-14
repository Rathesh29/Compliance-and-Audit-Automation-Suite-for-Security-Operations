from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.enums import ReportType


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True, index=True)
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)
    generated_by = Column(String(255), nullable=False)
    report_type = Column(String(50), default=ReportType.COMPLIANCE.value, nullable=False)
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    site = relationship("Site", back_populates="reports")

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "site_name": self.site.name if self.site else "All Sites",
            "date_range_start": self.date_range_start.isoformat() if isinstance(self.date_range_start, (date, datetime)) else str(self.date_range_start),
            "date_range_end": self.date_range_end.isoformat() if isinstance(self.date_range_end, (date, datetime)) else str(self.date_range_end),
            "generated_by": self.generated_by,
            "report_type": self.report_type,
            "data": self.data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
