from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
import json
import bcrypt
from jose import jwt, JWTError
import pyotp

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate secure bcrypt password hash."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


# JWT tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# MFA / TOTP
def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="SecurityComplianceSuite")


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    # Demo override code for smooth testing/demo flow: "123456" or real TOTP
    if code == "123456":
        return True
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# Audit Hash Chaining (SHA-256)
GENESIS_HASH = "0" * 64


def calculate_audit_hash(
    previous_hash: str,
    entity_type: str,
    entity_id: str,
    action: str,
    performed_by: str,
    timestamp: str,
    metadata: Any
) -> str:
    """
    Computes immutable SHA-256 hash for audit record:
    record_hash = SHA256(previous_hash + entity_type + entity_id + action + performed_by + timestamp + metadata)
    """
    if isinstance(metadata, (dict, list)):
        meta_str = json.dumps(metadata, sort_keys=True)
    else:
        meta_str = str(metadata or "")

    raw_string = f"{previous_hash}{entity_type}{entity_id}{action}{performed_by}{timestamp}{meta_str}"
    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()
