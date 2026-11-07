import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_telemedicine_ids.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app import database  # noqa: E402
from app import models  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password  # noqa: E402

engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # app.database.engine also points at TEST_DB_PATH (via the DATABASE_URL env var override above) and
    # keeps a pooled connection open after import-time create_all, which blocks deleting the file on Windows.
    database.engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    database.engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def admin_user(db_session):
    user = db_session.query(models.User).filter_by(username="test_admin").first()
    if not user:
        user = models.User(
            username="test_admin", email="test_admin@example.com",
            password_hash=hash_password("TestAdmin@123"), role=models.UserRole.ADMIN,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture()
def analyst_user(db_session):
    user = db_session.query(models.User).filter_by(username="test_analyst").first()
    if not user:
        user = models.User(
            username="test_analyst", email="test_analyst@example.com",
            password_hash=hash_password("TestAnalyst@123"), role=models.UserRole.ANALYST,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture()
def admin_token(client, admin_user):
    resp = client.post("/auth/login", data={"username": "test_admin", "password": "TestAdmin@123"})
    return resp.json()["access_token"]


@pytest.fixture()
def analyst_token(client, analyst_user):
    resp = client.post("/auth/login", data={"username": "test_analyst", "password": "TestAnalyst@123"})
    return resp.json()["access_token"]


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def analyst_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}
