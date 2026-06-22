# Realtime Team Chat

[![CI](https://github.com/demonewgenij-maker/realtime-team-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/demonewgenij-maker/realtime-team-chat/actions/workflows/ci.yml)

A compact, production-minded realtime team chat (a mini Slack/Telegram) built
from scratch as a reference implementation. FastAPI serves both a JSON REST API
and a WebSocket hub; a dependency-light SQLite layer (stdlib `sqlite3`) stores
users, channels and messages; the frontend is a zero-build vanilla-JS PWA.

## Features

- **JWT auth** — register / login, passwords hashed with `pbkdf2_hmac` (stdlib), tokens signed with `exp`.
- **Channels** — list and create, all behind auth.
- **Messages** — history with keyset pagination (`limit` / `before`), send endpoint.
- **Realtime WebSocket** — clients authenticate by token, subscribe to channels, and receive new messages instantly via a fan-out hub.
- **PWA frontend** — installable app shell cached by a service worker for offline-friendly loading; HTML rendered XSS-safe via `textContent`.
- **Tested** — pure `pytest`, including real WebSocket delivery tests, with no external services required.

## Architecture

```
                +-------------------------------------------+
   Browser      |                FastAPI app                |
  (PWA + WS)    |                                           |
  +--------+    |  REST routers      ConnectionManager      |
  | app.js | <--+--> /api/auth   --> (hub on app.state)     |
  |  +     |    |    /api/channels      |  broadcast per    |
  |  sw.js | <--+--> /api/messages -----+  channel_id       |
  +--------+    |    /ws  (token auth) <-+                  |
       ^        |            |                              |
       |        |            v                              |
       +--WS----+      SQLite (sqlite3)                     |
                |   users / channels / messages             |
                +-------------------------------------------+
```

A REST `POST /messages` writes to SQLite then `await hub.broadcast(...)`, which
pushes a JSON event to every WebSocket subscribed to that channel.

## Design decisions

| Decision | Why |
|---|---|
| Env-only config (`os.getenv`) | No secrets in code; `SECRET_KEY` defaults to a loud placeholder; tests override via env. |
| Parameterized SQL everywhere | No string formatting in queries -> injection-safe by construction. |
| WS auth via `?token=<JWT>` | Browsers can't set headers on `WebSocket`; token in query is verified before `accept()`. |
| `pbkdf2_hmac` for passwords | Salted + slow hashing from the stdlib, no native build dependency. |
| Singleton hub on `app.state` | One in-process `ConnectionManager`; async `broadcast` awaited from async routes. |
| PWA offline shell | Service worker caches static assets, never API/WS traffic. |
| Pure pytest incl. WebSocket tests | `TestClient.websocket_connect` proves realtime delivery without external infra. |

## Tech stack

- Python 3.11+, FastAPI, Uvicorn
- Standard-library `sqlite3` and `hashlib`
- PyJWT for tokens, Pydantic for schemas
- Vanilla JS / HTML / CSS PWA (no build step)
- pytest + pytest-asyncio

## Quick start

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env          # optional; sensible defaults otherwise

uvicorn server.app:app --reload
# open http://localhost:8000  -> register "alice", chat in #general

pytest -q                     # run the full suite (incl. WebSocket tests)
```

Demo channels `general` and `random` are seeded on first start. Register two
users (e.g. `alice`, `bob`) in two browser tabs to watch realtime delivery.

## Roadmap

Out of scope for this reference implementation, but natural next steps:

- Bot API (programmatic message senders)
- Web-push notifications
- Invite-based registration / org membership
- File uploads and attachments

## Notes

This is a from-scratch reference implementation. It contains **no real data,
secrets, domains, or credentials** — only neutral demo values.

## License

MIT © 2026 demonewgenij-maker
