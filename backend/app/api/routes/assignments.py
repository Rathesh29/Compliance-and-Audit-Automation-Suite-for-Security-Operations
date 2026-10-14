from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentValidateRequest
)
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.assignment_service import AssignmentService
from app.api.deps import get_current_user, require_roles
from app.models.user import User
from app.models.enums import AssignmentStatus

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("", response_model=StandardResponse[List[AssignmentResponse]])
def list_assignments(
    site_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_val: Optional[date] = Query(None, alias="date"),
    status_val: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Rule 15: Guards can only access their own assignments
    effective_user_id = user_id
    if current_user.role == "GUARD":
        effective_user_id = current_user.id

    service = AssignmentService(db)
    assignments = service.list_assignments(
        site_id=site_id,
        user_id=effective_user_id,
        assignment_date=date_val,
        status=status_val
    )
    return success_response([a.to_dict() for a in assignments])


@router.post("/validate", response_model=StandardResponse[dict])
def validate_proposed_assignment(
    payload: AssignmentValidateRequest,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    service = AssignmentService(db)
    try:
        check_result = service.validate_proposed_assignment(
            user_id=payload.user_id,
            site_id=payload.site_id,
            shift_id=payload.shift_id,
            assignment_date=payload.date
        )
        return success_response(check_result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_FAILED", "message": str(e), "details": {}}
        )


@router.post("", response_model=StandardResponse[AssignmentResponse], status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    service = AssignmentService(db)
    try:
        assignment, violation_info = service.create_assignment(payload, performed_by=current_user.email)
        if not assignment and violation_info:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "COMPLIANCE_VIOLATION",
                    "message": violation_info.get("message", "Assignment violates compliance rules"),
                    "details": violation_info
                }
            )
        return success_response(assignment.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ASSIGNMENT_CREATION_FAILED", "message": str(e), "details": {}}
        )


@router.get("/{assignment_id}", response_model=StandardResponse[AssignmentResponse])
def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AssignmentService(db)
    assignment = service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": f"Assignment #{assignment_id} not found", "details": {}}
        )

    # Rule 15: Guards can only access their own assignments
    if current_user.role == "GUARD" and assignment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access restricted to your own assignments", "details": {}}
        )

    return success_response(assignment.to_dict())


@router.put("/{assignment_id}/status", response_model=StandardResponse[AssignmentResponse])
def update_assignment_status(
    assignment_id: int,
    new_status: AssignmentStatus,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    service = AssignmentService(db)
    try:
        updated = service.update_assignment_status(assignment_id, new_status, performed_by=current_user.email)
        return success_response(updated.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "STATUS_UPDATE_FAILED", "message": str(e), "details": {}}
        )
