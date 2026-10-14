from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=150.0, nullable=False)
    qr_token = Column(String(255), unique=True, index=True, nullable=False)
    compliance_rules = Column(JSON, default=lambda: {
        "max_daily_hours": 12,
        "minimum_rest_hours": 8,
        "max_weekly_hours": 60,
        "allow_overtime": False,
        "require_qr": True,
        "require_gps": True,
        "late_threshold_minutes": 10
    })
    compliance_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = relationship("Assignment", back_populates="site", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="site", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_meters": self.radius_meters,
            "qr_token": self.qr_token,
            "compliance_rules": self.compliance_rules,
            "compliance_score": round(self.compliance_score, 1) if self.compliance_score is not None else 100.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
