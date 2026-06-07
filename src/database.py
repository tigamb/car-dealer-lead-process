
import json
from typing import Optional, Any
import aiosqlite
from src.logger import get_logger

logger = get_logger("database")

DB_PATH = "leads.db"




async def init_db() -> None:
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id          TEXT PRIMARY KEY,
                score       INTEGER,
                priority    TEXT,
                assigned_to TEXT,
                status      TEXT,
                created_at  TEXT,
                data        TEXT  -- האובייקט המלא כ-JSON
            )
        """)
        await db.commit()
    logger.info("Database initialized", path=DB_PATH)


async def save_lead(lead: dict[str, Any]) -> None:
    """שומר ליד מעובד במלואו לטבלה."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO leads (id, score, priority, assigned_to, status, created_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["lead_id"],
                lead.get("score", 0),
                lead.get("priority", "COLD"),
                lead.get("assigned_to", "General Pool"),
                lead.get("status", "processed"),
                lead.get("created_at", ""),
                json.dumps(lead, ensure_ascii=False),  # שומר הכל כ-JSON
            ),
        )
        await db.commit()


async def get_lead(lead_id: str) -> Optional[dict]:

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT data FROM leads WHERE id = ?", (lead_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["data"])
    return None


async def get_all_leads(limit: int = 100, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT data FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
            return [json.loads(row["data"]) for row in rows]