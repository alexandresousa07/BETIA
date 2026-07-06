"""Add odds matching columns to existing matches table."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database.session import engine


MIGRATIONS = [
    "ALTER TABLE matches ADD COLUMN IF NOT EXISTS odds_event_id VARCHAR(100)",
    "ALTER TABLE matches ADD COLUMN IF NOT EXISTS odds_sport_key VARCHAR(100)",
    "ALTER TABLE matches ADD COLUMN IF NOT EXISTS odds_match_confidence FLOAT",
    "CREATE INDEX IF NOT EXISTS ix_matches_odds_event_id ON matches (odds_event_id)",
]


async def migrate():
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            await conn.execute(text(sql))
            print(f"OK: {sql[:60]}...")
    print("Migration completed.")


if __name__ == "__main__":
    asyncio.run(migrate())
