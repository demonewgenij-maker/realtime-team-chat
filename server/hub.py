"""In-memory realtime hub.

A singleton ConnectionManager held on ``app.state`` tracks live WebSocket
connections grouped by channel id and fans messages out to subscribers.
Kept deliberately simple (single-process); see README roadmap for scaling.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # channel_id -> set of subscribed websockets
        self._channels: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, channel_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._channels[channel_id].add(ws)

    async def unsubscribe_all(self, ws: WebSocket) -> None:
        """Drop a socket from every channel (called on disconnect)."""
        async with self._lock:
            for subscribers in self._channels.values():
                subscribers.discard(ws)

    async def broadcast(self, channel_id: int, message: dict) -> None:
        """Send a ``{type:"message", ...}`` payload to channel subscribers.

        Dead sockets are collected and pruned so a single broken client can't
        block delivery to the rest.
        """
        payload = {"type": "message", "channel_id": channel_id, "message": message}
        async with self._lock:
            targets = list(self._channels.get(channel_id, ()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    for subscribers in self._channels.values():
                        subscribers.discard(ws)
