from __future__ import annotations


def test_register_returns_token(client):
    r = client.post("/api/auth/register", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["username"] == "alice"
    assert body["user_id"] >= 1


def test_duplicate_username_conflicts(client):
    client.post("/api/auth/register", json={"username": "bob", "password": "secret123"})
    r = client.post("/api/auth/register", json={"username": "bob", "password": "other999"})
    assert r.status_code == 409


def test_login_success(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret123"})
    r = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret123"})
    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrongpass"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/channels")
    assert r.status_code == 401


def test_protected_route_rejects_bad_token(client):
    r = client.get("/api/channels", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401
