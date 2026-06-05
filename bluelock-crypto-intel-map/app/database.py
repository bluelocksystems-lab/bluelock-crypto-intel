"""
database.py
───────────
SQLite database setup using aiosqlite for async access.
Stores investigation cases, wallet notes, and analyst tags.
"""

import os
import json
import aiosqlite
from app.config import settings


async def get_db():
    """Async context manager: yields a database connection."""
    db_path = settings.DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """Create tables if they don't exist yet. Called on startup."""
    db_path = settings.DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                address     TEXT NOT NULL,
                chain       TEXT NOT NULL,
                label       TEXT,
                tags        TEXT,       -- JSON list of strings
                notes       TEXT,
                risk_score  INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS tx_cache (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                address     TEXT NOT NULL,
                chain       TEXT NOT NULL,
                data        TEXT NOT NULL,  -- JSON blob
                fetched_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_address
            ON cases (address, chain)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tx_cache_address
            ON tx_cache (address, chain)
        """)

        await db.commit()


# ── Case helpers ──────────────────────────────────────────────

async def save_case(db, address: str, chain: str, notes: str = "",
                    tags: list = None, label: str = "", risk_score: int = 0):
    """Insert or update a case record."""
    tags_json = json.dumps(tags or [])
    existing = await get_case(db, address, chain)
    if existing:
        await db.execute("""
            UPDATE cases
            SET notes=?, tags=?, label=?, risk_score=?,
                updated_at=datetime('now')
            WHERE address=? AND chain=?
        """, (notes, tags_json, label, risk_score, address, chain))
    else:
        await db.execute("""
            INSERT INTO cases (address, chain, notes, tags, label, risk_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (address, chain, notes, tags_json, label, risk_score))
    await db.commit()


async def get_case(db, address: str, chain: str):
    """Fetch one case by address+chain."""
    async with db.execute(
        "SELECT * FROM cases WHERE address=? AND chain=?", (address, chain)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_cases(db):
    """Return all saved cases."""
    async with db.execute(
        "SELECT * FROM cases ORDER BY updated_at DESC"
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_case(db, case_id: int):
    """Delete a case by ID."""
    await db.execute("DELETE FROM cases WHERE id=?", (case_id,))
    await db.commit()
