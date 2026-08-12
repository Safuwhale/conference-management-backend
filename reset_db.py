"""
DROPS every table and recreates them from the current models. Use this when
the schema has changed (like the events/attendance restructure) and you're
fine losing existing data - it does NOT migrate, it wipes.

    python reset_db.py

For a fresh database with no schema change needed, use create_tables.py
instead (it only creates missing tables, never drops anything).
"""
import asyncio

from app.database import engine, Base
from app import models  # noqa: F401 - ensures models are registered on Base.metadata


async def main():
    confirm = input("This will DROP ALL TABLES and recreate them. Type 'yes' to continue: ")
    if confirm.strip().lower() != "yes":
        print("Cancelled.")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables dropped and recreated. Run seed_staff.py again to re-add staff logins.")


if __name__ == "__main__":
    asyncio.run(main())
