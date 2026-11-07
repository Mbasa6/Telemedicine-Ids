from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import alerts, auth, detection, events, incidents, reports
from app.security import hash_password

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Academic prototype: AI-driven intrusion detection for telemedicine cybersecurity in South Africa.",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(detection.router)
app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(reports.router)


def _seed_demo_admin() -> None:
    db: Session = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == settings.DEMO_ADMIN_USERNAME).first():
            db.add(models.User(
                username=settings.DEMO_ADMIN_USERNAME, email=settings.DEMO_ADMIN_EMAIL,
                password_hash=hash_password(settings.DEMO_ADMIN_PASSWORD), role=models.UserRole.ADMIN,
            ))
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    _seed_demo_admin()


@app.get("/")
def root():
    return {"service": settings.APP_NAME, "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
