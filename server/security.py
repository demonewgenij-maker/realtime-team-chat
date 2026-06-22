"""Password hashing (pbkdf2_hmac, stdlib) and JWT issue/verify.

pbkdf2_hmac avoids a native bcrypt dependency while staying salted + slow.
Stored format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

_ALGO = "HS256"
_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time compare against the stored pbkdf2 record."""
    try:
        algo, iter_s, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iter_s)
        )
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(dk.hex(), hash_hex)


def create_token(user_id: int, username: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=s.token_ttl_min),
    }
    return jwt.encode(payload, s.secret_key, algorithm=_ALGO)


def decode_token(token: str) -> dict | None:
    """Return the claims dict, or None if invalid/expired."""
    try:
        return jwt.decode(
            token, get_settings().secret_key, algorithms=[_ALGO]
        )
    except jwt.PyJWTError:
        return None
