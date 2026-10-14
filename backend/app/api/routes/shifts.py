from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.shift_service import ShiftService
from app.api.deps import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.get("", response_model=StandardResponse[List[ShiftResponse]])
def list_shifts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ShiftService(db)
    shifts = service.list_shifts()
    return success_response([s.to_dict() for s in shifts])


@router.post("", response_model=StandardResponse[ShiftResponse], status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    service = ShiftService(db)
    shift = service.create_shift(payload, performed_by=current_user.email)
    return success_response(shift.to_dict())


@router.get("/{shift_id}", response_model=StandardResponse[ShiftResponse])
def get_shift(
    shift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ShiftService(db)
    shift = service.get_shift(shift_id)
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIFT_NOT_FOUND", "message": f"Shift #{shift_id} not found", "details": {}}
        )
    return success_response(shift.to_dict())


@router.put("/{shift_id}", response_model=StandardResponse[ShiftResponse])
def update_shift(
    shift_id: int,
    payload: ShiftUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    service = ShiftService(db)
    try:
        shift = service.update_shift(shift_id, payload, performed_by=current_user.email)
        return success_response(shift.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SHIFT_UPDATE_FAILED", "message": str(e), "details": {}}
        )
