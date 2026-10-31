"""Tests run against a real Postgres (TEST_DATABASE_URL), never the dev/prod DB."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.core.config import _to_psycopg_url, settings
from app.db.session import Base, get_db
from app.main import app

if not settings.test_database_url:
    raise RuntimeError("Set TEST_DATABASE_URL in backend/.env to run tests")
if settings.test_database_url == settings.database_url:
    raise RuntimeError("TEST_DATABASE_URL must differ from DATABASE_URL — tests wipe the database")

engine = create_engine(_to_psycopg_url(settings.test_database_url), pool_pre_ping=True)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, categories, expenses RESTART IDENTITY CASCADE"))


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


def register(client, email="a@example.com", password="password123") -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
