from datetime import datetime, timezone, date
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.attendance import AttendanceLog
from app.models.compliance import ComplianceException
from app.models.user import User
from app.models.enums import (
    AssignmentStatus,
    AttendanceType,
    ViolationType,
    ViolationSeverity,
    ExceptionStatus
)
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.compliance_repo import ComplianceRepository
from app.services.compliance_engine import ComplianceEngine
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.websocket_manager import ws_manager
import asyncio


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db
        self.asg_repo = AssignmentRepository(db)
        self.att_repo = AttendanceRepository(db)
        self.comp_repo = ComplianceRepository(db)
        self.compliance_engine = ComplianceEngine(db)
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    def process_check_in(
        self,
        guard: User,
        assignment_id: int,
        latitude: float,
        longitude: float,
        qr_token: str,
        timestamp: Optional[datetime] = None
    ) -> Tuple[AttendanceLog, Assignment, List[Dict[str, Any]]]:
        """
        Executes end-to-end check-in validation.
        Enforces:
        - Guard ownership
        - Valid date / assignment status
        - Haversine GPS geofence
        - QR token validity
        - Shift grace period & lateness detection
        Logs append-only audit events and exceptions.
        """
        now = timestamp or datetime.now(timezone.utc)
        assignment = self.asg_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment #{assignment_id} not found.")

        # Guard assignment verification (Rule 1: A guard cannot check into another guard's assignment)
        if assignment.user_id != guard.id:
            self.audit.log_event(
                entity_type="ATTENDANCE",
                entity_id=str(assignment_id),
                action="UNAUTHORIZED_CHECKIN_ATTEMPT",
                performed_by=guard.email,
                metadata={"reason": "Assignment belongs to different user"}
            )
            raise ValueError("Forbidden: You cannot check into an assignment that does not belong to you.")

        # Status check
        if assignment.status in [AssignmentStatus.COMPLETED.value, AssignmentStatus.MISSED.value]:
            raise ValueError(f"Cannot check in: Assignment is already marked as {assignment.status}.")

        # Run compliance engine check-in evaluation
        violations = self.compliance_engine.evaluate_checkin(
            guard=guard,
            assignment=assignment,
            lat=latitude,
            lon=longitude,
            qr_token=qr_token,
            checkin_time=now
        )

        has_critical_blocker = any(v.severity == ViolationSeverity.CRITICAL.value for v in violations)
        is_valid_checkin = not has_critical_blocker
        violation_reason = "; ".join([v.message for v in violations]) if violations else None

        # Create attendance log
        log = AttendanceLog(
            assignment_id=assignment.id,
            type=AttendanceType.CHECK_IN.value,
            timestamp=now,
            latitude=latitude,
            longitude=longitude,
            qr_token=qr_token,
            is_valid=is_valid_checkin,
            violation_reason=violation_reason,
            created_at=now
        )
        saved_log = self.att_repo.create(log)

        if not is_valid_checkin:
            # Audit rejected check-in
            self.audit.log_event(
                entity_type="ATTENDANCE",
                entity_id=str(saved_log.id),
                action="CHECK_IN_REJECTED",
                performed_by=guard.email,
                metadata={"reason": violation_reason}
            )
            raise ValueError(f"Check-in rejected: {violation_reason}")

        # Update assignment to CHECKED_IN
        assignment.status = AssignmentStatus.CHECKED_IN.value
        if violations:
            current_viols = list(assignment.compliance_violations or [])
            current_viols.extend([v.to_dict() for v in violations])
            assignment.compliance_violations = current_viols
        self.asg_repo.update(assignment)

        # Audit successful check-in
        self.audit.log_event(
            entity_type="ATTENDANCE",
            entity_id=str(saved_log.id),
            action="CHECK_IN",
            performed_by=guard.email,
            metadata={
                "site": assignment.site.name,
                "shift": assignment.shift.name,
                "latitude": latitude,
                "longitude": longitude,
                "has_violations": len(violations) > 0
            }
        )

        # Record compliance exceptions & trigger notifications
        for v in violations:
            exc = ComplianceException(
                assignment_id=assignment.id,
                violation_type=v.type,
                severity=v.severity,
                status=ExceptionStatus.OPEN.value,
                detected_at=now,
                resolution_notes=f"Detected automatically during guard check-in: {v.message}"
            )
            self.comp_repo.create(exc)

            # Audit exception creation
            self.audit.log_event(
                entity_type="EXCEPTION",
                entity_id=str(exc.id),
                action="EXCEPTION_CREATED",
                performed_by="SYSTEM",
                metadata={"violation_type": v.type, "guard": guard.email, "site": assignment.site.name}
            )

            # Trigger supervisor notification
            self.notification.send_notification(
                notif_type=v.type,
                title=f"{v.type} Detected: {guard.name}",
                message=f"{guard.name} at {assignment.site.name}: {v.message}",
                recipient_role="SUPERVISOR",
                data={"assignment_id": assignment.id, "violation": v.to_dict()}
            )

        # Broadcast live event for real-time dashboard update
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast("check_in", {
                    "assignment_id": assignment.id,
                    "guard_name": guard.name,
                    "site_name": assignment.site.name,
                    "status": assignment.status,
                    "violations": [v.to_dict() for v in violations]
                }))
        except Exception:
            pass

        return saved_log, assignment, [v.to_dict() for v in violations]

    def process_check_out(
        self,
        guard: User,
        assignment_id: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        qr_token: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Tuple[AttendanceLog, Assignment, List[Dict[str, Any]]]:
        """
        Executes check-out validation:
        - Verifies guard ownership
        - Confirms prior valid check-in exists
        - Evaluates duration & overtime
        - Transitions assignment to COMPLETED
        - Emits tamper-evident audit records
        """
        now = timestamp or datetime.now(timezone.utc)
        assignment = self.asg_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment #{assignment_id} not found.")

        if assignment.user_id != guard.id:
            raise ValueError("Forbidden: You cannot check out of another guard's assignment.")

        if assignment.status != AssignmentStatus.CHECKED_IN.value:
            raise ValueError(f"Invalid checkout: Assignment status is {assignment.status}, must be CHECKED_IN.")

        # Retrieve check-in record
        checkin_log = self.att_repo.get_by_assignment_and_type(assignment.id, AttendanceType.CHECK_IN.value)
        if not checkin_log:
            raise ValueError("Invalid checkout: No valid check-in record found for this assignment.")

        # Evaluate overtime / checkout compliance
        violations = self.compliance_engine.evaluate_checkout(
            assignment=assignment,
            checkin_log=checkin_log,
            checkout_time=now
        )

        violation_reason = "; ".join([v.message for v in violations]) if violations else None

        # Create checkout attendance log
        log = AttendanceLog(
            assignment_id=assignment.id,
            type=AttendanceType.CHECK_OUT.value,
            timestamp=now,
            latitude=latitude,
            longitude=longitude,
            qr_token=qr_token,
            is_valid=True,
            violation_reason=violation_reason,
            created_at=now
        )
        saved_log = self.att_repo.create(log)

        # Transition assignment to COMPLETED
        assignment.status = AssignmentStatus.COMPLETED.value
        if violations:
            current_viols = list(assignment.compliance_violations or [])
            current_viols.extend([v.to_dict() for v in violations])
            assignment.compliance_violations = current_viols
        self.asg_repo.update(assignment)

        # Audit check-out
        cin_ts = checkin_log.timestamp
        if cin_ts.tzinfo is None:
            cin_ts = cin_ts.replace(tzinfo=timezone.utc)
        duration_hours = round((now - cin_ts).total_seconds() / 3600.0, 2)

        self.audit.log_event(
            entity_type="ATTENDANCE",
            entity_id=str(saved_log.id),
            action="CHECK_OUT",
            performed_by=guard.email,
            metadata={
                "site": assignment.site.name,
                "duration_hours": duration_hours,
                "overtime": len(violations) > 0
            }
        )

        for v in violations:
            exc = ComplianceException(
                assignment_id=assignment.id,
                violation_type=v.type,
                severity=v.severity,
                status=ExceptionStatus.OPEN.value,
                detected_at=now,
                resolution_notes=f"Detected during checkout: {v.message}"
            )
            self.comp_repo.create(exc)

            self.notification.send_notification(
                notif_type=v.type,
                title=f"{v.type}: {guard.name}",
                message=f"Guard worked {duration_hours}h at {assignment.site.name}. {v.message}",
                recipient_role="SUPERVISOR"
            )

        # Broadcast live checkout event
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast("check_out", {
                    "assignment_id": assignment.id,
                    "guard_name": guard.name,
                    "site_name": assignment.site.name,
                    "status": assignment.status,
                    "duration_hours": duration_hours
                }))
        except Exception:
            pass

        return saved_log, assignment, [v.to_dict() for v in violations]

    def get_guard_attendance_status(self, guard_id: int) -> List[Dict[str, Any]]:
        """Get live attendance statuses for guard's assignments today & upcoming."""
        today = date.today()
        assignments = self.asg_repo.list_assignments(user_id=guard_id, assignment_date=today)
        results = []
        for asg in assignments:
            cin = self.att_repo.get_by_assignment_and_type(asg.id, AttendanceType.CHECK_IN.value)
            cout = self.att_repo.get_by_assignment_and_type(asg.id, AttendanceType.CHECK_OUT.value)
            
            duration = None
            if cin and cout:
                c1 = cin.timestamp.replace(tzinfo=timezone.utc) if cin.timestamp.tzinfo is None else cin.timestamp
                c2 = cout.timestamp.replace(tzinfo=timezone.utc) if cout.timestamp.tzinfo is None else cout.timestamp
                duration = round((c2 - c1).total_seconds() / 3600.0, 2)

            results.append({
                "assignment_id": asg.id,
                "status": asg.status,
                "site_name": asg.site.name if asg.site else "Site",
                "shift_name": asg.shift.name if asg.shift else "Shift",
                "shift_start": asg.shift.start_time if asg.shift else "",
                "shift_end": asg.shift.end_time if asg.shift else "",
                "date": str(asg.date),
                "check_in_time": cin.timestamp.isoformat() if cin else None,
                "check_out_time": cout.timestamp.isoformat() if cout else None,
                "duration_hours": duration,
                "violations": [v.get("message", "") for v in (asg.compliance_violations or [])]
            })
        return results
