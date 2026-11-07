import io

SAMPLE_CSV = (
    "timestamp,source_ip,destination_ip,user_id,login_attempts,failed_login_attempts,"
    "request_frequency,session_duration,data_transfer_volume,access_type,device_information,geo_location,attack_label\n"
    "2026-01-01 08:00:00,41.0.0.1,10.0.0.1,patient_1,2,0,5,320,120,web_portal,windows_pc,Pretoria,normal\n"
    "2026-01-01 08:05:00,41.0.0.2,10.0.0.1,patient_2,15,12,120,30,5000,api,linux,Cape Town,brute_force\n"
    "invalid_row_with_missing_fields,,,,,,,,,,,,\n"
)


def test_upload_csv_events(client, analyst_headers):
    files = {"file": ("sample.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    resp = client.post("/events/upload", files=files, headers=analyst_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == 3
    assert body["valid_rows"] == 2
    assert body["invalid_rows"] == 1
    assert len(body["errors"]) >= 1


def test_upload_rejects_non_csv(client, analyst_headers):
    files = {"file": ("sample.txt", io.BytesIO(b"not a csv"), "text/plain")}
    resp = client.post("/events/upload", files=files, headers=analyst_headers)
    assert resp.status_code == 400


def test_list_events_requires_auth(client):
    resp = client.get("/events")
    assert resp.status_code == 401


def test_list_events(client, admin_headers):
    resp = client.get("/events", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
