# Technical Decisions

## Why this stack
The approved Design Phase document described a more enterprise-oriented architecture (React,
NestJS, message brokers, PostgreSQL, container orchestration). For the Implementation, Testing and
Evaluation phase, a lighter but still fully functional stack was used so that a complete, runnable,
testable end-to-end prototype could be delivered and demonstrated within the available academic
timeframe:

| Design-phase component | Implemented prototype component | Reason |
|---|---|---|
| React frontend | Streamlit + Plotly | Streamlit lets a small team build an interactive, chart-rich analyst dashboard directly in Python, reusing the same language as the ML pipeline, with no separate build toolchain. |
| NestJS backend | FastAPI | FastAPI gives the same REST/DI/validation ergonomics as NestJS, with first-class Pydantic request/response validation and automatic OpenAPI docs, in Python so it can call scikit-learn models in-process (no inter-service RPC needed). |
| PostgreSQL + message broker | SQLite + SQLAlchemy, synchronous request/response | A file-based SQLite database requires no separate server process, satisfying the "no external DB server" implementation constraint, and is adequate for a single-analyst-at-a-time academic demonstration. A message broker was not implemented; detection runs synchronously on request instead of via an async queue. |
| Container orchestration | Local Python virtual environment | Out of scope for a single-machine academic demonstration; see "Future improvements" below. |

This is explicitly documented here so the prototype technologies are never presented as if they
were part of the originally approved design.

## Implementation compromises / prototype limitations
- **Authentication is JWT-based and stateless.** `POST /auth/logout` does not invalidate the token
  server-side (no token blacklist/allowlist) — it relies on the client discarding the token. A
  stolen token remains valid until expiry (60 minutes by default). This is a known, documented
  prototype limitation, not production-ready session management.
- **`SECRET_KEY` defaults to a hardcoded development value** (`app/config.py`) if the `SECRET_KEY`
  environment variable is not set. This is acceptable for a local academic demo only; a real
  deployment must set a strong, secret, environment-provided key.
- **CORS is fully open** (`allow_origins=["*"]`) because the frontend and backend run on the same
  developer machine during the demonstration. This would need to be restricted to the frontend's
  actual origin for any shared or public deployment.
- **No token refresh flow** — once a JWT expires, the analyst must log in again.
- **Detection is synchronous and on-demand** via `/detection/run`, not a background/streaming
  pipeline, so "near real time" (REQ-001) means "on-demand against newly-ingested events within the
  same request/response cycle", not continuous live packet/traffic monitoring.
- **No external identity provider integration** (no SSO/OAuth/Active Directory). Only local
  username/password accounts stored in the `users` table are supported.
- **No containerisation/orchestration** — the prototype runs as two local processes (`uvicorn` for
  the API, `streamlit run` for the dashboard) against a single SQLite file.
- **`incident_notes` table added beyond the originally specified schema** (see
  [DATABASE.md](DATABASE.md)) to give incident investigation history a proper queryable audit trail,
  in addition to the flat `investigation_notes` text field that was in the original design.
- **Reports/audit outputs describe themselves as prototype capabilities.** They are not presented as
  meeting POPIA, HIPAA, or any other regulatory compliance standard — they are audit/reporting
  features that *could* support a future compliance process, not compliance certification.

## Hybrid risk scoring methodology
`R = 0.4·A + 0.3·N + 0.2·C + 0.1·F`, where:
- `A` = Random Forest attack probability (0–1, from `predict_proba`).
- `N` = Isolation Forest anomaly score, min-max normalised against the training set's score range to
  0–1 (see `app/ml/if_model.py`).
- `C` = asset criticality, a fixed lookup by `access_type` (`admin_console`=1.0, `api`=0.8,
  `web_portal`=0.6, `mobile_app`=0.4, unknown=0.5 default) — reflecting that compromise of an admin
  console is inherently more severe than a patient-facing mobile app session.
- `F` = repeat-activity frequency, `request_frequency` linearly normalised against a configurable
  `max_expected` baseline (default 100 requests in the observed window), clamped to 0–1.

All four inputs are clamped to `[0, 1]` before weighting (see `compute_risk_score` in
`app/ml/risk_scoring.py`) so a single malformed/out-of-range input cannot distort the final score
beyond 0–100. The weighted sum is multiplied by 100 and rounded to 2 decimal places.

Severity thresholds (configurable in `app/config.py`):
`critical ≥ 80`, `high ≥ 60`, `medium ≥ 40`, `low < 40`.

## Model training/evaluation safeguards against data leakage
- `backend/app/ml/evaluate.py` performs a single stratified `train_test_split` (70/30) **before**
  any fitting occurs.
- The Random Forest is trained only on the training split; all reported classification metrics are
  computed on the held-out test split's predictions.
- The Isolation Forest is trained **only on rows labelled "normal" within the training split**
  (never on test-split rows, and never on attack-labelled rows), consistent with its intended use as
  an unsupervised detector of deviation from normal behaviour; its evaluation metrics report score
  separation on the test split, which it never saw during training.
- Both models are deterministic for grading/reproducibility (`random_state=42`, fixed `numpy`/
  `random` seeds in the synthetic data generator).

## Future improvements (not implemented in this prototype)
- Background/streaming detection pipeline instead of on-demand synchronous scoring.
- Token revocation / short-lived refresh tokens / session store.
- PostgreSQL + Alembic migrations for a multi-analyst production deployment.
- Integration with a real labelled public dataset (e.g. CICIDS2017) alongside the synthetic
  telemedicine dataset, if/when available in the environment.
- Containerised deployment (Docker Compose for API + dashboard).
