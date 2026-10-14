from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest(self) -> Optional[AuditLog]:
        """Fetch the most recent audit log to link hash chain."""
        return self.db.query(AuditLog).order_by(AuditLog.id.desc()).first()

    def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        return self.db.query(AuditLog).filter(AuditLog.id == log_id).first()

    def append(self, log: AuditLog) -> AuditLog:
        """Append-only write to immutable audit log."""
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        performed_by: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        query = self.db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == str(entity_id))
        if action:
            query = query.filter(AuditLog.action == action)
        if performed_by:
            query = query.filter(AuditLog.performed_by.ilike(f"%{performed_by}%"))
        if start_time:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLog.timestamp <= end_time)

        return query.order_by(AuditLog.id.desc()).offset(offset).limit(limit).all()

    def get_all_ordered(self) -> List[AuditLog]:
        """Retrieve all audit logs strictly ordered by ascending ID for cryptographic chain verification."""
        return self.db.query(AuditLog).order_by(AuditLog.id.asc()).all()
