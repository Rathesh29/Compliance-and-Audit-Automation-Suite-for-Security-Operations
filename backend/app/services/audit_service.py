from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.repositories.audit_repo import AuditRepository
from app.core.security import calculate_audit_hash, GENESIS_HASH
from app.core.logging_config import logger


def format_canonical_timestamp(dt: Any) -> str:
    """Canonical timestamp representation for deterministic cryptographic hashing."""
    if isinstance(dt, str):
        return dt[:19].replace(" ", "T")
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log_event(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        performed_by: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Appends an immutable audit log record to the tamper-evident hash chain.
        """
        now = datetime.now(timezone.utc)
        canonical_ts = format_canonical_timestamp(now)

        # Find the preceding record hash
        latest_record = self.repo.get_latest()
        previous_hash = latest_record.record_hash if latest_record else GENESIS_HASH

        # Calculate cryptographically chained SHA-256
        record_hash = calculate_audit_hash(
            previous_hash=previous_hash,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            performed_by=performed_by,
            timestamp=canonical_ts,
            metadata=metadata or {}
        )

        audit_entry = AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            performed_by=performed_by,
            timestamp=now,
            extra_metadata=metadata or {},
            previous_hash=previous_hash,
            record_hash=record_hash
        )

        saved = self.repo.append(audit_entry)
        logger.info(
            f"Audit log appended: {action} on {entity_type}#{entity_id} by {performed_by} [hash={record_hash[:12]}...]",
            extra={"props": {"action": action, "entity_type": entity_type, "performed_by": performed_by}}
        )
        return saved

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Performs full mathematical verification of the SHA-256 audit hash chain.
        Traverses records in ascending order, verifying both local hash calculation
        and parent pointer chaining.
        """
        records = self.repo.get_all_ordered()
        if not records:
            return {
                "valid": True,
                "records_checked": 0,
                "tampered_records": [],
                "genesis_valid": True,
                "chain_head": GENESIS_HASH
            }

        expected_previous_hash = GENESIS_HASH
        tampered_ids: List[int] = []

        for record in records:
            # Check 1: Does previous_hash match the previous record's hash?
            if record.previous_hash != expected_previous_hash:
                tampered_ids.append(record.id)
                logger.error(f"Audit chain broken at record #{record.id}: previous_hash mismatch! Expected {expected_previous_hash}, got {record.previous_hash}")

            # Check 2: Does recalculating the record's hash match record_hash?
            canonical_ts = format_canonical_timestamp(record.timestamp)
            recalc_hash = calculate_audit_hash(
                previous_hash=record.previous_hash,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                action=record.action,
                performed_by=record.performed_by,
                timestamp=canonical_ts,
                metadata=record.extra_metadata or {}
            )

            if recalc_hash != record.record_hash:
                if record.id not in tampered_ids:
                    tampered_ids.append(record.id)
                logger.error(f"Audit record #{record.id} altered! Hash mismatch. Computed {recalc_hash}, stored {record.record_hash}")

            # Advance expected hash for next link
            expected_previous_hash = record.record_hash

        is_valid = len(tampered_ids) == 0
        return {
            "valid": is_valid,
            "records_checked": len(records),
            "tampered_records": tampered_ids,
            "genesis_valid": True,
            "chain_head": records[-1].record_hash if records else GENESIS_HASH
        }
