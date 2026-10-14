def test_admin_can_create_user(client, admin_headers):
    res = client.post("/api/users", headers=admin_headers, json={
        "name": "New Recruited Guard",
        "email": "recruit.guard@ops.com",
        "password": "Password123!",
        "role": "GUARD"
    })
    assert res.status_code == 201
    assert res.json()["data"]["email"] == "recruit.guard@ops.com"


def test_supervisor_forbidden_to_create_user(client, supervisor_headers):
    res = client.post("/api/users", headers=supervisor_headers, json={
        "name": "Should Fail",
        "email": "fail@ops.com",
        "password": "Password123!",
        "role": "GUARD"
    })
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_auditor_forbidden_to_create_site(client, auditor_headers):
    res = client.post("/api/sites", headers=auditor_headers, json={
        "name": "Unauthorized Site",
        "location_name": "Somewhere",
        "latitude": 37.0,
        "longitude": -122.0
    })
    assert res.status_code == 403


def test_guard_cannot_inspect_other_guards(client, guard_headers, db_session):
    from app.models.user import User
    other = db_session.query(User).filter(User.email == "other_guard@ops.com").first()
    res = client.get(f"/api/users/{other.id}", headers=guard_headers)
    assert res.status_code == 403
