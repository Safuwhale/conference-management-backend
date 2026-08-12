"""
Seeds staff logins. Default password for everyone is "admin" - have each
staffer change it later if you add a change-password endpoint, or just
reset it manually in the DB after the event.

Edit STAFF_USERNAMES below to the 8 real names/usernames, then run:
    python seed_staff.py
"""
import asyncio

from app.auth import hash_password
from app.database import AsyncSessionLocal
from app.models import Staff

STAFF_USERNAMES = [
    "Nandom",
    "admin",
    "Vincent",
    "Asa",
    "Laura",
    "Sally",
    "Njamba",
    "Elvis",
    "Samuel",
]
DEFAULT_PASSWORD = "admin"


async def main():
    async with AsyncSessionLocal() as db:
        for username in STAFF_USERNAMES:
            db.add(Staff(username=username, password_hash=hash_password(DEFAULT_PASSWORD)))
        await db.commit()
    print(f"Seeded {len(STAFF_USERNAMES)} staff accounts with password '{DEFAULT_PASSWORD}'.")


if __name__ == "__main__":
    asyncio.run(main())
