from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import LoginRequest, MFARequest, TokenResponse, MFASetupResponse, UserResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=StandardResponse[TokenResponse])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"

    user, error_msg = auth_service.authenticate_user(payload.email, payload.password, client_ip)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "LOGIN_FAILED", "message": error_msg or "Invalid email or password", "details": {}}
        )

    # Check if user requires MFA
    if user.mfa_enabled:
        return success_response({
            "access_token": "",
            "token_type": "bearer",
            "mfa_required": True,
            "user_id": user.id,
            "role": user.role,
            "email": user.email,
            "name": user.name
        })

    token = auth_service.issue_token_for_user(user)
    return success_response({
        "access_token": token,
        "token_type": "bearer",
        "mfa_required": False,
        "user_id": user.id,
        "role": user.role,
        "email": user.email,
        "name": user.name
    })


@router.post("/mfa", response_model=StandardResponse[TokenResponse])
def verify_mfa(payload: MFARequest, request: Request, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"

    token, error_msg = auth_service.verify_mfa_login(payload.user_id, payload.code, client_ip)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MFA_FAILED", "message": error_msg or "Invalid verification code", "details": {}}
        )

    user = auth_service.repo.get_by_id(payload.user_id)
    return success_response({
        "access_token": token,
        "token_type": "bearer",
        "mfa_required": False,
        "user_id": user.id,
        "role": user.role,
        "email": user.email,
        "name": user.name
    })


@router.post("/mfa/setup", response_model=StandardResponse[MFASetupResponse])
def setup_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    res = auth_service.setup_mfa(current_user)
    return success_response(res)


@router.get("/me", response_model=StandardResponse[UserResponse])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return success_response(current_user.to_dict())
