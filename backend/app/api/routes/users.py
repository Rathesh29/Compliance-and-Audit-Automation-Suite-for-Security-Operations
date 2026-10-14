from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.user_service import UserService
from app.api.deps import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=StandardResponse[List[UserResponse]])
def list_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    users = service.list_users(role=role, status=status, search=search)
    return success_response([u.to_dict() for u in users])


@router.post("", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    try:
        user = service.create_user(payload, performed_by=current_user.email)
        return success_response(user.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USER_CREATION_FAILED", "message": str(e), "details": {}}
        )


@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Rule 15: Guards can only access their own operational/profile information
    if current_user.role == "GUARD" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Guards are restricted to viewing their own profile only", "details": {}}
        )

    service = UserService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found", "details": {}}
        )
    return success_response(user.to_dict())


@router.put("/{user_id}", response_model=StandardResponse[UserResponse])
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    try:
        user = service.update_user(user_id, payload, performed_by=current_user.email)
        return success_response(user.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USER_UPDATE_FAILED", "message": str(e), "details": {}}
        )
