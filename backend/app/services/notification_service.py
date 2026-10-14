from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.repositories.notification_repo import NotificationRepository
from app.core.config import settings
from app.core.logging_config import logger
from app.services.websocket_manager import ws_manager
import asyncio


class EmailProviderBase:
    def send(self, recipient: str, subject: str, body: str) -> bool:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProviderBase):
    def send(self, recipient: str, subject: str, body: str) -> bool:
        logger.info(f"[NOTIFICATION-DISPATCH] To: {recipient} | Subject: {subject} | Body: {body}")
        return True


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
        self.email_provider = ConsoleEmailProvider()

    def send_notification(
        self,
        notif_type: str,
        title: str,
        message: str,
        recipient_role: str = "SUPERVISOR",
        recipient_user_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Creates, persists, logs, and broadcasts operational notifications.
        """
        notif = Notification(
            type=notif_type,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            title=title,
            message=message,
            data=data or {},
            read=False,
            created_at=datetime.now(timezone.utc)
        )
        saved = self.repo.create(notif)

        # Dispatch via simulated email provider
        self.email_provider.send(
            recipient=f"role-{recipient_role.lower()}@security-ops.local",
            subject=f"[{notif_type}] {title}",
            body=message
        )

        # Broadcast via WebSocket for instant live UI popups
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast("notification", saved.to_dict()))
        except Exception as e:
            logger.warning(f"WebSocket broadcast skipped in non-async worker: {e}")

        return saved

    def list_notifications(
        self,
        role: Optional[str] = None,
        user_id: Optional[int] = None,
        unread_only: bool = False
    ) -> List[Notification]:
        return self.repo.list_notifications(role=role, user_id=user_id, unread_only=unread_only)

    def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        notif = self.repo.get_by_id(notification_id)
        if notif:
            return self.repo.mark_as_read(notif)
        return None
