from datetime import date, timedelta
from app.models.user import User
from app.models.site import Site
from app.models.shift import Shift
from app.models.assignment import Assignment


def test_guard_valid_checkin_and_checkout(client, guard_headers, supervisor_headers, db_session):
    guard = db_session.query(User).filter(User.email == "test_guard@ops.com").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    target_date = date.today()

    # Create assignment
    asg = Assignment(user_id=guard.id, site_id=site.id, shift_id=shift.id, date=target_date, status="SCHEDULED")
    db_session.add(asg)
    db_session.commit()
    db_session.refresh(asg)

    # 1. Valid Check-in
    res_in = client.post("/api/attendance/check-in", headers=guard_headers, json={
        "assignment_id": asg.id,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "qr_token": site.qr_token
    })
    assert res_in.status_code == 200
    assert res_in.json()["data"]["assignment"]["status"] == "CHECKED_IN"

    # 2. Valid Check-out
    res_out = client.post("/api/attendance/check-out", headers=guard_headers, json={
        "assignment_id": asg.id,
        "latitude": site.latitude,
        "longitude": site.longitude
    })
    assert res_out.status_code == 200
    assert res_out.json()["data"]["assignment"]["status"] == "COMPLETED"


def test_invalid_qr_code_rejected(client, guard_headers, db_session):
    guard = db_session.query(User).filter(User.email == "test_guard@ops.com").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    asg = Assignment(user_id=guard.id, site_id=site.id, shift_id=shift.id, date=date.today(), status="SCHEDULED")
    db_session.add(asg)
    db_session.commit()

    res = client.post("/api/attendance/check-in", headers=guard_headers, json={
        "assignment_id": asg.id,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "qr_token": "FORGED-QR-TOKEN-INVALID"
    })
    assert res.status_code == 400
    assert "Invalid or tampered Site QR Code" in res.json()["error"]["message"]


def test_guard_cannot_checkin_other_guards_assignment(client, guard_headers, db_session):
    other = db_session.query(User).filter(User.email == "other_guard@ops.com").first()
    site = db_session.query(Site).first()
    shift = db_session.query(Shift).first()

    asg = Assignment(user_id=other.id, site_id=site.id, shift_id=shift.id, date=date.today(), status="SCHEDULED")
    db_session.add(asg)
    db_session.commit()

    # Logged-in as test_guard, trying to check into other_guard's assignment
    res = client.post("/api/attendance/check-in", headers=guard_headers, json={
        "assignment_id": asg.id,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "qr_token": site.qr_token
    })
    assert res.status_code == 400
    assert "Forbidden" in res.json()["error"]["message"]
