# hanpipette chat server

FastAPI + SQLite backend powering the `/chat` room.

## Setup

```bash
cd server
cp .env.example .env
# edit .env and set CHAT_SECRET_KEY + CHAT_ADMIN_PASSWORD

uv sync
uv run uvicorn app.main:app --reload --port 8000
```

On first boot the admin user (`CHAT_ADMIN_USERNAME`) is created automatically.
Log in at `/admin` in the web UI to create additional users.

## Endpoints

- `POST /api/auth/login` — `{username, password}` → `{token, user}`
- `GET  /api/auth/me` — current user (Bearer token)
- `PATCH /api/auth/nickname` — change own nickname
- `GET  /api/messages?limit=100&before_id=...` — message history
- `GET  /api/users` *(admin)* — list users
- `POST /api/users` *(admin)* — create user
- `DELETE /api/users/{id}` *(admin)* — delete user
- `WS   /ws?token=...` — realtime chat
