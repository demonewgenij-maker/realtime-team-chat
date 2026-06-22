"""Message history (paginated) and send (broadcasts over WS)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import MessageIn, MessageOut

router = APIRouter(prefix="/api/channels", tags=["messages"])


def _channel_exists(db: sqlite3.Connection, channel_id: int) -> bool:
    return db.execute(
        "SELECT 1 FROM channels WHERE id = ?", (channel_id,)
    ).fetchone() is not None


@router.get("/{channel_id}/messages", response_model=list[MessageOut])
def history(
    channel_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    before: int | None = Query(default=None, description="Return messages with id < before"),
    db: sqlite3.Connection = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MessageOut]:
    if not _channel_exists(db, channel_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Channel not found")
    # Keyset pagination on id; newest-first slice, returned oldest-first.
    sql = (
        "SELECT m.id, m.channel_id, m.user_id, u.username, m.content, m.created_at "
        "FROM messages m JOIN users u ON u.id = m.user_id "
        "WHERE m.channel_id = ?"
    )
    params: list[object] = [channel_id]
    if before is not None:
        sql += " AND m.id < ?"
        params.append(before)
    sql += " ORDER BY m.id DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(sql, params).fetchall()
    rows = list(reversed(rows))
    return [
        MessageOut(
            id=r["id"], channel_id=r["channel_id"], user_id=r["user_id"],
            username=r["username"], content=r["content"], created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post(
    "/{channel_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send(
    channel_id: int,
    body: MessageIn,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageOut:
    if not _channel_exists(db, channel_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Channel not found")
    cur = db.execute(
        "INSERT INTO messages(channel_id, user_id, content) VALUES (?, ?, ?)",
        (channel_id, user.id, body.content),
    )
    db.commit()
    row = db.execute(
        "SELECT m.id, m.channel_id, m.user_id, u.username, m.content, m.created_at "
        "FROM messages m JOIN users u ON u.id = m.user_id WHERE m.id = ?",
        (cur.lastrowid,),
    ).fetchone()
    out = MessageOut(
        id=row["id"], channel_id=row["channel_id"], user_id=row["user_id"],
        username=row["username"], content=row["content"], created_at=row["created_at"],
    )
    # Async route -> await the hub directly; works under TestClient's loop.
    await request.app.state.hub.broadcast(channel_id, out.model_dump())
    return out
