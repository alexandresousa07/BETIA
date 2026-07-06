"""Add competition sync columns."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database.session import engine

MIGRATIONS = [
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS country_code VARCHAR(10)",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS country_flag_url VARCHAR(500)",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS season_year INTEGER",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS league_type VARCHAR(50)",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS odds_sport_key VARCHAR(100)",
    "ALTER TABLE competitions ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITH TIME ZONE",
    "CREATE INDEX IF NOT EXISTS ix_competitions_country_code ON competitions (country_code)",
    "CREATE INDEX IF NOT EXISTS ix_competitions_status ON competitions (status)",
]


async def migrate():
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            await conn.execute(text(sql))
            print(f"OK: {sql[:65]}...")
    print("Competition migration completed.")


if __name__ == "__main__":
    asyncio.run(migrate())
