from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.enums import UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user_repo import UserRepository
from app.core.security import get_password_hash
from app.services.audit_service import AuditService


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
        self.audit = AuditService(db)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repo.get_by_id(user_id)

    def list_users(self, role: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[User]:
        return self.repo.list_users(role=role, status=status, search=search)

    def create_user(self, payload: UserCreate, performed_by: str) -> User:
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise ValueError(f"Email {payload.email} is already registered.")

        user = User(
            name=payload.name,
            email=payload.email.lower().strip(),
            password_hash=get_password_hash(payload.password),
            role=payload.role.value if hasattr(payload.role, "value") else str(payload.role),
            status=payload.status.value if hasattr(payload.status, "value") else str(payload.status),
            phone=payload.phone
        )
        saved = self.repo.create(user)

        self.audit.log_event(
            entity_type="USER",
            entity_id=str(saved.id),
            action="USER_CREATED",
            performed_by=performed_by,
            metadata={"name": saved.name, "email": saved.email, "role": saved.role}
        )
        return saved

    def update_user(self, user_id: int, payload: UserUpdate, performed_by: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        old_role = user.role
        old_status = user.status

        if payload.name is not None:
            user.name = payload.name
        if payload.email is not None:
            user.email = payload.email.lower().strip()
        if payload.password is not None and payload.password.strip():
            user.password_hash = get_password_hash(payload.password)
        if payload.role is not None:
            user.role = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
        if payload.status is not None:
            user.status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.mfa_enabled is not None:
            user.mfa_enabled = payload.mfa_enabled

        updated = self.repo.update(user)

        action = "USER_UPDATED"
        if old_status != updated.status and updated.status == UserStatus.INACTIVE.value:
            action = "USER_DISABLED"

        self.audit.log_event(
            entity_type="USER",
            entity_id=str(updated.id),
            action=action,
            performed_by=performed_by,
            metadata={
                "old_role": old_role,
                "new_role": updated.role,
                "old_status": old_status,
                "new_status": updated.status
            }
        )
        return updated
