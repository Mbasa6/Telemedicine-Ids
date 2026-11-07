# Requirements Traceability Matrix

Maps each approved functional requirement to implemented modules, source files, and test IDs.
Test IDs reference [TESTING_REPORT.md](TESTING_REPORT.md).

## REQ-001: Detect suspicious telemedicine access attempts in near real time
- **Implemented modules**: CSV ingestion + on-demand AI detection pipeline (Random Forest +
  Isolation Forest + hybrid risk scoring), auto-generated alerts for medium/high/critical results.
- **Source files**: `backend/app/routers/events.py` (`POST /events/upload`),
  `backend/app/routers/detection.py` (`POST /detection/run`), `backend/app/ml/rf_model.py`,
  `backend/app/ml/if_model.py`, `backend/app/ml/risk_scoring.py`.
- **Test IDs**: TC-EVT-01..04, TC-DET-04.
- **Note**: "near real time" means on-demand scoring of newly-ingested events within a single
  request/response cycle, not continuous packet capture (see TECHNICAL_DECISIONS.md). TC-DET-05
  (`test_list_detection_results`) is excluded here — it only reads back already-stored results and
  does not itself exercise ingestion or detection; it is referenced under REQ-003 instead.

## REQ-002: Identify unknown attack behaviour
- **Implemented modules**: Isolation Forest unsupervised anomaly detection, trained only on
  normal-labelled training data; anomaly score feeds into the hybrid risk score.
- **Source files**: `backend/app/ml/if_model.py`, `backend/app/ml/evaluate.py`
  (`isolation_forest` evaluation block), `backend/app/routers/detection.py`.
- **Test IDs**: TC-ML-03..04, TC-DET-03 (evaluation includes Isolation Forest metrics).
- **Note**: documented as identifying deviations from learned normal behaviour requiring
  investigation, not a guarantee of detecting every unknown attack type.

## REQ-003: Provide an analyst-friendly investigation interface
- **Implemented modules**: Streamlit SOC dashboard — Overview, Security Events, Threat Detection,
  Alerts, Incidents, Reports, Administration pages; alert/incident detail expanders showing risk
  score, detection explanation, and investigation history.
- **Source files**: `frontend/streamlit_app.py`, `frontend/api_client.py`.
- **Test IDs**: TC-ALR-01..05, TC-INC-01..05, TC-DET-05 (detection-results listing surfaced to
  analysts) — these are automated API-level tests exercising the same endpoints the Streamlit UI
  calls.
- **Note**: the Streamlit UI pages themselves (Overview, Security Events, Threat Detection, Alerts,
  Incidents, Reports, Administration) have not been exercised by an automated UI test suite; any UI
  walkthrough has been manual/exploratory only and is not logged as a formal test execution in
  TESTING_REPORT.md.

## REQ-004: Maintain an auditable incident history
- **Implemented modules**: `IncidentNote` append-only history per incident, `AuditLog` table
  recording every significant action across the system.
- **Source files**: `backend/app/models.py` (`IncidentNote`, `AuditLog`),
  `backend/app/audit.py`, `backend/app/routers/incidents.py`, `backend/app/routers/reports.py`
  (`GET /reports/audit`).
- **Test IDs**: TC-INC-02, TC-INC-04, TC-RPT-04..05, TC-INT-02.

## REQ-005: Secure access through roles and identity management
- **Implemented modules**: bcrypt password hashing, JWT bearer authentication, two roles
  (`administrator`, `security_analyst`) enforced per-endpoint.
- **Source files**: `backend/app/security.py`, `backend/app/routers/auth.py`.
- **Test IDs**: TC-AUTH-01..07, TC-AUTHX-01 (`test_login_invalid_credentials_httpx` — invalid-credential
  rejection verified via a second, independent HTTP client).
- **Note**: prototype-level auth only — no SSO/IdP integration, stateless logout (see
  TECHNICAL_DECISIONS.md).

## REQ-006: Support South African deployment constraints
- **Implemented modules**: SQLite (no external DB server required), single-machine two-process
  deployment (FastAPI + Streamlit), synthetic dataset includes South African city geolocations for
  realistic demonstration data; no dependency on cloud-only managed services.
- **Source files**: `backend/app/database.py` (SQLite, auto-created), `backend/scripts/
  generate_synthetic_data.py` (`SA_CITIES`), README.md (local setup instructions requiring only a
  Python interpreter).
- **Test IDs**: TC-INT-01 (DB persistence without external server).

## REQ-007: Produce compliance-ready reports
- **Implemented modules**: Reporting module with live-aggregated summary, CSV export of alerts,
  PDF export of the summary report, administrator-only audit log view.
- **Source files**: `backend/app/routers/reports.py`, `frontend/streamlit_app.py`
  (`reports_page`).
- **Test IDs**: TC-RPT-01..05.
- **Note**: described as prototype audit/reporting capabilities that could support a future
  compliance process — not a claim of regulatory compliance (see TECHNICAL_DECISIONS.md).
