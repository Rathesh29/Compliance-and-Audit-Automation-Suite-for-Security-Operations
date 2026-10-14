from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.shift import Shift
from app.schemas.shift import ShiftCreate, ShiftUpdate
from app.repositories.shift_repo import ShiftRepository
from app.services.audit_service import AuditService


class ShiftService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShiftRepository(db)
        self.audit = AuditService(db)

    def get_shift(self, shift_id: int) -> Optional[Shift]:
        return self.repo.get_by_id(shift_id)

    def list_shifts(self) -> List[Shift]:
        return self.repo.list_shifts()

    def create_shift(self, payload: ShiftCreate, performed_by: str) -> Shift:
        shift = Shift(
            name=payload.name,
            start_time=payload.start_time,
            end_time=payload.end_time,
            grace_period_minutes=payload.grace_period_minutes
        )
        saved = self.repo.create(shift)

        self.audit.log_event(
            entity_type="SHIFT",
            entity_id=str(saved.id),
            action="SHIFT_CREATED",
            performed_by=performed_by,
            metadata={
                "name": saved.name,
                "start_time": saved.start_time,
                "end_time": saved.end_time,
                "is_overnight": saved.is_overnight,
                "duration_hours": saved.duration_hours
            }
        )
        return saved

    def update_shift(self, shift_id: int, payload: ShiftUpdate, performed_by: str) -> Shift:
        shift = self.repo.get_by_id(shift_id)
        if not shift:
            raise ValueError("Shift not found")

        if payload.name is not None:
            shift.name = payload.name
        if payload.start_time is not None:
            shift.start_time = payload.start_time
        if payload.end_time is not None:
            shift.end_time = payload.end_time
        if payload.grace_period_minutes is not None:
            shift.grace_period_minutes = payload.grace_period_minutes

        updated = self.repo.update(shift)

        self.audit.log_event(
            entity_type="SHIFT",
            entity_id=str(updated.id),
            action="SHIFT_UPDATED",
            performed_by=performed_by,
            metadata={"name": updated.name}
        )
        return updated
