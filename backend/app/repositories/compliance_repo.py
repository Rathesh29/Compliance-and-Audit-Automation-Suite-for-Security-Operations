from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.compliance import ComplianceException
from app.models.assignment import Assignment
from app.models.enums import ExceptionStatus


class ComplianceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, exception_id: int) -> Optional[ComplianceException]:
        return self.db.query(ComplianceException).filter(ComplianceException.id == exception_id).first()

    def create(self, exception: ComplianceException) -> ComplianceException:
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        return exception

    def update(self, exception: ComplianceException) -> ComplianceException:
        self.db.commit()
        self.db.refresh(exception)
        return exception

    def list_exceptions(
        self,
        site_id: Optional[int] = None,
        violation_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ComplianceException]:
        query = self.db.query(ComplianceException).join(Assignment, ComplianceException.assignment_id == Assignment.id)
        if site_id:
            query = query.filter(Assignment.site_id == site_id)
        if violation_type:
            query = query.filter(ComplianceException.violation_type == violation_type)
        if status:
            query = query.filter(ComplianceException.status == status)
        if severity:
            query = query.filter(ComplianceException.severity == severity)

        return query.order_by(ComplianceException.id.desc()).offset(offset).limit(limit).all()

    def count_open(self, site_id: Optional[int] = None) -> int:
        query = self.db.query(ComplianceException).filter(ComplianceException.status == ExceptionStatus.OPEN.value)
        if site_id:
            query = query.join(Assignment, ComplianceException.assignment_id == Assignment.id).filter(Assignment.site_id == site_id)
        return query.count()
