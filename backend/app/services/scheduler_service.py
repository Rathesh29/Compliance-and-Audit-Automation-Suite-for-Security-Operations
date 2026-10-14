from datetime import datetime, timezone, date, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.attendance import AttendanceLog
from app.models.compliance import ComplianceException
from app.models.enums import AssignmentStatus, ViolationType, ViolationSeverity, ExceptionStatus
from app.database.session import SessionLocal
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.core.logging_config import logger
import asyncio


class SchedulerService:
    @staticmethod
    def detect_and_mark_missed_shifts(db: Session) -> int:
        """
        Scans scheduled assignments. If shift start + grace period has lapsed
        and no check-in exists, flags assignment as MISSED, creates compliance exception,
        logs tamper-evident audit record, and alerts supervisor.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        # Find candidates: SCHEDULED or ASSIGNED for today (or yesterday for overnight)
        candidates = db.query(Assignment).filter(
            Assignment.status.in_([AssignmentStatus.SCHEDULED.value, AssignmentStatus.ASSIGNED.value]),
            Assignment.date <= today
        ).all()

        missed_count = 0
        audit_service = AuditService(db)
        notif_service = NotificationService(db)

        for asg in candidates:
            shift = asg.shift
            if not shift:
                continue

            shift_h, shift_m = map(int, shift.start_time.split(":"))
            expected_start = datetime(
                asg.date.year,
                asg.date.month,
                asg.date.day,
                shift_h,
                shift_m,
                tzinfo=timezone.utc
            )

            grace_limit = expected_start + timedelta(minutes=shift.grace_period_minutes)

            if now > grace_limit:
                # Confirm whether any check-in exists
                has_checkin = db.query(AttendanceLog).filter(
                    AttendanceLog.assignment_id == asg.id,
                    AttendanceLog.type == "CHECK_IN"
                ).first()

                if not has_checkin:
                    asg.status = AssignmentStatus.MISSED.value
                    db.commit()
                    missed_count += 1

                    # Create compliance exception
                    exc = ComplianceException(
                        assignment_id=asg.id,
                        violation_type=ViolationType.MISSED_SHIFT.value,
                        severity=ViolationSeverity.CRITICAL.value,
                        status=ExceptionStatus.OPEN.value,
                        detected_at=now,
                        resolution_notes=f"Automatic detection: Guard did not check in within grace period ({shift.grace_period_minutes}m)."
                    )
                    db.add(exc)
                    db.commit()

                    # Audit event
                    audit_service.log_event(
                        entity_type="ASSIGNMENT",
                        entity_id=str(asg.id),
                        action="MISSED_SHIFT",
                        performed_by="SYSTEM",
                        metadata={
                            "guard": asg.user.email if asg.user else "Unknown",
                            "site": asg.site.name if asg.site else "Unknown",
                            "shift": shift.name
                        }
                    )

                    # Supervisor notification
                    notif_service.send_notification(
                        notif_type=ViolationType.MISSED_SHIFT.value,
                        title=f"CRITICAL: Missed Shift Alert at {asg.site.name if asg.site else 'Site'}",
                        message=f"Guard {asg.user.name if asg.user else 'Assigned Guard'} failed to report for shift '{shift.name}'. Marked as MISSED.",
                        recipient_role="SUPERVISOR",
                        data={"assignment_id": asg.id}
                    )

        if missed_count > 0:
            logger.info(f"[SCHEDULER] Automatically flagged {missed_count} missed shifts.")
        return missed_count


async def run_missed_shift_scheduler_loop(interval_seconds: int = 60):
    """
    Lightweight background loop for local execution and standalone production worker.
    """
    while True:
        try:
            db = SessionLocal()
            try:
                SchedulerService.detect_and_mark_missed_shifts(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[SCHEDULER] Background worker encountered error: {e}")
        await asyncio.sleep(interval_seconds)
