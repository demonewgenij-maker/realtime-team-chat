"""Test fixtures: isolated temp DB per test + a fresh TestClient.

DATABASE_PATH is set on the environment *before* the app is built, and
``config.get_settings()`` reads env fresh each call, so every test gets a
clean SQLite file under pytest's tmp_path.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("TOKEN_TTL_MIN", "60")

    # Import after env is set so the app + DB bind to the temp path.
    from server.app import create_app

    app = create_app()
    # ``with`` triggers lifespan -> init_db() against the temp DB.
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client) -> str:
    resp = client.post(
        "/api/auth/register", json={"username": "alice", "password": "secret123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
