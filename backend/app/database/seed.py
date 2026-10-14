from datetime import datetime, date, timedelta, timezone
from app.database.session import SessionLocal, Base, engine
from app.models.user import User
from app.models.site import Site
from app.models.shift import Shift
from app.models.assignment import Assignment
from app.models.attendance import AttendanceLog
from app.models.compliance import ComplianceException
from app.models.notification import Notification
from app.models.report import Report
from app.models.enums import (
    UserRole,
    UserStatus,
    AssignmentStatus,
    AttendanceType,
    ViolationType,
    ViolationSeverity,
    ExceptionStatus,
    ReportType
)
from app.core.security import get_password_hash
from app.services.audit_service import AuditService
from app.services.compliance_engine import ComplianceEngine
from app.services.report_service import ReportService
from app.utils.qr import generate_secure_qr_token


def seed_database():
    print("Starting database seeding...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    audit_service = AuditService(db)

    try:
        # Check if already seeded
        admin_check = db.query(User).filter(User.email == "admin@security-ops.com").first()
        if admin_check:
            print("Database already contains seed data. Skipping duplicate insertion.")
            return

        demo_password = get_password_hash("Password123!")

        # 1. USERS
        print("Creating users...")
        users_data = [
            # Admin
            {"name": "System Administrator", "email": "admin@security-ops.com", "role": UserRole.ADMIN.value, "phone": "+1-555-0101"},
            # Supervisors
            {"name": "Sarah Jenkins (Supervisor)", "email": "supervisor.jenkins@security-ops.com", "role": UserRole.SUPERVISOR.value, "phone": "+1-555-0102"},
            {"name": "Marcus Vance (Supervisor)", "email": "supervisor.vance@security-ops.com", "role": UserRole.SUPERVISOR.value, "phone": "+1-555-0103"},
            # Auditor
            {"name": "Elena Rostova (Lead Auditor)", "email": "auditor.rostova@security-ops.com", "role": UserRole.AUDITOR.value, "phone": "+1-555-0104"},
            # Guards
            {"name": "Guard 001 - James Miller", "email": "guard.001@security-ops.com", "role": UserRole.GUARD.value, "phone": "+1-555-0201"},
            {"name": "Guard 002 - David Chen", "email": "guard.002@security-ops.com", "role": UserRole.GUARD.value, "phone": "+1-555-0202"},
            {"name": "Guard 003 - Maria Rodriguez", "email": "guard.003@security-ops.com", "role": UserRole.GUARD.value, "phone": "+1-555-0203"},
            {"name": "Guard 004 - Robert Taylor", "email": "guard.004@security-ops.com", "role": UserRole.GUARD.value, "phone": "+1-555-0204"},
            {"name": "Guard 005 - Aisha Patel", "email": "guard.005@security-ops.com", "role": UserRole.GUARD.value, "phone": "+1-555-0205"},
        ]

        created_users = {}
        for u in users_data:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=demo_password,
                role=u["role"],
                status=UserStatus.ACTIVE.value,
                phone=u["phone"],
                mfa_enabled=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users[u["email"]] = user
            audit_service.log_event(
                entity_type="USER",
                entity_id=str(user.id),
                action="USER_CREATED",
                performed_by="SYSTEM_INIT",
                metadata={"name": user.name, "role": user.role}
            )

        # 2. SITES
        print("Creating operational sites...")
        sites_data = [
            {
                "name": "Corporate Tower Headquarters",
                "location_name": "742 Evergreen Plaza, Financial District",
                "latitude": 37.774929,
                "longitude": -122.419416,
                "radius_meters": 120.0,
                "qr_token": "SITE-SEC-CORP-TOWER-7749",
                "compliance_rules": {
                    "max_daily_hours": 10.0,
                    "minimum_rest_hours": 10.0,
                    "max_weekly_hours": 50.0,
                    "allow_overtime": False,
                    "require_qr": True,
                    "require_gps": True,
                    "late_threshold_minutes": 10
                }
            },
            {
                "name": "Industrial Facility & Logistics Port",
                "location_name": "Gate 4, Bay Industrial Complex",
                "latitude": 37.798853,
                "longitude": -122.398672,
                "radius_meters": 250.0,
                "qr_token": "SITE-SEC-IND-PORT-9885",
                "compliance_rules": {
                    "max_daily_hours": 12.0,
                    "minimum_rest_hours": 8.0,
                    "max_weekly_hours": 60.0,
                    "allow_overtime": True,
                    "require_qr": True,
                    "require_gps": True,
                    "late_threshold_minutes": 15
                }
            },
            {
                "name": "Highland Crest Residential Complex",
                "location_name": "South Gate, 1200 Highland Ave",
                "latitude": 37.753344,
                "longitude": -122.441228,
                "radius_meters": 100.0,
                "qr_token": "SITE-SEC-RES-CREST-5334",
                "compliance_rules": {
                    "max_daily_hours": 8.0,
                    "minimum_rest_hours": 12.0,
                    "max_weekly_hours": 48.0,
                    "allow_overtime": False,
                    "require_qr": True,
                    "require_gps": True,
                    "late_threshold_minutes": 5
                }
            }
        ]

        created_sites = []
        for s in sites_data:
            site = Site(
                name=s["name"],
                location_name=s["location_name"],
                latitude=s["latitude"],
                longitude=s["longitude"],
                radius_meters=s["radius_meters"],
                qr_token=s["qr_token"],
                compliance_rules=s["compliance_rules"],
                compliance_score=95.0
            )
            db.add(site)
            db.commit()
            db.refresh(site)
            created_sites.append(site)
            audit_service.log_event(
                entity_type="SITE",
                entity_id=str(site.id),
                action="SITE_CREATED",
                performed_by="SYSTEM_INIT",
                metadata={"name": site.name, "qr_token": site.qr_token}
            )

        # 3. SHIFTS
        print("Creating shifts...")
        shifts_data = [
            {"name": "Morning Patrol (06:00 - 14:00)", "start_time": "06:00", "end_time": "14:00", "grace": 15},
            {"name": "Day Shift (08:00 - 16:00)", "start_time": "08:00", "end_time": "16:00", "grace": 10},
            {"name": "Evening Guard (14:00 - 22:00)", "start_time": "14:00", "end_time": "22:00", "grace": 15},
            {"name": "Overnight Sentinel (22:00 - 06:00)", "start_time": "22:00", "end_time": "06:00", "grace": 10},
        ]

        created_shifts = []
        for sh in shifts_data:
            shift = Shift(
                name=sh["name"],
                start_time=sh["start_time"],
                end_time=sh["end_time"],
                grace_period_minutes=sh["grace"]
            )
            db.add(shift)
            db.commit()
            db.refresh(shift)
            created_shifts.append(shift)
            audit_service.log_event(
                entity_type="SHIFT",
                entity_id=str(shift.id),
                action="SHIFT_CREATED",
                performed_by="SYSTEM_INIT",
                metadata={"name": shift.name, "start": shift.start_time, "end": shift.end_time}
            )

        # 4. ASSIGNMENTS, REALISTIC ATTENDANCE & VIOLATIONS
        print("Generating historical and active assignments across scenarios...")
        today = date.today()
        guards_list = [created_users[f"guard.{i:03d}@security-ops.com"] for i in range(1, 6)]

        # SCENARIO A: Yesterday completed on-time (Guard 1, Site 0, Shift 1)
        asg1 = Assignment(
            user_id=guards_list[0].id,
            site_id=created_sites[0].id,
            shift_id=created_shifts[1].id,
            date=today - timedelta(days=1),
            status=AssignmentStatus.COMPLETED.value
        )
        db.add(asg1)
        db.commit()
        db.refresh(asg1)

        cin1 = AttendanceLog(
            assignment_id=asg1.id,
            type=AttendanceType.CHECK_IN.value,
            timestamp=datetime(today.year, today.month, today.day, 7, 58, tzinfo=timezone.utc) - timedelta(days=1),
            latitude=created_sites[0].latitude + 0.0001,
            longitude=created_sites[0].longitude + 0.0001,
            qr_token=created_sites[0].qr_token,
            is_valid=True
        )
        cout1 = AttendanceLog(
            assignment_id=asg1.id,
            type=AttendanceType.CHECK_OUT.value,
            timestamp=datetime(today.year, today.month, today.day, 16, 2, tzinfo=timezone.utc) - timedelta(days=1),
            is_valid=True
        )
        db.add_all([cin1, cout1])
        db.commit()
        audit_service.log_event(
            entity_type="ATTENDANCE",
            entity_id=str(cin1.id),
            action="CHECK_IN",
            performed_by=guards_list[0].email,
            metadata={"status": "ON_TIME"}
        )

        # SCENARIO B: Yesterday Late Check-in (Guard 2, Site 1, Shift 0)
        asg2 = Assignment(
            user_id=guards_list[1].id,
            site_id=created_sites[1].id,
            shift_id=created_shifts[0].id,
            date=today - timedelta(days=1),
            status=AssignmentStatus.COMPLETED.value,
            compliance_violations=[{"type": "LATE_CHECKIN", "severity": "MEDIUM", "message": "Guard arrived 25 minutes late"}]
        )
        db.add(asg2)
        db.commit()
        db.refresh(asg2)

        cin2 = AttendanceLog(
            assignment_id=asg2.id,
            type=AttendanceType.CHECK_IN.value,
            timestamp=datetime(today.year, today.month, today.day, 6, 25, tzinfo=timezone.utc) - timedelta(days=1),
            latitude=created_sites[1].latitude,
            longitude=created_sites[1].longitude,
            qr_token=created_sites[1].qr_token,
            is_valid=True,
            violation_reason="Late check-in (25m delay)"
        )
        cout2 = AttendanceLog(
            assignment_id=asg2.id,
            type=AttendanceType.CHECK_OUT.value,
            timestamp=datetime(today.year, today.month, today.day, 14, 5, tzinfo=timezone.utc) - timedelta(days=1),
            is_valid=True
        )
        db.add_all([cin2, cout2])
        db.commit()

        exc2 = ComplianceException(
            assignment_id=asg2.id,
            violation_type=ViolationType.LATE_CHECKIN.value,
            severity=ViolationSeverity.MEDIUM.value,
            status=ExceptionStatus.RESOLVED.value,
            detected_at=datetime(today.year, today.month, today.day, 6, 25, tzinfo=timezone.utc) - timedelta(days=1),
            resolved_at=datetime.now(timezone.utc),
            resolved_by="supervisor.jenkins@security-ops.com",
            resolution_notes="Public transport delays verified. Guard completed handover on schedule."
        )
        db.add(exc2)
        db.commit()

        # SCENARIO C: Missed Shift (Guard 3, Site 2, Shift 1)
        asg3 = Assignment(
            user_id=guards_list[2].id,
            site_id=created_sites[2].id,
            shift_id=created_shifts[1].id,
            date=today - timedelta(days=1),
            status=AssignmentStatus.MISSED.value,
            compliance_violations=[{"type": "MISSED_SHIFT", "severity": "CRITICAL", "message": "Guard did not report for shift"}]
        )
        db.add(asg3)
        db.commit()
        db.refresh(asg3)

        exc3 = ComplianceException(
            assignment_id=asg3.id,
            violation_type=ViolationType.MISSED_SHIFT.value,
            severity=ViolationSeverity.CRITICAL.value,
            status=ExceptionStatus.OPEN.value,
            detected_at=datetime(today.year, today.month, today.day, 8, 30, tzinfo=timezone.utc) - timedelta(days=1),
            resolution_notes="Guard unreachable by dispatch supervisor. Investigation ongoing."
        )
        db.add(exc3)
        db.commit()

        # SCENARIO D: GPS Geofence Violation (Guard 4, Site 0, Shift 2)
        asg4 = Assignment(
            user_id=guards_list[3].id,
            site_id=created_sites[0].id,
            shift_id=created_shifts[2].id,
            date=today - timedelta(days=2),
            status=AssignmentStatus.COMPLETED.value,
            compliance_violations=[{"type": "GPS_VIOLATION", "severity": "HIGH", "message": "Guard checked in 850m outside allowed site radius"}]
        )
        db.add(asg4)
        db.commit()
        db.refresh(asg4)

        cin4 = AttendanceLog(
            assignment_id=asg4.id,
            type=AttendanceType.CHECK_IN.value,
            timestamp=datetime(today.year, today.month, today.day, 14, 2, tzinfo=timezone.utc) - timedelta(days=2),
            latitude=created_sites[0].latitude + 0.009,
            longitude=created_sites[0].longitude + 0.008,
            qr_token=created_sites[0].qr_token,
            is_valid=True,
            violation_reason="GPS Geofence Breach (850m away)"
        )
        db.add(cin4)
        db.commit()

        exc4 = ComplianceException(
            assignment_id=asg4.id,
            violation_type=ViolationType.GPS_VIOLATION.value,
            severity=ViolationSeverity.HIGH.value,
            status=ExceptionStatus.OPEN.value,
            detected_at=datetime(today.year, today.month, today.day, 14, 2, tzinfo=timezone.utc) - timedelta(days=2),
            resolution_notes="Device GPS drift reported by officer. Site supervisor reviewing tower logs."
        )
        db.add(exc4)
        db.commit()

        # SCENARIO E: Overtime Violation (Guard 5, Site 0, Shift 1)
        asg5 = Assignment(
            user_id=guards_list[4].id,
            site_id=created_sites[0].id,
            shift_id=created_shifts[1].id,
            date=today - timedelta(days=3),
            status=AssignmentStatus.COMPLETED.value,
            compliance_violations=[{"type": "OVERTIME_VIOLATION", "severity": "MEDIUM", "message": "Unauthorized overtime of 2.5 hours"}]
        )
        db.add(asg5)
        db.commit()
        db.refresh(asg5)

        exc5 = ComplianceException(
            assignment_id=asg5.id,
            violation_type=ViolationType.OVERTIME_VIOLATION.value,
            severity=ViolationSeverity.MEDIUM.value,
            status=ExceptionStatus.RESOLVED.value,
            detected_at=datetime(today.year, today.month, today.day, 18, 30, tzinfo=timezone.utc) - timedelta(days=3),
            resolved_at=datetime.now(timezone.utc),
            resolved_by="admin@security-ops.com",
            resolution_notes="Emergency client executive protection extension approved retroactively."
        )
        db.add(exc5)
        db.commit()

        # ACTIVE TODAY ASSIGNMENTS:
        # Guard 1: Assigned today at Corporate Tower (Scheduled)
        asg_today1 = Assignment(
            user_id=guards_list[0].id,
            site_id=created_sites[0].id,
            shift_id=created_shifts[1].id,
            date=today,
            status=AssignmentStatus.SCHEDULED.value
        )
        # Guard 2: Checked in today at Industrial Port
        asg_today2 = Assignment(
            user_id=guards_list[1].id,
            site_id=created_sites[1].id,
            shift_id=created_shifts[0].id,
            date=today,
            status=AssignmentStatus.CHECKED_IN.value
        )
        db.add_all([asg_today1, asg_today2])
        db.commit()
        db.refresh(asg_today2)

        cin_today2 = AttendanceLog(
            assignment_id=asg_today2.id,
            type=AttendanceType.CHECK_IN.value,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
            latitude=created_sites[1].latitude,
            longitude=created_sites[1].longitude,
            qr_token=created_sites[1].qr_token,
            is_valid=True
        )
        db.add(cin_today2)
        db.commit()

        # Guard 3, 4, 5 scheduled for today
        for idx, g in enumerate(guards_list[2:], start=2):
            asg_t = Assignment(
                user_id=g.id,
                site_id=created_sites[idx % 3].id,
                shift_id=created_shifts[idx % 4].id,
                date=today,
                status=AssignmentStatus.ASSIGNED.value
            )
            db.add(asg_t)
        db.commit()

        # 5. INITIAL NOTIFICATIONS
        notifs = [
            Notification(
                type="MISSED_SHIFT",
                recipient_role="SUPERVISOR",
                title="Critical: Missed Shift at Highland Crest",
                message="Guard 003 did not check in within grace window. Status set to MISSED.",
                data={"assignment_id": asg3.id},
                read=False
            ),
            Notification(
                type="GPS_VIOLATION",
                recipient_role="SUPERVISOR",
                title="Geofence Breach: Corporate Tower Headquarters",
                message="Guard 004 submitted attendance 850m outside allowed site radius.",
                data={"assignment_id": asg4.id},
                read=False
            ),
            Notification(
                type="COMPLIANCE_BREACH",
                recipient_role="ADMIN",
                title="Weekly Labor Audit Summary Available",
                message="Weekly compliance score calculated at 92.4% across 3 active facilities.",
                data={},
                read=True
            )
        ]
        db.add_all(notifs)
        db.commit()

        # 6. INITIAL SEED REPORT
        rep_service = ReportService(db)
        rep_service.save_report(
            site_id=created_sites[0].id,
            start_date=today - timedelta(days=7),
            end_date=today,
            generated_by="System Initializer",
            report_type=ReportType.COMPLIANCE
        )

        # 7. Update site scores
        comp_engine = ComplianceEngine(db)
        for s in created_sites:
            s.compliance_score = comp_engine.calculate_site_compliance_score(s.id)
            db.commit()

        # Audit initial integrity
        integrity = audit_service.verify_integrity()
        print(f"Database seeded successfully! Audit chain verified: {integrity['records_checked']} records, valid: {integrity['valid']}.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
