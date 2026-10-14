from datetime import timedelta, timezone, datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_mfa_secret,
    get_totp_uri,
    verify_totp
)
from app.utils.qr import generate_qr_code_base64
from app.core.config import settings
from app.core.logging_config import logger
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
        self.audit = AuditService(db)

    def authenticate_user(self, email: str, password: str, client_ip: str = "unknown") -> Tuple[Optional[User], Optional[str]]:
        """
        Validates email & password. Logs audit events for both success and failure.
        """
        user = self.repo.get_by_email(email)
        if not user:
            logger.warning(f"Failed login attempt for non-existent email: {email}")
            self.audit.log_event(
                entity_type="AUTH",
                entity_id="0",
                action="LOGIN_FAILED",
                performed_by=email,
                metadata={"reason": "User not found", "ip_address": client_ip}
            )
            return None, "Invalid email or password"

        if user.status != "ACTIVE":
            logger.warning(f"Login rejected for inactive user: {email} ({user.status})")
            self.audit.log_event(
                entity_type="AUTH",
                entity_id=str(user.id),
                action="LOGIN_BLOCKED",
                performed_by=email,
                metadata={"reason": f"Account status is {user.status}", "ip_address": client_ip}
            )
            return None, "User account is inactive or suspended"

        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {email}")
            self.audit.log_event(
                entity_type="AUTH",
                entity_id=str(user.id),
                action="LOGIN_FAILED",
                performed_by=email,
                metadata={"reason": "Password mismatch", "ip_address": client_ip}
            )
            return None, "Invalid email or password"

        # Audit login
        self.audit.log_event(
            entity_type="AUTH",
            entity_id=str(user.id),
            action="LOGIN_SUCCESS",
            performed_by=email,
            metadata={"role": user.role, "ip_address": client_ip}
        )
        return user, None

    def issue_token_for_user(self, user: User) -> str:
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
        return create_access_token(payload)

    def verify_mfa_login(self, user_id: int, code: str, client_ip: str = "unknown") -> Tuple[Optional[str], Optional[str]]:
        user = self.repo.get_by_id(user_id)
        if not user:
            return None, "User not found"

        if not user.mfa_secret or not verify_totp(user.mfa_secret, code):
            self.audit.log_event(
                entity_type="AUTH",
                entity_id=str(user.id),
                action="MFA_FAILED",
                performed_by=user.email,
                metadata={"ip_address": client_ip}
            )
            return None, "Invalid MFA / TOTP verification code"

        self.audit.log_event(
            entity_type="AUTH",
            entity_id=str(user.id),
            action="MFA_VERIFIED",
            performed_by=user.email,
            metadata={"ip_address": client_ip}
        )
        token = self.issue_token_for_user(user)
        return token, None

    def setup_mfa(self, user: User) -> Dict[str, str]:
        secret = generate_mfa_secret()
        user.mfa_secret = secret
        user.mfa_enabled = True
        self.repo.update(user)

        otp_uri = get_totp_uri(secret, user.email)
        qr_code_b64 = generate_qr_code_base64(otp_uri)

        self.audit.log_event(
            entity_type="USER",
            entity_id=str(user.id),
            action="MFA_ENABLED",
            performed_by=user.email,
            metadata={"mfa_enabled": True}
        )

        return {
            "secret": secret,
            "otpauth_url": otp_uri,
            "qr_code_base64": qr_code_b64
        }
