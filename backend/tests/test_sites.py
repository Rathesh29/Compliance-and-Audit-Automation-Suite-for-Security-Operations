def test_create_and_fetch_site(client, admin_headers):
    res = client.post("/api/sites", headers=admin_headers, json={
        "name": "Delta Logistics Hub",
        "location_name": "Terminal 9",
        "latitude": 37.8044,
        "longitude": -122.2712,
        "radius_meters": 180.0
    })
    assert res.status_code == 201
    site_id = res.json()["data"]["id"]

    # Fetch site
    res_get = client.get(f"/api/sites/{site_id}", headers=admin_headers)
    assert res_get.status_code == 200
    assert res_get.json()["data"]["name"] == "Delta Logistics Hub"


def test_site_qr_code_generation(client, admin_headers, db_session):
    from app.models.site import Site
    site = db_session.query(Site).first()
    res = client.get(f"/api/sites/{site.id}/qr", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "qr_code_base64" in data
    assert data["qr_code_base64"].startswith("data:image/png;base64,")


def test_site_compliance_score(client, admin_headers, db_session):
    from app.models.site import Site
    site = db_session.query(Site).first()
    res = client.get(f"/api/sites/{site.id}/compliance-score", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["compliance_score"] >= 0.0
