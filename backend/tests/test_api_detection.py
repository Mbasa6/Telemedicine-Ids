import io


def test_run_detection_fails_without_trained_models(client, admin_headers, monkeypatch):
    import app.routers.detection as detection_module
    monkeypatch.setattr(detection_module, "RF_PATH", "/nonexistent/rf.joblib")
    monkeypatch.setattr(detection_module, "IF_PATH", "/nonexistent/if.joblib")
    resp = client.post("/detection/run", headers=admin_headers)
    assert resp.status_code in (409, 200)  # 200 only if there are no new events to process


def test_only_admin_can_train_models(client, analyst_headers):
    resp = client.post("/detection/train", headers=analyst_headers)
    assert resp.status_code == 403


def test_train_models_and_get_evaluation(client, admin_headers):
    resp = client.post("/detection/train", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "random_forest" in data
    assert "isolation_forest" in data
    assert data["random_forest"]["train_size"] > 0

    eval_resp = client.get("/detection/evaluation", headers=admin_headers)
    assert eval_resp.status_code == 200


def test_run_detection_after_training(client, admin_headers, analyst_headers):
    csv_content = (
        "timestamp,source_ip,destination_ip,user_id,login_attempts,failed_login_attempts,"
        "request_frequency,session_duration,data_transfer_volume,access_type,device_information,geo_location,attack_label\n"
        "2026-01-02 02:00:00,41.0.0.9,10.0.0.1,patient_9,20,18,150,20,9000,admin_console,linux,Durban,\n"
    )
    client.post(
        "/events/upload",
        files={"file": ("det.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=analyst_headers,
    )
    resp = client.post("/detection/run", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["events_processed"] >= 1


def test_list_detection_results(client, admin_headers):
    resp = client.get("/detection/results", headers=admin_headers)
    assert resp.status_code == 200
