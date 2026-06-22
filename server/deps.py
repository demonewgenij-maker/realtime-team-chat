"""FastAPI dependencies: DB connection lifecycle and current-user auth."""
from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, Header, HTTPException, status

from .db import connect
from .models import User
from .security import decode_token


def get_db() -> Iterator[sqlite3.Connection]:
    """Yield a per-request connection and always close it."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: sqlite3.Connection = Depends(get_db),
) -> User:
    """Parse ``Authorization: Bearer <jwt>`` and load the user, else 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    claims = decode_token(authorization.split(" ", 1)[1].strip())
    if not claims:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    row = db.execute(
        "SELECT id, username FROM users WHERE id = ?", (int(claims["sub"]),)
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return User(id=row["id"], username=row["username"])
