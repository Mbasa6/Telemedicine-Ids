# Testing Report

All results in this report were obtained by executing the automated test suite, the model
training/evaluation pipeline, and the running backend/frontend processes on **2026-11-07**,
against **Python 3.15.0** on Windows. See [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md)
for the REQ-00X → test mapping referenced throughout.

## 1. Environment

| Item | Value |
|---|---|
| Python | 3.15.0 |
| pytest | 9.2.0 (+ pytest-asyncio 1.4.1.post1, httpx 0.28.1) |
| FastAPI / Uvicorn | 0.162.1 / 0.54.0 |
| SQLAlchemy | 2.1.8 |
| scikit-learn / pandas / numpy | 1.9.1 / 3.1.1 / 2.5.4 |
| passlib / bcrypt | 1.7.4 / 4.0.1 (pinned `bcrypt<4.1`, see §4) |
| Database | SQLite, file-based (`backend/telemedicine_ids.db`) |

No Python 3.15 compatibility issues were found during dependency installation — every package had
a prebuilt `cp315` wheel available, so a downgrade to Python 3.12/3.13 was not necessary.

## 2. Automated test suite results

Command: `pytest -v` run from `backend/`.

**Result: 51 passed, 0 failed, 93 warnings in 21.90s.**

All 93 warnings are cosmetic deprecation notices (not test failures): `datetime.utcnow()`
deprecated (`security.py`, `evaluate.py`, SQLAlchemy internals), fpdf2's `ln=True` parameter
deprecated (`reports.py`), FastAPI `on_event` deprecated (`main.py`), and pandas
`Timestamp.utcnow()` deprecated.

### Test breakdown by file

| File | Tests | Result | Covers |
|---|---|---|---|
| `test_api_auth.py` | 7 | ✅ all passed | login, `/auth/me`, role-gated user creation, logout |
| `test_api_auth_httpx.py` | 3 | ✅ all passed | invalid-credential login, `/health`, `/` via httpx client |
| `test_api_events.py` | 4 | ✅ all passed | CSV upload/validation, event listing, auth enforcement |
| `test_api_detection.py` | 5 | ✅ all passed | training (admin-only), evaluation retrieval, running detection, result listing |
| `test_api_alerts.py` | 5 | ✅ all passed | listing/filtering, acknowledge, escalate-to-incident |
| `test_api_incidents.py` | 5 | ✅ all passed | listing, status update + validation, incident notes |
| `test_api_reports.py` | 5 | ✅ all passed | summary, CSV export, PDF export, audit log (admin-only) |
| `test_integration.py` | 2 | ✅ all passed | ORM relationship persistence, audit log creation on login |
| `test_ml_models.py` | 4 | ✅ all passed | Random Forest train/predict/persist, Isolation Forest scoring, untrained-model guards |
| `test_preprocessing.py` | 5 | ✅ all passed | CSV validation/normalisation (valid rows, missing columns, invalid values, missing IP), feature extraction shape |
| `test_risk_scoring.py` | 6 | ✅ all passed | hybrid risk score bounds/weights/clamping, severity thresholds, asset criticality, frequency normalisation |
| **Total** | **51** | **51 passed, 0 failed** | |

### Test ID reference (TC-XXX, as cited in REQUIREMENTS_TRACEABILITY.md)

Each individual TC-XXX identifier maps 1:1 to a specific automated `def test_...` function in
`backend/tests/`. A range (e.g. `TC-AUTH-01..07`) denotes a sequential group of individually-numbered
test functions within that file, listed in file order below — it is not a single test.

| Test ID | File | Test function |
|---|---|---|
| TC-AUTH-01..07 | `test_api_auth.py` | `test_login_success_and_me`, `test_login_invalid_password`, `test_login_unknown_user`, `test_protected_endpoint_requires_auth`, `test_only_admin_can_create_users`, `test_admin_can_create_user`, `test_logout` |
| TC-AUTHX-01..03 | `test_api_auth_httpx.py` | `test_login_invalid_credentials_httpx` (REQ-005), `test_health_endpoint_httpx`, `test_root_endpoint_httpx` (latter two are httpx-based infra smoke tests; not mapped to a specific REQ-00X) |
| TC-EVT-01..04 | `test_api_events.py` | `test_upload_csv_events`, `test_upload_rejects_non_csv`, `test_list_events_requires_auth`, `test_list_events` |
| TC-DET-01..05 | `test_api_detection.py` | `test_run_detection_fails_without_trained_models`, `test_only_admin_can_train_models`, `test_train_models_and_get_evaluation`, `test_run_detection_after_training`, `test_list_detection_results` |
| TC-ALR-01..05 | `test_api_alerts.py` | `test_list_alerts`, `test_filter_alerts_by_severity`, `test_acknowledge_alert_if_any_exist`, `test_acknowledge_nonexistent_alert`, `test_escalate_alert_creates_incident` |
| TC-INC-01..05 | `test_api_incidents.py` | `test_list_incidents`, `test_update_incident_status_if_any_exist`, `test_update_incident_invalid_status`, `test_add_note_to_incident_if_any_exist`, `test_update_nonexistent_incident` |
| TC-RPT-01..05 | `test_api_reports.py` | `test_report_summary`, `test_export_csv`, `test_export_pdf`, `test_audit_log_requires_admin`, `test_audit_log_as_admin` |
| TC-INT-01..02 | `test_integration.py` | `test_security_event_persists_with_relationships`, `test_audit_log_created_on_login` |
| TC-ML-01..04 | `test_ml_models.py` | `test_random_forest_train_predict_persist`, `test_random_forest_raises_when_not_trained`, `test_isolation_forest_scores_in_range`, `test_isolation_forest_raises_when_not_trained` |
| TC-PRE-01..05 | `test_preprocessing.py` | `test_validate_and_normalize_accepts_valid_rows`, `test_validate_and_normalize_flags_missing_required_columns`, `test_validate_and_normalize_flags_invalid_numeric_value`, `test_validate_and_normalize_flags_missing_ip`, `test_extract_features_shape` |
| TC-RSK-01..06 | `test_risk_scoring.py` | `test_compute_risk_score_bounds`, `test_compute_risk_score_weights`, `test_compute_risk_score_clamps_out_of_range_inputs`, `test_classify_severity_thresholds`, `test_asset_criticality_known_and_unknown`, `test_normalize_frequency_clamped` |

## 3. AI model evaluation results (real, from `backend/ml_models/evaluation_results.json`)

Trained against the full 3000-row synthetic dataset
(`backend/data/synthetic_telemedicine_events.csv`), 70/30 stratified split.

### Random Forest (supervised, attack vs. normal classification)

| Metric | Value |
|---|---|
| Accuracy | 0.9967 |
| Precision | 1.0 |
| Recall | 0.9885 |
| F1 score | 0.9942 |
| False positive rate | 0.0 |
| Confusion matrix (`normal(0)` / `attack(1)`) | `[[638, 0], [3, 259]]` |
| Average prediction latency | 0.052 ms/sample |
| Train / test size | 2100 / 900 |

Interpretation: 3 attack events were misclassified as normal (false negatives) out of 262 actual
attacks in the test split; zero normal events were misclassified as attacks.

### Isolation Forest (unsupervised anomaly detection)

| Metric | Value |
|---|---|
| Trained on normal-only rows | 1490 |
| Mean anomaly score — normal test rows | 0.409 |
| Mean anomaly score — attack test rows | 0.7816 |
| Flagged rate (test set) | 0.4844 |

Isolation Forest is unsupervised and trained only on normal-labelled data; the metrics above
describe score separation between the known classes for evaluation purposes, and reflect the
model identifying deviations from learned normal behaviour rather than a guarantee of flagging
every unknown attack type.

Model artifacts confirmed present on disk: `backend/ml_models/random_forest_model.joblib`,
`backend/ml_models/isolation_forest_model.joblib`, `backend/ml_models/evaluation_results.json`.

## 4. Defects found and fixed during verification

| # | Defect | Root cause | Fix |
|---|---|---|---|
| 1 | `generate_synthetic_data.py` crashed with `pandas.errors.LossySetitemError` | pandas 3.x disallows assigning string/empty values into an `int64`/typed column without first widening the dtype | Cast affected columns (`login_attempts`, `failed_login_attempts`, `source_ip`) to `object` dtype before injecting intentionally-invalid demo rows |
| 2 | ALL 51 tests failed with `PermissionError: [WinError 32]` on `os.remove(TEST_DB_PATH)` in `conftest.py` | A second SQLAlchemy engine (`app.database.engine`, created at import time via `app/main.py`'s `Base.metadata.create_all`) also pointed at the test DB path via the `DATABASE_URL` env override, and was never disposed, keeping a pooled connection that locks the file on Windows | Dispose **both** `engine` (conftest's) and `database.engine` (the app's) before `os.remove`, at both session start and teardown |
| 3 | `test_security_event_persists_with_relationships` failed with a SQLite `DateTime` type error | A raw datetime string was passed into a SQLAlchemy `DateTime` column; SQLite's dialect strictly rejects strings | Use an actual `datetime(2026, 1, 3, 10, 0, 0)` object instead of a string |
| 4 | Many auth-related API tests failed with `ValueError: password cannot be longer than 72 bytes` even for short passwords | passlib 1.7.4's internal bcrypt truncation-detection self-test is incompatible with bcrypt ≥ 4.1's stricter 72-byte enforcement | Pinned `bcrypt<4.1` in `requirements.txt`; installed version downgraded from 5.0.0 → 4.0.1 |
| 5 | `test_preprocessing.py`'s invalid-numeric-value test hit the same pandas lossy-setitem error as #1 | Same pandas 3.x dtype-widening restriction, in test code this time | Cast `login_attempts` to `object` dtype before assigning `"not_a_number"` |
| 6 | Production SQLite DB file was created in the wrong directory (a sibling VS Code workspace folder) on first backend smoke-test launch | `uvicorn --app-dir backend` only changes Python's import path, not the OS process's working directory; the relative `DATABASE_URL` (`sqlite:///./telemedicine_ids.db`) resolved against the actual shell cwd at launch time, which had not been changed | Launch uvicorn via `cmd /c "cd /d <backend_path> && ..."` to set the real process working directory before starting the server; stray file deleted |

After fixes 1–5, the full suite passed 51/51 with zero remaining functional failures. Defect 6 was
found and fixed during backend runtime smoke-testing (not part of the pytest suite, which uses an
isolated test database path and was unaffected).

## 5. Runtime smoke tests (live HTTP verification)

Backend (`uvicorn`, port 8000, launched from `backend/` as the working directory):

| Check | Result |
|---|---|
| `GET /` | `200 OK` — `{"service": "Telemedicine AI-IDS", "status": "running"}` |
| `GET /health` | `200 OK` — `{"status": "ok"}` |
| `POST /auth/login` (valid demo administrator credentials) | `200 OK` — real JWT `access_token` returned |
| Database file location | Confirmed created at `backend/telemedicine_ids.db` (98,304 bytes) after the working-directory fix (defect #6) |

Frontend (`streamlit run streamlit_app.py --server.headless true`, port 8501):

| Check | Result |
|---|---|
| `GET http://localhost:8501` | `200 OK` |
| Startup log | Process started with no errors reported; exact console output was not captured for this run |

## 6. Summary

- **51/51 automated tests passing** (0 failures) across authentication, event ingestion, detection,
  alerts, incidents, reports, ML models, preprocessing, risk scoring, and integration test files.
- **Real AI model metrics recorded**: Random Forest 99.67% accuracy / 100% precision / 98.85% recall
  on held-out test data; Isolation Forest shows clear anomaly-score separation between normal and
  attack test rows (0.409 vs 0.7816 mean score).
- **6 real defects found and fixed** during verification (3 pandas 3.x dtype issues, 1 Windows
  SQLAlchemy engine-disposal issue, 1 passlib/bcrypt version incompatibility, 1 working-directory/
  relative-path issue affecting where the SQLite file was created).
- **Both runtime processes (FastAPI backend, Streamlit frontend) verified live** via direct HTTP
  requests, including a full login round-trip producing a real JWT.
