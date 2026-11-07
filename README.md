# Telemedicine AI-IDS

An AI-driven Intrusion Detection prototype for telemedicine platform cybersecurity, built as part
of a PGDip ICT academic project ("AI-Driven Intrusion Detection Framework for Telemedicine
Cybersecurity in South Africa").

It ingests telemedicine access-log events (CSV), scores them with a hybrid AI detection pipeline
(supervised Random Forest + unsupervised Isolation Forest), raises alerts/incidents for an analyst
to triage via a Streamlit dashboard, and produces audit-ready reports.

See [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE.md](DATABASE.md),
[API_DOCUMENTATION.md](API_DOCUMENTATION.md), [TECHNICAL_DECISIONS.md](TECHNICAL_DECISIONS.md),
[REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) and
[TESTING_REPORT.md](TESTING_REPORT.md) for full design, decision, and verification detail.

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI 0.162, Uvicorn 0.54 |
| Database | SQLite (file-based) via SQLAlchemy 2.1 ORM |
| Auth | JWT (python-jose) + bcrypt password hashing (passlib) |
| AI / ML | scikit-learn 1.9 (Random Forest + Isolation Forest), pandas 3.1, numpy 2.5 |
| Frontend | Streamlit 1.67 + Plotly 7.1 analyst dashboard |
| Reporting | fpdf2 (PDF export), native CSV export |
| Testing | pytest 9.2, pytest-asyncio, httpx |

Developed and verified against **Python 3.15.0** on Windows — no compatibility issues were found;
every dependency had a prebuilt `cp315` wheel, so no downgrade to Python 3.12/3.13 was necessary.

The versions above are the exact ones this project was built and tested against, pinned in
[`requirements-lock.txt`](requirements-lock.txt). [`requirements.txt`](requirements.txt) lists
unpinned direct dependencies for general install; use the lock file instead if you need to
reproduce the exact tested environment (`pip install -r requirements-lock.txt`).

## Project structure

```
telemedicine-ids/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration, demo admin seeding
│   │   ├── config.py            # Settings (DATABASE_URL, JWT secret, risk weights, thresholds)
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models.py            # ORM models (users, events, alerts, incidents, audit log, ...)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── security.py          # Password hashing, JWT issuing/verification
│   │   ├── audit.py             # Audit log helper
│   │   ├── ml/                  # Random Forest, Isolation Forest, risk scoring, evaluation
│   │   └── routers/             # auth, events, detection, alerts, incidents, reports
│   ├── scripts/generate_synthetic_data.py  # Synthetic dataset generator
│   ├── data/                    # Generated CSV datasets — present in this submission
│   │                             # (sample_events.csv, synthetic_telemedicine_events.csv)
│   ├── ml_models/                # Trained model artifacts + evaluation_results.json — present in
│   │                             # this submission; the *.joblib files are git-ignored (see
│   │                             # .gitignore), so a fresh git clone must regenerate them via
│   │                             # "Training the AI models" below
│   └── tests/                    # 51 automated pytest tests
├── frontend/
│   ├── streamlit_app.py          # Analyst SOC dashboard (multi-page)
│   └── api_client.py             # Thin HTTP client wrapping the FastAPI backend
├── requirements.txt               # Unpinned direct dependencies
└── requirements-lock.txt          # Exact pinned versions this project was built/tested against
```

## Setup

```powershell
# From the project root
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Generate the synthetic dataset

```powershell
cd backend
..\.venv\Scripts\python.exe scripts/generate_synthetic_data.py
```

Produces `backend/data/synthetic_telemedicine_events.csv` (3000 labelled rows, used for model
training/evaluation) and `backend/data/sample_events.csv` (40 rows, including 3 intentionally
invalid rows, for demonstrating CSV ingestion/validation).

## Running the backend (FastAPI)

> **Important (Windows):** the database path in `config.py` is a relative SQLite path
> (`sqlite:///./telemedicine_ids.db`), which resolves against the process's actual **working
> directory**, not against `--app-dir`. Always `cd` into `backend/` before launching, rather than
> relying on `--app-dir` alone, or you will get a stray `.db` file created in the wrong folder.

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

On first startup the app auto-creates all tables and seeds a demo administrator account:

- **Username**: `admin`
- **Password**: `Admin@12345`

> **Local demo credentials only — not for production.** This account and its default password are
> for local/academic-demo evaluation only and are seeded unconditionally on first startup. Override
> via the `DEMO_ADMIN_USERNAME` / `DEMO_ADMIN_PASSWORD` environment variables before any non-local
> use. Likewise, `SECRET_KEY` in `config.py` defaults to an insecure placeholder
> (`dev-only-insecure-secret-key-change-in-production`) and must be overridden via the `SECRET_KEY`
> environment variable outside local demo use.

Verify it's running:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
# -> status : ok
```

## Running the frontend (Streamlit)

```powershell
cd frontend
..\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open `http://localhost:8501` and log in with the demo admin credentials above. The dashboard
expects the backend to already be running on `http://127.0.0.1:8000` (see `api_client.py`).

## Training the AI models

Models can be trained either through the dashboard (Administration page, admin-only) or the API:

```powershell
# After logging in and obtaining a bearer token:
Invoke-RestMethod -Uri http://127.0.0.1:8000/detection/train -Method POST -Headers @{Authorization="Bearer <token>"}
```

This trains the Random Forest (supervised, attack vs normal) and Isolation Forest (unsupervised,
trained only on normal-labelled rows) against `backend/data/synthetic_telemedicine_events.csv`,
persists both models as `.joblib` files under `backend/ml_models/`, and writes
`backend/ml_models/evaluation_results.json` with real evaluation metrics (see
[TESTING_REPORT.md](TESTING_REPORT.md) for the actual recorded results).

## Running the automated tests

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -v
```

**Verified result: 51 passed, 0 failed** (93 cosmetic deprecation warnings only — see
[TESTING_REPORT.md](TESTING_REPORT.md) for full details and the defects found/fixed during
verification).

## Known limitations

See [TECHNICAL_DECISIONS.md](TECHNICAL_DECISIONS.md) for the full list (stateless JWT logout, no
SSO/IdP integration, synchronous on-demand detection rather than streaming, no containerisation,
CORS fully open for local demo purposes, reports are prototype-level and not a regulatory
compliance claim).
