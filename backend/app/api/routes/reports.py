from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.schemas.common import StandardResponse, success_response, error_response
from app.services.report_service import ReportService
from app.api.deps import get_current_user, require_roles
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=StandardResponse[List[ReportResponse]])
def list_reports(
    site_id: Optional[int] = None,
    report_type: Optional[str] = None,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    reports = service.repo.list_reports(site_id=site_id, report_type=report_type)
    return success_response([r.to_dict() for r in reports])


@router.post("/generate", response_model=StandardResponse[ReportResponse], status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    report = service.save_report(
        site_id=payload.site_id,
        start_date=payload.date_range_start,
        end_date=payload.date_range_end,
        generated_by=current_user.email,
        report_type=payload.report_type
    )
    return success_response(report.to_dict())


@router.get("/{report_id}/csv")
def export_report_csv(
    report_id: int,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        csv_data = service.export_csv(report_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": str(e), "details": {}}
        )


@router.get("/{report_id}/pdf")
def export_report_pdf(
    report_id: int,
    current_user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "AUDITOR")),
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    try:
        pdf_data = service.export_pdf(report_id)
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=compliance_report_{report_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": str(e), "details": {}}
        )
