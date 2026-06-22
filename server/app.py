"""FastAPI application factory: wires routers, hub, static frontend, DB init."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .hub import ConnectionManager
from .routers import auth, channels, messages, ws

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the DB schema on startup; nothing to tear down for SQLite."""
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Realtime Team Chat", lifespan=lifespan)
    app.state.hub = ConnectionManager()

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(channels.router)
    app.include_router(messages.router)
    app.include_router(ws.router)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    # Serve the PWA frontend (html=True -> "/" returns index.html).
    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

    return app


app = create_app()
