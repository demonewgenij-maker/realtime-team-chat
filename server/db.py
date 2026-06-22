"""SQLite connection helper and idempotent schema bootstrap.

Uses the stdlib sqlite3 module to keep dependencies minimal. A new connection
is opened per request (cheap for SQLite) and rows come back as dict-like Rows.
"""
from __future__ import annotations

import sqlite3

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_id, id);
"""


def connect() -> sqlite3.Connection:
    """Open a connection to the configured database with FK + Row factory on."""
    # check_same_thread=False: FastAPI may run an async route and its sync
    # dependency on different threads (esp. under TestClient). Each request
    # still gets its own short-lived connection, so this stays safe.
    conn = sqlite3.connect(get_settings().database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if missing and seed neutral demo channels (idempotent)."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        for name in ("general", "random"):
            conn.execute(
                "INSERT OR IGNORE INTO channels(name) VALUES (?)", (name,)
            )
        conn.commit()
    finally:
        conn.close()
