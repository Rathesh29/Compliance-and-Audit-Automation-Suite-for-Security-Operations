from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse, SiteQRResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.site_service import SiteService
from app.api.deps import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", response_model=StandardResponse[List[SiteResponse]])
def list_sites(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    sites = service.list_sites(search=search)
    return success_response([s.to_dict() for s in sites])


@router.post("", response_model=StandardResponse[SiteResponse], status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    site = service.create_site(payload, performed_by=current_user.email)
    return success_response(site.to_dict())


@router.get("/{site_id}", response_model=StandardResponse[SiteResponse])
def get_site(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    site = service.get_site(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SITE_NOT_FOUND", "message": f"Site #{site_id} not found", "details": {}}
        )
    return success_response(site.to_dict())


@router.put("/{site_id}", response_model=StandardResponse[SiteResponse])
def update_site(
    site_id: int,
    payload: SiteUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    try:
        site = service.update_site(site_id, payload, performed_by=current_user.email)
        return success_response(site.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SITE_UPDATE_FAILED", "message": str(e), "details": {}}
        )


@router.get("/{site_id}/qr", response_model=StandardResponse[SiteQRResponse])
def get_site_qr(
    site_id: int,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    try:
        qr_info = service.get_site_qr(site_id)
        return success_response(qr_info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SITE_NOT_FOUND", "message": str(e), "details": {}}
        )


@router.get("/{site_id}/compliance-score", response_model=StandardResponse[dict])
def get_site_compliance_score(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = SiteService(db)
    try:
        score_info = service.get_compliance_score(site_id)
        return success_response(score_info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SITE_NOT_FOUND", "message": str(e), "details": {}}
        )
