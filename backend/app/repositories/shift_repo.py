from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.shift import Shift


class ShiftRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, shift_id: int) -> Optional[Shift]:
        return self.db.query(Shift).filter(Shift.id == shift_id).first()

    def list_shifts(self) -> List[Shift]:
        return self.db.query(Shift).order_by(Shift.start_time.asc()).all()

    def create(self, shift: Shift) -> Shift:
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def update(self, shift: Shift) -> Shift:
        self.db.commit()
        self.db.refresh(shift)
        return shift
