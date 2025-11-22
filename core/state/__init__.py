"""State management with SQLite storage"""
import aiosqlite
import json
import os
from typing import Any, Optional, List
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "salesbot.db"


async def init_db():
    """Initialize database schema"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS state_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def set_state(key: str, value: Any):
    """Store state by key"""
    async with aiosqlite.connect(DB_PATH) as db:
        json_value = json.dumps(value)
        await db.execute("""
            INSERT INTO state_store (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, json_value))
        await db.commit()


async def get_state(key: str) -> Optional[Any]:
    """Retrieve state by key"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM state_store WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None


async def delete_state(key: str):
    """Delete state by key"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM state_store WHERE key = ?", (key,))
        await db.commit()


async def list_keys(prefix: str = "") -> List[str]:
    """List all keys with optional prefix"""
    async with aiosqlite.connect(DB_PATH) as db:
        if prefix:
            cursor = await db.execute(
                "SELECT key FROM state_store WHERE key LIKE ?",
                (f"{prefix}%",)
            )
        else:
            cursor = await db.execute("SELECT key FROM state_store")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
