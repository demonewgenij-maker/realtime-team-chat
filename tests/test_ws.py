"""WebSocket realtime delivery tests — the core demonstration.

Flow: register -> login token -> open WS -> subscribe -> POST via REST ->
the broadcast arrives on the WS connection. Also asserts auth rejection.
"""
from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect


def _setup_user_and_channel(client):
    reg = client.post(
        "/api/auth/register", json={"username": "alice", "password": "secret123"}
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    channels = client.get("/api/channels", headers=headers).json()
    cid = next(c["id"] for c in channels if c["name"] == "general")
    return token, headers, cid


def test_ws_receives_broadcast_after_rest_post(client):
    token, headers, cid = _setup_user_and_channel(client)

    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "channel_id": cid})
        ack = ws.receive_json()
        assert ack == {"type": "subscribed", "channel_id": cid}

        # Trigger a broadcast via the REST endpoint.
        r = client.post(
            f"/api/channels/{cid}/messages",
            json={"content": "realtime hi"},
            headers=headers,
        )
        assert r.status_code == 201

        event = ws.receive_json()
        assert event["type"] == "message"
        assert event["channel_id"] == cid
        assert event["message"]["content"] == "realtime hi"
        assert event["message"]["username"] == "alice"


def test_ws_no_broadcast_for_other_channel(client):
    token, headers, cid = _setup_user_and_channel(client)
    other = client.post(
        "/api/channels", json={"name": "engineering"}, headers=headers
    ).json()["id"]

    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.send_json({"action": "subscribe", "channel_id": cid})
        assert ws.receive_json()["type"] == "subscribed"

        # Post to a different channel -> subscriber must NOT get it.
        client.post(
            f"/api/channels/{other}/messages",
            json={"content": "elsewhere"},
            headers=headers,
        )
        # Post to the subscribed channel -> this one should arrive.
        client.post(
            f"/api/channels/{cid}/messages",
            json={"content": "mine"},
            headers=headers,
        )
        event = ws.receive_json()
        assert event["message"]["content"] == "mine"


def test_ws_rejects_missing_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()


def test_ws_rejects_bad_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=not.a.jwt") as ws:
            ws.receive_json()
