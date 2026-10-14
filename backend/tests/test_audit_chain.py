from app.services.audit_service import AuditService
from app.models.audit import AuditLog


def test_audit_log_creation_and_integrity(client, auditor_headers, db_session):
    audit_service = AuditService(db_session)

    # Append test events
    l1 = audit_service.log_event("TEST_ENTITY", "101", "ACTION_ALPHA", "test_user@ops.com", {"k": "v1"})
    l2 = audit_service.log_event("TEST_ENTITY", "102", "ACTION_BETA", "test_user@ops.com", {"k": "v2"})

    assert l2.previous_hash == l1.record_hash

    # Verify integrity via API
    res = client.get("/api/audit/integrity", headers=auditor_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["valid"] is True
    assert len(data["tampered_records"]) == 0


def test_audit_tamper_detection(client, auditor_headers, db_session):
    audit_service = AuditService(db_session)
    log = audit_service.log_event("PAYLOAD_ENTITY", "201", "CRITICAL_ACTION", "system", {"amount": 5000})

    # Tamper with the database row directly
    log.performed_by = "attacker@malicious.com"
    db_session.commit()

    # Re-verify integrity - must catch tampering
    verification = audit_service.verify_integrity()
    assert verification["valid"] is False
    assert log.id in verification["tampered_records"]
