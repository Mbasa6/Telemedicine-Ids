def test_report_summary(client, admin_headers):
    resp = client.get("/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "severity_distribution" in data


def test_export_csv(client, admin_headers):
    resp = client.get("/reports/export/csv", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")


def test_export_pdf(client, admin_headers):
    resp = client.get("/reports/export/pdf", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_audit_log_requires_admin(client, analyst_headers):
    resp = client.get("/reports/audit", headers=analyst_headers)
    assert resp.status_code == 403


def test_audit_log_as_admin(client, admin_headers):
    resp = client.get("/reports/audit", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0
