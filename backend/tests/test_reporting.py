from datetime import date, timedelta


def test_generate_and_export_reports(client, auditor_headers):
    today = date.today()
    start_date = str(today - timedelta(days=7))
    end_date = str(today)

    # 1. Generate Report
    res = client.post("/api/reports/generate", headers=auditor_headers, json={
        "date_range_start": start_date,
        "date_range_end": end_date,
        "report_type": "COMPLIANCE"
    })
    assert res.status_code == 201
    report_id = res.json()["data"]["id"]

    # 2. Export CSV
    res_csv = client.get(f"/api/reports/{report_id}/csv", headers=auditor_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "REPORT_ID" in res_csv.text

    # 3. Export PDF
    res_pdf = client.get(f"/api/reports/{report_id}/pdf", headers=auditor_headers)
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert res_pdf.content.startswith(b"%PDF")
