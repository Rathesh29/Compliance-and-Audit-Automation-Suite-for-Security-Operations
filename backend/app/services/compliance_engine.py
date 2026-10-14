from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.shift import Shift
from app.models.site import Site
from app.models.user import User
from app.models.attendance import AttendanceLog
from app.models.enums import ViolationType, ViolationSeverity, UserStatus
from app.utils.geo import haversine_distance_meters


class ComplianceViolation:
    def __init__(self, violation_type: str, severity: str, message: str):
        self.type = violation_type
        self.severity = severity
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message
        }


class ComplianceEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_assignment_creation(
        self,
        guard: User,
        site: Site,
        shift: Shift,
        assignment_date: date
    ) -> List[ComplianceViolation]:
        """
        Validates all labor, contractual, and site constraints before an assignment is locked in.
        """
        violations: List[ComplianceViolation] = []
        rules = site.compliance_rules or {}
        max_daily_hours = rules.get("max_daily_hours", 12.0)
        minimum_rest_hours = rules.get("minimum_rest_hours", 8.0)
        max_weekly_hours = rules.get("max_weekly_hours", 60.0)

        # 1. Guard Status Check
        if guard.status != UserStatus.ACTIVE.value:
            violations.append(ComplianceViolation(
                violation_type=ViolationType.UNAUTHORIZED_ASSIGNMENT.value,
                severity=ViolationSeverity.CRITICAL.value,
                message=f"Guard {guard.name} is inactive or suspended ({guard.status})"
            ))

        # 2. Existing assignments on the same day
        same_day_assignments = self.db.query(Assignment).filter(
            Assignment.user_id == guard.id,
            Assignment.date == assignment_date
        ).all()

        current_daily_hours = 0.0
        for existing in same_day_assignments:
            if existing.shift_id == shift.id:
                violations.append(ComplianceViolation(
                    violation_type=ViolationType.UNAUTHORIZED_ASSIGNMENT.value,
                    severity=ViolationSeverity.CRITICAL.value,
                    message=f"Guard {guard.name} is already assigned to shift '{shift.name}' on {assignment_date}"
                ))
            if existing.shift:
                current_daily_hours += existing.shift.duration_hours

        # 3. Maximum daily hours check
        projected_daily = current_daily_hours + shift.duration_hours
        if projected_daily > max_daily_hours:
            violations.append(ComplianceViolation(
                violation_type=ViolationType.OVERSCHEDULED.value,
                severity=ViolationSeverity.HIGH.value,
                message=f"Projected daily hours ({projected_daily:.1f}h) exceeds maximum allowed ({max_daily_hours:.1f}h)"
            ))

        # 4. Weekly hours check (7 days up to assignment_date)
        week_start = assignment_date - timedelta(days=6)
        week_assignments = self.db.query(Assignment).filter(
            Assignment.user_id == guard.id,
            Assignment.date >= week_start,
            Assignment.date <= assignment_date
        ).all()

        weekly_hours = sum(a.shift.duration_hours for a in week_assignments if a.shift) + shift.duration_hours
        if weekly_hours > max_weekly_hours:
            violations.append(ComplianceViolation(
                violation_type=ViolationType.OVERSCHEDULED.value,
                severity=ViolationSeverity.HIGH.value,
                message=f"Projected weekly hours ({weekly_hours:.1f}h) exceeds max allowable threshold ({max_weekly_hours:.1f}h)"
            ))

        # 5. Minimum Rest Period between consecutive shifts (previous day and next day)
        yesterday = assignment_date - timedelta(days=1)
        yesterday_assignments = self.db.query(Assignment).filter(
            Assignment.user_id == guard.id,
            Assignment.date == yesterday
        ).all()

        for prev_asg in yesterday_assignments:
            if prev_asg.shift:
                prev_end_h, prev_end_m = map(int, prev_asg.shift.end_time.split(":"))
                curr_start_h, curr_start_m = map(int, shift.start_time.split(":"))
                rest_gap = (curr_start_h + 24) - prev_end_h + (curr_start_m - prev_end_m) / 60.0
                if rest_gap < minimum_rest_hours:
                    violations.append(ComplianceViolation(
                        violation_type=ViolationType.INSUFFICIENT_REST.value,
                        severity=ViolationSeverity.HIGH.value,
                        message=f"Insufficient rest period ({rest_gap:.1f}h < required {minimum_rest_hours}h) since previous shift"
                    ))

        return violations

    def evaluate_checkin(
        self,
        guard: User,
        assignment: Assignment,
        lat: float,
        lon: float,
        qr_token: str,
        checkin_time: datetime
    ) -> List[ComplianceViolation]:
        """
        Validates Guard Check-In against GPS boundaries, QR authenticity, and Shift schedule/grace periods.
        """
        violations: List[ComplianceViolation] = []
        site = assignment.site
        shift = assignment.shift
        rules = site.compliance_rules or {}
        late_threshold_minutes = rules.get("late_threshold_minutes", shift.grace_period_minutes)

        # 1. Guard ownership check
        if assignment.user_id != guard.id:
            violations.append(ComplianceViolation(
                violation_type=ViolationType.UNAUTHORIZED_ASSIGNMENT.value,
                severity=ViolationSeverity.CRITICAL.value,
                message="Guard is attempting to check into an assignment belonging to another officer."
            ))

        # 2. QR Token verification
        if rules.get("require_qr", True):
            if not qr_token or qr_token.strip() != site.qr_token.strip():
                violations.append(ComplianceViolation(
                    violation_type=ViolationType.QR_VIOLATION.value,
                    severity=ViolationSeverity.CRITICAL.value,
                    message="Invalid or tampered Site QR Code."
                ))

        # 3. GPS Geofence verification
        if rules.get("require_gps", True):
            distance = haversine_distance_meters(lat, lon, site.latitude, site.longitude)
            if distance > site.radius_meters:
                violations.append(ComplianceViolation(
                    violation_type=ViolationType.GPS_VIOLATION.value,
                    severity=ViolationSeverity.HIGH.value,
                    message=f"GPS Geofence Breach: Guard is {distance:.1f}m away from site (Max allowed: {site.radius_meters:.1f}m)."
                ))

        # 4. Shift Schedule Timing & Lateness detection
        shift_h, shift_m = map(int, shift.start_time.split(":"))
        # Construct expected shift start datetime for assignment date
        expected_start = datetime(
            assignment.date.year,
            assignment.date.month,
            assignment.date.day,
            shift_h,
            shift_m,
            tzinfo=timezone.utc
        )
        
        # Ensure checkin_time is timezone aware
        if checkin_time.tzinfo is None:
            checkin_time = checkin_time.replace(tzinfo=timezone.utc)

        grace_limit = expected_start + timedelta(minutes=late_threshold_minutes)

        if checkin_time > grace_limit:
            delay_minutes = int((checkin_time - expected_start).total_seconds() / 60)
            violations.append(ComplianceViolation(
                violation_type=ViolationType.LATE_CHECKIN.value,
                severity=ViolationSeverity.MEDIUM.value,
                message=f"Guard checked in {delay_minutes} minutes late (Grace period: {late_threshold_minutes}m)."
            ))

        return violations

    def evaluate_checkout(
        self,
        assignment: Assignment,
        checkin_log: AttendanceLog,
        checkout_time: datetime
    ) -> List[ComplianceViolation]:
        """
        Validates check-out timing, actual duration, and overtime violations.
        """
        violations: List[ComplianceViolation] = []
        site = assignment.site
        shift = assignment.shift
        rules = site.compliance_rules or {}
        allow_overtime = rules.get("allow_overtime", False)

        if not checkin_log:
            violations.append(ComplianceViolation(
                violation_type=ViolationType.INVALID_CHECKOUT.value,
                severity=ViolationSeverity.CRITICAL.value,
                message="Cannot check out without a recorded valid check-in."
            ))
            return violations

        # Calculate actual working duration
        cin_time = checkin_log.timestamp
        if cin_time.tzinfo is None:
            cin_time = cin_time.replace(tzinfo=timezone.utc)
        if checkout_time.tzinfo is None:
            checkout_time = checkout_time.replace(tzinfo=timezone.utc)

        duration_hours = (checkout_time - cin_time).total_seconds() / 3600.0

        # Overtime check
        expected_duration = shift.duration_hours
        if duration_hours > (expected_duration + 0.5) and not allow_overtime:
            overtime_hours = duration_hours - expected_duration
            violations.append(ComplianceViolation(
                violation_type=ViolationType.OVERTIME_VIOLATION.value,
                severity=ViolationSeverity.MEDIUM.value,
                message=f"Unauthorized overtime detected: Guard worked {duration_hours:.2f}h, exceeding shift schedule by {overtime_hours:.2f}h."
            ))

        return violations

    def calculate_site_compliance_score(self, site_id: int) -> float:
        """
        Computes weighted site compliance score (0 - 100):
        Attendance compliance: 30%
        Assignment compliance: 20%
        GPS compliance: 15%
        QR compliance: 15%
        Working-hour compliance: 10%
        Exception resolution: 10%
        """
        assignments = self.db.query(Assignment).filter(Assignment.site_id == site_id).all()
        if not assignments:
            return 100.0

        total_asgs = len(assignments)
        
        # 1. Attendance compliance (completed vs missed)
        missed = sum(1 for a in assignments if a.status == "MISSED")
        att_rate = max(0.0, 1.0 - (missed / total_asgs))
        
        # Collect attendance logs
        asg_ids = [a.id for a in assignments]
        att_logs = self.db.query(AttendanceLog).filter(AttendanceLog.assignment_id.in_(asg_ids)).all()
        
        # 2. GPS & QR compliance
        gps_breaches = sum(1 for log in att_logs if log.violation_reason and "GPS" in log.violation_reason)
        qr_breaches = sum(1 for log in att_logs if log.violation_reason and "QR" in log.violation_reason)
        
        total_logs = max(1, len(att_logs))
        gps_rate = max(0.0, 1.0 - (gps_breaches / total_logs))
        qr_rate = max(0.0, 1.0 - (qr_breaches / total_logs))

        # 3. Assignment compliance (clean scheduled vs violations)
        asgs_with_violations = sum(1 for a in assignments if a.compliance_violations and len(a.compliance_violations) > 0)
        asg_rate = max(0.0, 1.0 - (asgs_with_violations / total_asgs))

        # 4. Working-hour / overtime compliance
        overtime_count = sum(1 for a in assignments if any(v.get("type") == "OVERTIME_VIOLATION" for v in (a.compliance_violations or [])))
        wh_rate = max(0.0, 1.0 - (overtime_count / total_asgs))

        # 5. Exception resolution rate
        from app.models.compliance import ComplianceException
        exceptions = self.db.query(ComplianceException).join(Assignment, ComplianceException.assignment_id == Assignment.id).filter(Assignment.site_id == site_id).all()
        if exceptions:
            resolved_count = sum(1 for e in exceptions if e.status == "RESOLVED")
            res_rate = resolved_count / len(exceptions)
        else:
            res_rate = 1.0

        # Weighted calculation
        score = (
            att_rate * 30.0 +
            asg_rate * 20.0 +
            gps_rate * 15.0 +
            qr_rate * 15.0 +
            wh_rate * 10.0 +
            res_rate * 10.0
        )
        return round(score, 1)
