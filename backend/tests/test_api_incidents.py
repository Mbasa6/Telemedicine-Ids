def test_list_incidents(client, admin_headers):
    resp = client.get("/incidents", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_update_incident_status_if_any_exist(client, admin_headers):
    incidents = client.get("/incidents", headers=admin_headers).json()
    if not incidents:
        return
    incident_id = incidents[0]["id"]
    resp = client.put(f"/incidents/{incident_id}/status", json={"status": "investigating"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"


def test_update_incident_invalid_status(client, admin_headers):
    incidents = client.get("/incidents", headers=admin_headers).json()
    if not incidents:
        return
    incident_id = incidents[0]["id"]
    resp = client.put(f"/incidents/{incident_id}/status", json={"status": "not_a_real_status"}, headers=admin_headers)
    assert resp.status_code == 400


def test_add_note_to_incident_if_any_exist(client, admin_headers):
    incidents = client.get("/incidents", headers=admin_headers).json()
    if not incidents:
        return
    incident_id = incidents[0]["id"]
    resp = client.post(
        f"/incidents/{incident_id}/notes", json={"note": "Investigated source IP, appears malicious."},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert any("Investigated source IP" in n["note"] for n in resp.json()["notes"])


def test_update_nonexistent_incident(client, admin_headers):
    resp = client.put("/incidents/999999/status", json={"status": "open"}, headers=admin_headers)
    assert resp.status_code == 404
