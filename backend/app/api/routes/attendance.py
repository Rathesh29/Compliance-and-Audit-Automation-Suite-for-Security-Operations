from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.attendance import (
    CheckInRequest,
    CheckOutRequest,
    AttendanceLogResponse,
    AttendanceStatusResponse
)
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.attendance_service import AttendanceService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=StandardResponse[dict])
def check_in(
    payload: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AttendanceService(db)
    try:
        log, assignment, violations = service.process_check_in(
            guard=current_user,
            assignment_id=payload.assignment_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            qr_token=payload.qr_token
        )
        return success_response({
            "log": log.to_dict(),
            "assignment": assignment.to_dict(),
            "violations": violations
        })
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHECKIN_FAILED", "message": str(e), "details": {}}
        )


@router.post("/check-out", response_model=StandardResponse[dict])
def check_out(
    payload: CheckOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AttendanceService(db)
    try:
        log, assignment, violations = service.process_check_out(
            guard=current_user,
            assignment_id=payload.assignment_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            qr_token=payload.qr_token
        )
        return success_response({
            "log": log.to_dict(),
            "assignment": assignment.to_dict(),
            "violations": violations
        })
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHECKOUT_FAILED", "message": str(e), "details": {}}
        )


@router.get("/status", response_model=StandardResponse[List[AttendanceStatusResponse]])
def get_attendance_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AttendanceService(db)
    statuses = service.get_guard_attendance_status(current_user.id)
    return success_response(statuses)


@router.get("/logs/{assignment_id}", response_model=StandardResponse[List[AttendanceLogResponse]])
def get_assignment_attendance_logs(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AttendanceService(db)
    asg = service.asg_repo.get_by_id(assignment_id)
    if not asg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found", "details": {}}
        )

    if current_user.role == "GUARD" and asg.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Guards may only inspect their own attendance history", "details": {}}
        )

    logs = service.att_repo.list_by_assignment(assignment_id)
    return success_response([l.to_dict() for l in logs])
