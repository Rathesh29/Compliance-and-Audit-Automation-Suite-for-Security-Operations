from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.enums import AssignmentStatus


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assignment_id: int) -> Optional[Assignment]:
        return self.db.query(Assignment).filter(Assignment.id == assignment_id).first()

    def get_by_guard_and_date(self, user_id: int, assignment_date: date) -> List[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.user_id == user_id,
            Assignment.date == assignment_date
        ).all()

    def list_assignments(
        self,
        site_id: Optional[int] = None,
        user_id: Optional[int] = None,
        assignment_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> List[Assignment]:
        query = self.db.query(Assignment)
        if site_id:
            query = query.filter(Assignment.site_id == site_id)
        if user_id:
            query = query.filter(Assignment.user_id == user_id)
        if assignment_date:
            query = query.filter(Assignment.date == assignment_date)
        if status:
            query = query.filter(Assignment.status == status)
        return query.order_by(Assignment.date.desc(), Assignment.id.desc()).all()

    def create(self, assignment: Assignment) -> Assignment:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def update(self, assignment: Assignment) -> Assignment:
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
