from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.audit import AuditLogResponse, AuditIntegrityResponse
from app.schemas.compliance import ComplianceExceptionResponse, ExceptionResolveRequest
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.audit_service import AuditService
from app.services.report_service import ReportService
from app.repositories.compliance_repo import ComplianceRepository
from app.api.deps import get_current_user, require_roles
from app.models.user import User
from app.models.enums import ExceptionStatus

router = APIRouter(prefix="/audit", tags=["Audit & Integrity"])


@router.get("/logs", response_model=StandardResponse[List[AuditLogResponse]])
def get_audit_logs(
    entity: Optional[str] = Query(None, alias="entity"),
    entity_id: Optional[str] = Query(None, alias="entity_id"),
    action: Optional[str] = Query(None, alias="action"),
    performed_by: Optional[str] = Query(None, alias="performed_by"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = AuditService(db)
    logs = service.repo.list_logs(
        entity_type=entity,
        entity_id=entity_id,
        action=action,
        performed_by=performed_by,
        limit=limit,
        offset=offset
    )
    return success_response([l.to_dict() for l in logs])


@router.get("/integrity", response_model=StandardResponse[AuditIntegrityResponse])
def verify_audit_integrity(
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = AuditService(db)
    verification = service.verify_integrity()
    return success_response(verification)


@router.get("/exceptions", response_model=StandardResponse[List[ComplianceExceptionResponse]])
def list_compliance_exceptions(
    site_id: Optional[int] = Query(None, alias="site"),
    violation_type: Optional[str] = Query(None, alias="violation_type"),
    status_val: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None, alias="severity"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    comp_repo = ComplianceRepository(db)
    exceptions = comp_repo.list_exceptions(
        site_id=site_id,
        violation_type=violation_type,
        status=status_val,
        severity=severity,
        limit=limit,
        offset=offset
    )
    return success_response([e.to_dict() for e in exceptions])


@router.post("/exceptions/{exception_id}/resolve", response_model=StandardResponse[ComplianceExceptionResponse])
def resolve_compliance_exception(
    exception_id: int,
    payload: ExceptionResolveRequest,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR")),
    db: Session = Depends(get_db)
):
    comp_repo = ComplianceRepository(db)
    exc = comp_repo.get_by_id(exception_id)
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EXCEPTION_NOT_FOUND", "message": "Compliance exception not found", "details": {}}
        )

    exc.status = ExceptionStatus.RESOLVED.value
    exc.resolved_at = datetime.utcnow()
    exc.resolved_by = current_user.email
    exc.resolution_notes = payload.resolution_notes
    updated = comp_repo.update(exc)

    # Immutable audit record of exception resolution
    audit_service = AuditService(db)
    audit_service.log_event(
        entity_type="EXCEPTION",
        entity_id=str(updated.id),
        action="EXCEPTION_RESOLVED",
        performed_by=current_user.email,
        metadata={"notes": payload.resolution_notes, "violation_type": updated.violation_type}
    )

    return success_response(updated.to_dict())
