from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole, UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MFARequest(BaseModel):
    user_id: int
    code: str


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    mfa_required: bool = False
    user_id: Optional[int] = None
    role: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.GUARD
    phone: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    status: Optional[UserStatus] = None
    mfa_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    phone: Optional[str] = None
    mfa_enabled: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
