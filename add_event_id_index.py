"""
One-off script for the roster/export feature: adds an index on
attendance.event_id to an EXISTING database, without touching any data.
Safe to run any time - CREATE INDEX IF NOT EXISTS is a no-op if it's
already there.

    python add_event_id_index.py
"""
import asyncio
from sqlalchemy import text
from app.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_attendance_event_id ON attendance (event_id)"))
    print("Index ix_attendance_event_id is in place. No data was touched.")


if __name__ == "__main__":
    asyncio.run(main())