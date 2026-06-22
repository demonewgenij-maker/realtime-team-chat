"""Channel listing and creation (auth required)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import ChannelIn, ChannelOut

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=list[ChannelOut])
def list_channels(
    db: sqlite3.Connection = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ChannelOut]:
    rows = db.execute("SELECT id, name FROM channels ORDER BY id").fetchall()
    return [ChannelOut(id=r["id"], name=r["name"]) for r in rows]


@router.post("", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(
    body: ChannelIn,
    db: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChannelOut:
    try:
        cur = db.execute(
            "INSERT INTO channels(name, created_by) VALUES (?, ?)",
            (body.name, user.id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Channel name already exists")
    return ChannelOut(id=cur.lastrowid, name=body.name)
