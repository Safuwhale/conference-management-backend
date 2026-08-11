"""
Run once against a fresh database to create all tables:
    python create_tables.py
"""
import asyncio

from app.database import engine, Base
from app import models  # noqa: F401 - ensures models are registered on Base.metadata


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(main())
