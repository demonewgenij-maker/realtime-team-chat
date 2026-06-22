"""WebSocket endpoint: token-auth via query param, then channel subscribe.

Protocol:
  connect:  /ws?token=<JWT>
  client -> {"action": "subscribe", "channel_id": 1}
  server -> {"type": "subscribed", "channel_id": 1}
  server -> {"type": "message", "channel_id": 1, "message": {...}}  (on broadcast)
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    token = ws.query_params.get("token", "")
    claims = decode_token(token)
    if not claims:
        # Reject before completing the handshake.
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws.accept()
    hub = ws.app.state.hub
    try:
        while True:
            data = await ws.receive_json()
            if data.get("action") == "subscribe":
                channel_id = int(data["channel_id"])
                await hub.subscribe(channel_id, ws)
                await ws.send_json({"type": "subscribed", "channel_id": channel_id})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unsubscribe_all(ws)
