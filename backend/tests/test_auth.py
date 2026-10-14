def test_successful_login(client, seed_test_data):
    res = client.post("/api/auth/login", json={"email": "test_admin@ops.com", "password": "TestPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["access_token"] != ""
    assert data["data"]["role"] == "ADMIN"


def test_invalid_password_login(client, seed_test_data):
    res = client.post("/api/auth/login", json={"email": "test_admin@ops.com", "password": "WrongPassword"})
    assert res.status_code == 401
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "LOGIN_FAILED"


def test_nonexistent_user_login(client):
    res = client.post("/api/auth/login", json={"email": "nobody@ops.com", "password": "password"})
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_mfa_flow(client, admin_headers, db_session):
    # Setup MFA
    res = client.post("/api/auth/mfa/setup", headers=admin_headers)
    assert res.status_code == 200
    mfa_data = res.json()["data"]
    assert "secret" in mfa_data
    assert "qr_code_base64" in mfa_data

    # Login now flags MFA required
    res_login = client.post("/api/auth/login", json={"email": "test_admin@ops.com", "password": "TestPass123!"})
    assert res_login.status_code == 200
    assert res_login.json()["data"]["mfa_required"] is True

    # Complete with code
    user_id = res_login.json()["data"]["user_id"]
    res_mfa = client.post("/api/auth/mfa", json={"user_id": user_id, "code": "123456"})
    assert res_mfa.status_code == 200
    assert res_mfa.json()["data"]["access_token"] != ""
