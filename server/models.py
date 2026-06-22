"""Domain types used internally (decoupled from the wire schemas)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    username: str
