"""Pydantic request/response models — the public API contract."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    password: str = Field(min_length=4, max_length=200)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class ChannelOut(BaseModel):
    id: int
    name: str


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: int
    channel_id: int
    user_id: int
    username: str
    content: str
    created_at: str
