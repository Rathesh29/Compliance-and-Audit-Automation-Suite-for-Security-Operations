from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.database.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    performed_by = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    extra_metadata = Column("metadata", JSON, default=dict)
    previous_hash = Column(String(64), nullable=False)
    record_hash = Column(String(64), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "performed_by": self.performed_by,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.extra_metadata or {},
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash
        }
