from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.notification_service import NotificationService
from app.api.deps import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=StandardResponse[List[NotificationResponse]])
def get_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    # Filter based on role or user
    role = None if current_user.role == "ADMIN" else current_user.role
    user_id = current_user.id if current_user.role == "GUARD" else None

    notifs = service.list_notifications(role=role, user_id=user_id, unread_only=unread_only)
    return success_response([n.to_dict() for n in notifs])


@router.post("/send", response_model=StandardResponse[NotificationResponse], status_code=status.HTTP_201_CREATED)
def send_notification(
    payload: NotificationCreate,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    notif = service.send_notification(
        notif_type=payload.type,
        title=payload.title,
        message=payload.message,
        recipient_role=payload.recipient_role,
        recipient_user_id=payload.recipient_user_id,
        data=payload.data
    )
    return success_response(notif.to_dict())


@router.put("/{notification_id}/read", response_model=StandardResponse[NotificationResponse])
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    updated = service.mark_as_read(notification_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found", "details": {}}
        )
    return success_response(updated.to_dict())
