import io
import csv
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.report import Report
from app.models.site import Site
from app.models.assignment import Assignment
from app.models.attendance import AttendanceLog
from app.models.compliance import ComplianceException
from app.models.audit import AuditLog
from app.models.enums import ReportType
from app.repositories.report_repo import ReportRepository
from app.services.compliance_engine import ComplianceEngine
from app.services.audit_service import AuditService
from app.utils.pdf_generator import generate_pdf_report


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)
        self.compliance_engine = ComplianceEngine(db)
        self.audit_service = AuditService(db)

    def generate_report_data(
        self,
        site_id: Optional[int],
        start_date: date,
        end_date: date,
        report_type: ReportType = ReportType.COMPLIANCE
    ) -> Dict[str, Any]:
        """Gathers unified operational metrics, exceptions, and audit chain state."""
        # Query assignments within window
        asg_query = self.db.query(Assignment).filter(
            Assignment.date >= start_date,
            Assignment.date <= end_date
        )
        if site_id:
            asg_query = asg_query.filter(Assignment.site_id == site_id)
        assignments = asg_query.all()

        total_asgs = len(assignments)
        completed = sum(1 for a in assignments if a.status == "COMPLETED")
        checked_in = sum(1 for a in assignments if a.status == "CHECKED_IN")
        missed = sum(1 for a in assignments if a.status == "MISSED")

        # Query exceptions
        exc_query = self.db.query(ComplianceException).join(Assignment, ComplianceException.assignment_id == Assignment.id).filter(
            Assignment.date >= start_date,
            Assignment.date <= end_date
        )
        if site_id:
            exc_query = exc_query.filter(Assignment.site_id == site_id)
        exceptions = exc_query.all()

        late_count = sum(1 for e in exceptions if e.violation_type == "LATE_CHECKIN")
        gps_count = sum(1 for e in exceptions if e.violation_type == "GPS_VIOLATION")
        qr_count = sum(1 for e in exceptions if e.violation_type == "QR_VIOLATION")

        # Site score
        if site_id:
            site = self.db.query(Site).filter(Site.id == site_id).first()
            score = self.compliance_engine.calculate_site_compliance_score(site_id) if site else 100.0
            site_name = site.name if site else "Unknown Site"
        else:
            site_name = "All Operational Sites"
            scores = [self.compliance_engine.calculate_site_compliance_score(s.id) for s in self.db.query(Site).all()]
            score = round(sum(scores) / max(1, len(scores)), 1) if scores else 100.0

        # Audit chain summary
        audit_records = self.db.query(AuditLog).filter(
            AuditLog.timestamp >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc),
            AuditLog.timestamp <= datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
        ).all()
        chain_verification = self.audit_service.verify_integrity()

        report_payload = {
            "title": f"Security Operations {report_type.value} Audit",
            "site_name": site_name,
            "period": f"{start_date} to {end_date}",
            "compliance_score": score,
            "attendance_summary": {
                "total_scheduled": total_asgs,
                "checked_in": checked_in,
                "completed": completed,
                "missed": missed,
                "late": late_count,
                "gps_violations": gps_count,
                "qr_violations": qr_count,
            },
            "exceptions": [e.to_dict() for e in exceptions],
            "audit_summary": {
                "total_events": len(audit_records),
                "chain_valid": chain_verification.get("valid", True),
                "records_checked": chain_verification.get("records_checked", 0),
                "latest_hash": chain_verification.get("chain_head", "N/A")
            }
        }
        return report_payload

    def save_report(
        self,
        site_id: Optional[int],
        start_date: date,
        end_date: date,
        generated_by: str,
        report_type: ReportType = ReportType.COMPLIANCE
    ) -> Report:
        data = self.generate_report_data(site_id, start_date, end_date, report_type)
        report = Report(
            site_id=site_id,
            date_range_start=start_date,
            date_range_end=end_date,
            generated_by=generated_by,
            report_type=report_type.value if hasattr(report_type, "value") else str(report_type),
            data=data
        )
        saved = self.repo.create(report)

        # Audit report generation
        self.audit_service.log_event(
            entity_type="REPORT",
            entity_id=str(saved.id),
            action="REPORT_GENERATED",
            performed_by=generated_by,
            metadata={"report_type": report.report_type, "site_id": site_id, "score": data.get("compliance_score")}
        )
        return saved

    def export_csv(self, report_id: int) -> str:
        report = self.repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Meta section
        writer.writerow(["REPORT_ID", report.id])
        writer.writerow(["TITLE", report.data.get("title")])
        writer.writerow(["SITE", report.data.get("site_name")])
        writer.writerow(["PERIOD", report.data.get("period")])
        writer.writerow(["COMPLIANCE_SCORE", f"{report.data.get('compliance_score')}%"])
        writer.writerow([])

        # Summary
        att = report.data.get("attendance_summary", {})
        writer.writerow(["METRIC", "VALUE"])
        for k, v in att.items():
            writer.writerow([k.upper(), v])
        writer.writerow([])

        # Exceptions
        writer.writerow(["EXCEPTION_ID", "VIOLATION_TYPE", "SEVERITY", "STATUS", "DETECTED_AT", "RESOLUTION"])
        for exc in report.data.get("exceptions", []):
            writer.writerow([
                exc.get("id"),
                exc.get("violation_type"),
                exc.get("severity"),
                exc.get("status"),
                exc.get("detected_at"),
                exc.get("resolution_notes")
            ])

        return output.getvalue()

    def export_pdf(self, report_id: int) -> bytes:
        report = self.repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")

        data = report.data
        return generate_pdf_report(
            title=data.get("title", "Compliance Report"),
            site_name=data.get("site_name", "All Sites"),
            date_range_start=str(report.date_range_start),
            date_range_end=str(report.date_range_end),
            compliance_score=float(data.get("compliance_score", 100.0)),
            generated_by=report.generated_by,
            report_type=report.report_type,
            report_data=data
        )
