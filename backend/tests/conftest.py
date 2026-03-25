import os

# Test env before app imports (db engine uses DATABASE_URL at import time)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MOCK_AI", "true")
os.environ.setdefault("MOCK_WHISPER", "true")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session() -> Session:
    from app.db import SessionLocal

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_and_token(client: TestClient) -> tuple[dict, str]:
    r = client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/api/me", headers=auth_header(token)).json()
    return me, token
