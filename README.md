# Conference Management — Backend

FastAPI + PostgreSQL (Neon) backend for desk-based registration and 4-day attendance tracking.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in DATABASE_URL (Neon pooled connection string) and JWT_SECRET_KEY
```

## First-time DB setup

```bash
python create_tables.py   # creates all tables
python seed_staff.py      # edit STAFF_USERNAMES in the script first, then run
```

## Run locally

```bash
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`.

## Deploy (Render)

1. New Web Service → connect this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the env vars from `.env.example` in Render's dashboard (use the Neon **pooled** connection string).
5. After first deploy, run `create_tables.py` and `seed_staff.py` once (Render Shell, or run locally against the same `DATABASE_URL`).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/login` | Staff login, returns JWT (7-day expiry) |
| POST | `/registrants` | Register a new attendee; auto-marks today's attendance |
| GET | `/registrants/search?q=` | Search by tag ID, name, or phone |
| GET | `/registrants/{tag_id}` | Full record + 4-day attendance grid |
| POST | `/attendance/mark` | Mark a registrant present for a given day (1-4), idempotent |

## Concurrency notes

- `tag_id` is a Postgres-assigned sequence (not app-computed), so simultaneous registrations never collide.
- Registration + day-1 attendance write happen in a single transaction — a failure rolls back both, never leaves a half-created registrant.
- Attendance marking uses `ON CONFLICT DO NOTHING`, so two staff marking the same person present on the same day is safe.
- Use Neon's **pooled** connection string (the one with `-pooler` in the hostname) — this matters once 10+ staff are hitting the API concurrently.
