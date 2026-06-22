from __future__ import annotations


def _general_id(client, headers) -> int:
    channels = client.get("/api/channels", headers=headers).json()
    return next(c["id"] for c in channels if c["name"] == "general")


def test_send_and_history(client, auth_headers):
    cid = _general_id(client, auth_headers)
    r = client.post(f"/api/channels/{cid}/messages", json={"content": "hello team"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["content"] == "hello team"
    assert r.json()["username"] == "alice"

    hist = client.get(f"/api/channels/{cid}/messages", headers=auth_headers).json()
    assert [m["content"] for m in hist] == ["hello team"]


def test_history_pagination_before(client, auth_headers):
    cid = _general_id(client, auth_headers)
    ids = []
    for i in range(5):
        r = client.post(f"/api/channels/{cid}/messages", json={"content": f"m{i}"}, headers=auth_headers)
        ids.append(r.json()["id"])

    # limit returns the newest 2 (returned oldest-first)
    page = client.get(f"/api/channels/{cid}/messages?limit=2", headers=auth_headers).json()
    assert [m["content"] for m in page] == ["m3", "m4"]

    # before the 3rd message id -> only m0, m1
    older = client.get(
        f"/api/channels/{cid}/messages?before={ids[2]}", headers=auth_headers
    ).json()
    assert [m["content"] for m in older] == ["m0", "m1"]


def test_message_unknown_channel_404(client, auth_headers):
    r = client.post("/api/channels/9999/messages", json={"content": "x"}, headers=auth_headers)
    assert r.status_code == 404

    r2 = client.get("/api/channels/9999/messages", headers=auth_headers)
    assert r2.status_code == 404


def test_send_requires_auth(client):
    r = client.post("/api/channels/1/messages", json={"content": "x"})
    assert r.status_code == 401
