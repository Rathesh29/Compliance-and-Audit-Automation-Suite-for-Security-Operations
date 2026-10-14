from datetime import date, timedelta


def test_valid_assignment_creation(client, supervisor_headers, db_session):
    from app.models.user import User
    from app.models.site import Site
    from app.models.shift import Shift

    guard = db_session.query(User).filter(User.role == "GUARD").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    target_date = str(date.today() + timedelta(days=10))

    res = client.post("/api/assignments", headers=supervisor_headers, json={
        "user_id": guard.id,
        "site_id": site.id,
        "shift_id": shift.id,
        "date": target_date
    })
    assert res.status_code == 201
    assert res.json()["data"]["status"] == "SCHEDULED"


def test_duplicate_same_shift_assignment_rejected(client, supervisor_headers, db_session):
    from app.models.user import User
    from app.models.site import Site
    from app.models.shift import Shift

    guard = db_session.query(User).filter(User.role == "GUARD").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    target_date = str(date.today() + timedelta(days=11))

    # First assignment
    client.post("/api/assignments", headers=supervisor_headers, json={
        "user_id": guard.id,
        "site_id": site.id,
        "shift_id": shift.id,
        "date": target_date
    })

    # Duplicate attempt
    res = client.post("/api/assignments", headers=supervisor_headers, json={
        "user_id": guard.id,
        "site_id": site.id,
        "shift_id": shift.id,
        "date": target_date
    })
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "COMPLIANCE_VIOLATION"


def test_admin_override_on_assignment(client, supervisor_headers, db_session):
    from app.models.user import User
    from app.models.site import Site
    from app.models.shift import Shift

    guard = db_session.query(User).filter(User.role == "GUARD").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    target_date = str(date.today() + timedelta(days=12))

    # First assignment
    client.post("/api/assignments", headers=supervisor_headers, json={
        "user_id": guard.id,
        "site_id": site.id,
        "shift_id": shift.id,
        "date": target_date
    })

    # Override attempt
    res = client.post("/api/assignments", headers=supervisor_headers, json={
        "user_id": guard.id,
        "site_id": site.id,
        "shift_id": shift.id,
        "date": target_date,
        "override_violations": True,
        "override_reason": "Emergency operational shortage override by supervisor"
    })
    assert res.status_code == 201
