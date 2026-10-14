from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_time = Column(String(10), nullable=False)  # Format: "HH:MM", e.g. "08:00", "22:00"
    end_time = Column(String(10), nullable=False)    # Format: "HH:MM", e.g. "16:00", "06:00" (overnight)
    grace_period_minutes = Column(Integer, default=15, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = relationship("Assignment", back_populates="shift", cascade="all, delete-orphan")

    @property
    def is_overnight(self) -> bool:
        start_h, start_m = map(int, self.start_time.split(":"))
        end_h, end_m = map(int, self.end_time.split(":"))
        return (end_h * 60 + end_m) <= (start_h * 60 + start_m)

    @property
    def duration_hours(self) -> float:
        start_h, start_m = map(int, self.start_time.split(":"))
        end_h, end_m = map(int, self.end_time.split(":"))
        start_mins = start_h * 60 + start_m
        end_mins = end_h * 60 + end_m
        if end_mins <= start_mins:
            end_mins += 24 * 60
        return (end_mins - start_mins) / 60.0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "grace_period_minutes": self.grace_period_minutes,
            "is_overnight": self.is_overnight,
            "duration_hours": self.duration_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
