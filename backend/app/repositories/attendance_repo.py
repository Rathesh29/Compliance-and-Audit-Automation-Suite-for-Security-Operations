from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.attendance import AttendanceLog
from app.models.enums import AttendanceType


class AttendanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, log_id: int) -> Optional[AttendanceLog]:
        return self.db.query(AttendanceLog).filter(AttendanceLog.id == log_id).first()

    def get_by_assignment_and_type(self, assignment_id: int, log_type: str) -> Optional[AttendanceLog]:
        return self.db.query(AttendanceLog).filter(
            AttendanceLog.assignment_id == assignment_id,
            AttendanceLog.type == log_type
        ).order_by(AttendanceLog.id.desc()).first()

    def list_by_assignment(self, assignment_id: int) -> List[AttendanceLog]:
        return self.db.query(AttendanceLog).filter(
            AttendanceLog.assignment_id == assignment_id
        ).order_by(AttendanceLog.timestamp.asc()).all()

    def create(self, log: AttendanceLog) -> AttendanceLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
