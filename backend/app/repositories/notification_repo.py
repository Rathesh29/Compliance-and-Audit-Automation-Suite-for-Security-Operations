from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_notifications(
        self,
        role: Optional[str] = None,
        user_id: Optional[int] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        query = self.db.query(Notification)
        if role:
            query = query.filter((Notification.recipient_role == role) | (Notification.recipient_role == "ALL"))
        if user_id:
            query = query.filter((Notification.recipient_user_id == user_id) | (Notification.recipient_user_id.is_(None)))
        if unread_only:
            query = query.filter(Notification.read == False)
        return query.order_by(Notification.id.desc()).limit(limit).all()

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification
