def test_list_alerts(client, admin_headers):
    resp = client.get("/alerts", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_filter_alerts_by_severity(client, admin_headers):
    resp = client.get("/alerts", params={"severity": "critical"}, headers=admin_headers)
    assert resp.status_code == 200
    for alert in resp.json():
        assert alert["severity"] == "critical"


def test_acknowledge_alert_if_any_exist(client, admin_headers):
    alerts = client.get("/alerts", headers=admin_headers).json()
    if not alerts:
        return
    alert_id = alerts[0]["id"]
    resp = client.post(f"/alerts/{alert_id}/acknowledge", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"


def test_acknowledge_nonexistent_alert(client, admin_headers):
    resp = client.post("/alerts/999999/acknowledge", headers=admin_headers)
    assert resp.status_code == 404


def test_escalate_alert_creates_incident(client, admin_headers):
    alerts = client.get("/alerts", headers=admin_headers).json()
    unescalated = [a for a in alerts if a["status"] != "escalated"]
    if not unescalated:
        return
    alert_id = unescalated[0]["id"]
    resp = client.post(f"/alerts/{alert_id}/escalate", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["alert_id"] == alert_id
