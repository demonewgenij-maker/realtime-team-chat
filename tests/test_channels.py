from __future__ import annotations


def test_seeded_channels_listed(client, auth_headers):
    r = client.get("/api/channels", headers=auth_headers)
    assert r.status_code == 200
    names = {c["name"] for c in r.json()}
    assert {"general", "random"} <= names


def test_create_channel(client, auth_headers):
    r = client.post("/api/channels", json={"name": "engineering"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "engineering"

    listed = client.get("/api/channels", headers=auth_headers).json()
    assert any(c["name"] == "engineering" for c in listed)


def test_create_channel_requires_auth(client):
    r = client.post("/api/channels", json={"name": "secret"})
    assert r.status_code == 401


def test_duplicate_channel_conflicts(client, auth_headers):
    client.post("/api/channels", json={"name": "dup"}, headers=auth_headers)
    r = client.post("/api/channels", json={"name": "dup"}, headers=auth_headers)
    assert r.status_code == 409
