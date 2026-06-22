"""Registration and login endpoints."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_db
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: sqlite3.Connection = Depends(get_db)) -> TokenOut:
    try:
        cur = db.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (body.username, hash_password(body.password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    uid = cur.lastrowid
    return TokenOut(
        access_token=create_token(uid, body.username),
        user_id=uid,
        username=body.username,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: sqlite3.Connection = Depends(get_db)) -> TokenOut:
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (body.username,),
    ).fetchone()
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenOut(
        access_token=create_token(row["id"], row["username"]),
        user_id=row["id"],
        username=row["username"],
    )
