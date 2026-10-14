from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.user import User
from app.models.site import Site
from app.models.shift import Shift
from app.models.compliance import ComplianceException
from app.models.enums import AssignmentStatus, ExceptionStatus, ViolationSeverity
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.user_repo import UserRepository
from app.repositories.site_repo import SiteRepository
from app.repositories.shift_repo import ShiftRepository
from app.repositories.compliance_repo import ComplianceRepository
from app.services.compliance_engine import ComplianceEngine
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssignmentRepository(db)
        self.user_repo = UserRepository(db)
        self.site_repo = SiteRepository(db)
        self.shift_repo = ShiftRepository(db)
        self.comp_repo = ComplianceRepository(db)
        self.compliance_engine = ComplianceEngine(db)
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    def get_assignment(self, assignment_id: int) -> Optional[Assignment]:
        return self.repo.get_by_id(assignment_id)

    def list_assignments(
        self,
        site_id: Optional[int] = None,
        user_id: Optional[int] = None,
        assignment_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> List[Assignment]:
        return self.repo.list_assignments(
            site_id=site_id,
            user_id=user_id,
            assignment_date=assignment_date,
            status=status
        )

    def validate_proposed_assignment(
        self,
        user_id: int,
        site_id: int,
        shift_id: int,
        assignment_date: date
    ) -> Dict[str, Any]:
        """Pre-check compliance before creation without persisting."""
        guard = self.user_repo.get_by_id(user_id)
        if not guard:
            raise ValueError(f"Guard #{user_id} not found")
        site = self.site_repo.get_by_id(site_id)
        if not site:
            raise ValueError(f"Site #{site_id} not found")
        shift = self.shift_repo.get_by_id(shift_id)
        if not shift:
            raise ValueError(f"Shift #{shift_id} not found")

        violations = self.compliance_engine.evaluate_assignment_creation(
            guard=guard,
            site=site,
            shift=shift,
            assignment_date=assignment_date
        )

        return {
            "compliant": len(violations) == 0,
            "violations": [v.to_dict() for v in violations]
        }

    def create_assignment(self, payload: AssignmentCreate, performed_by: str) -> Tuple[Optional[Assignment], Optional[Dict[str, Any]]]:
        """
        Creates an assignment. Automatically runs compliance engine.
        If non-compliant and override_violations is False, rejects and returns violations.
        If overridden, records ADMIN_OVERRIDE audit event with mandatory reason.
        """
        guard = self.user_repo.get_by_id(payload.user_id)
        if not guard:
            raise ValueError(f"Guard #{payload.user_id} not found")
        site = self.site_repo.get_by_id(payload.site_id)
        if not site:
            raise ValueError(f"Site #{payload.site_id} not found")
        shift = self.shift_repo.get_by_id(payload.shift_id)
        if not shift:
            raise ValueError(f"Shift #{payload.shift_id} not found")

        violations = self.compliance_engine.evaluate_assignment_creation(
            guard=guard,
            site=site,
            shift=shift,
            assignment_date=payload.date
        )

        violation_dicts = [v.to_dict() for v in violations]

        if violation_dicts and not payload.override_violations:
            # Audit rejected attempt
            self.audit.log_event(
                entity_type="ASSIGNMENT",
                entity_id="0",
                action="ASSIGNMENT_REJECTED",
                performed_by=performed_by,
                metadata={
                    "guard": guard.email,
                    "site": site.name,
                    "violations": violation_dicts
                }
            )
            return None, {
                "compliant": False,
                "violations": violation_dicts,
                "message": "Assignment violates compliance rules. Override required."
            }

        # Build assignment
        assignment = Assignment(
            user_id=payload.user_id,
            site_id=payload.site_id,
            shift_id=payload.shift_id,
            date=payload.date,
            status=AssignmentStatus.SCHEDULED.value,
            compliance_violations=violation_dicts
        )
        saved = self.repo.create(assignment)

        # Audit creation
        self.audit.log_event(
            entity_type="ASSIGNMENT",
            entity_id=str(saved.id),
            action="ASSIGNMENT_CREATED",
            performed_by=performed_by,
            metadata={
                "guard_email": guard.email,
                "site_name": site.name,
                "shift_name": shift.name,
                "date": str(payload.date),
                "has_violations": len(violation_dicts) > 0
            }
        )

        # Handle override audit & compliance exceptions if violations were overridden
        if violation_dicts and payload.override_violations:
            self.audit.log_event(
                entity_type="ASSIGNMENT",
                entity_id=str(saved.id),
                action="ADMIN_OVERRIDE",
                performed_by=performed_by,
                metadata={
                    "reason": payload.override_reason or "Operational supervisor override",
                    "violations": violation_dicts
                }
            )
            for v in violations:
                exc = ComplianceException(
                    assignment_id=saved.id,
                    violation_type=v.type,
                    severity=v.severity,
                    status=ExceptionStatus.OPEN.value,
                    resolution_notes=f"Overridden by {performed_by}: {payload.override_reason or 'No note'}"
                )
                self.comp_repo.create(exc)

            self.notification.send_notification(
                notif_type="COMPLIANCE_BREACH",
                title=f"Override on Assignment #{saved.id}",
                message=f"Assignment for {guard.name} was approved with override: {payload.override_reason}",
                recipient_role="ADMIN",
                data={"assignment_id": saved.id, "violations": violation_dicts}
            )

        return saved, None

    def update_assignment_status(self, assignment_id: int, new_status: AssignmentStatus, performed_by: str) -> Assignment:
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        old_status = assignment.status
        assignment.status = new_status.value if hasattr(new_status, "value") else str(new_status)
        updated = self.repo.update(assignment)

        self.audit.log_event(
            entity_type="ASSIGNMENT",
            entity_id=str(updated.id),
            action="ASSIGNMENT_UPDATED",
            performed_by=performed_by,
            metadata={"old_status": old_status, "new_status": updated.status}
        )
        return updated
