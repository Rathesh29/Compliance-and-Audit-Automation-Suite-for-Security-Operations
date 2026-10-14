from datetime import date, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.dashboard import SiteDashboardResponse, AnalyticsResponse
from app.schemas.common import StandardResponse, success_response
from app.models.site import Site
from app.models.user import User
from app.models.assignment import Assignment
from app.models.compliance import ComplianceException
from app.services.compliance_engine import ComplianceEngine
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/site/{site_id}", response_model=StandardResponse[SiteDashboardResponse])
def get_site_dashboard(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SITE_NOT_FOUND", "message": "Site not found", "details": {}}
        )

    engine = ComplianceEngine(db)
    score = engine.calculate_site_compliance_score(site.id)

    today = date.today()
    today_asgs = db.query(Assignment).filter(Assignment.site_id == site_id, Assignment.date == today).all()

    total_guards = len(today_asgs)
    checked_in = sum(1 for a in today_asgs if a.status == "CHECKED_IN")
    completed = sum(1 for a in today_asgs if a.status == "COMPLETED")
    missing = sum(1 for a in today_asgs if a.status == "MISSED")
    scheduled = sum(1 for a in today_asgs if a.status == "SCHEDULED")

    # Collect exceptions for site
    exceptions = db.query(ComplianceException).join(Assignment, ComplianceException.assignment_id == Assignment.id).filter(
        Assignment.site_id == site_id
    ).all()

    open_exc = sum(1 for e in exceptions if e.status == "OPEN")
    late_guards = sum(1 for e in exceptions if e.violation_type == "LATE_CHECKIN")

    violations_summary = []
    for a in today_asgs:
        for v in (a.compliance_violations or []):
            violations_summary.append(v)

    return success_response({
        "site_id": site.id,
        "site_name": site.name,
        "compliance_score": score,
        "total_guards": total_guards,
        "scheduled_guards": scheduled,
        "checked_in_guards": checked_in,
        "missing_guards": missing,
        "late_guards": late_guards,
        "completed_guards": completed,
        "violations": violations_summary,
        "open_exceptions": open_exc
    })


@router.get("/analytics", response_model=StandardResponse[AnalyticsResponse])
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = ComplianceEngine(db)
    sites = db.query(Site).all()
    guards = db.query(User).filter(User.role == "GUARD").all()
    assignments = db.query(Assignment).all()
    exceptions = db.query(ComplianceException).all()

    total_sites = len(sites)
    total_guards = len(guards)
    total_assignments = len(assignments)

    open_exc = sum(1 for e in exceptions if e.status == "OPEN")
    resolved_exc = sum(1 for e in exceptions if e.status == "RESOLVED")
    total_exc = len(exceptions)
    res_rate = round((resolved_exc / total_exc * 100.0) if total_exc > 0 else 100.0, 1)

    late_arrivals = sum(1 for e in exceptions if e.violation_type == "LATE_CHECKIN")
    missed_shifts = sum(1 for e in exceptions if e.violation_type == "MISSED_SHIFT")
    overtime_count = sum(1 for e in exceptions if e.violation_type == "OVERTIME_VIOLATION")
    gps_violations = sum(1 for e in exceptions if e.violation_type == "GPS_VIOLATION")

    # Site scores
    site_scores = []
    total_score_sum = 0.0
    for s in sites:
        sc = engine.calculate_site_compliance_score(s.id)
        total_score_sum += sc
        site_scores.append({
            "site_id": s.id,
            "site_name": s.name,
            "score": sc,
            "radius_meters": s.radius_meters
        })

    overall_score = round(total_score_sum / max(1, len(sites)), 1) if sites else 100.0

    # Trend calculations (last 7 days)
    today = date.today()
    compliance_trend = []
    attendance_trend = []
    violation_trend = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%b %d")
        day_asgs = [a for a in assignments if a.date == day]
        day_exc = [e for e in exceptions if e.detected_at and e.detected_at.date() == day]

        c_in = sum(1 for a in day_asgs if a.status in ["CHECKED_IN", "COMPLETED"])
        miss = sum(1 for a in day_asgs if a.status == "MISSED")
        sched = len(day_asgs)

        # Baseline day compliance score
        day_comp = 100.0 if not day_asgs else max(40.0, round(100.0 - (len(day_exc) * 8.0), 1))

        compliance_trend.append({"date": day_str, "score": day_comp})
        attendance_trend.append({"date": day_str, "scheduled": sched, "checked_in": c_in, "missed": miss})
        violation_trend.append({
            "date": day_str,
            "late": sum(1 for e in day_exc if e.violation_type == "LATE_CHECKIN"),
            "gps": sum(1 for e in day_exc if e.violation_type == "GPS_VIOLATION"),
            "overtime": sum(1 for e in day_exc if e.violation_type == "OVERTIME_VIOLATION"),
            "total": len(day_exc)
        })

    return success_response({
        "overall_compliance_score": overall_score,
        "total_sites": total_sites,
        "total_guards": total_guards,
        "total_assignments": total_assignments,
        "open_exceptions_count": open_exc,
        "resolved_exceptions_count": resolved_exc,
        "exception_resolution_rate": res_rate,
        "late_arrivals_count": late_arrivals,
        "missed_shifts_count": missed_shifts,
        "overtime_count": overtime_count,
        "gps_violations_count": gps_violations,
        "compliance_trend": compliance_trend,
        "attendance_trend": attendance_trend,
        "violation_trend": violation_trend,
        "site_scores": site_scores
    })
