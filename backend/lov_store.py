"""Persistent store for custom LOV entries and change history (SQLite).

Data is stored in DATA_DIR (defaults to <project_root>/data/).
For Railway: mount a Volume at /app/data and set DATA_DIR=/app/data
to survive redeploys.
"""

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

_DB_DIR = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
)
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DB_DIR / "custom_lovs.db"


@contextmanager
def _conn():
    con = sqlite3.connect(str(_DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS custom_lovs (
                id          TEXT PRIMARY KEY,
                attribute   TEXT NOT NULL,
                key         TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                added_by    TEXT NOT NULL,
                added_at    REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lov_history (
                id          TEXT PRIMARY KEY,
                action      TEXT NOT NULL,
                attribute   TEXT NOT NULL,
                key         TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                user        TEXT NOT NULL,
                ts          REAL NOT NULL
            );
        """)


def get_custom_lovs() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT id, attribute, key, description, added_by, added_at "
            "FROM custom_lovs ORDER BY added_at"
        ).fetchall()
    return [dict(r) for r in rows]


def add_custom_lov(attribute: str, key: str, description: str, user: str) -> dict:
    entry_id = str(uuid.uuid4())
    now = time.time()
    with _conn() as con:
        con.execute(
            "INSERT INTO custom_lovs (id, attribute, key, description, added_by, added_at) "
            "VALUES (?,?,?,?,?,?)",
            (entry_id, attribute.strip(), key.strip(), description.strip(), user, now),
        )
        con.execute(
            "INSERT INTO lov_history (id, action, attribute, key, description, user, ts) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                "add",
                attribute.strip(),
                key.strip(),
                description.strip(),
                user,
                now,
            ),
        )
    return {
        "id": entry_id,
        "attribute": attribute.strip(),
        "key": key.strip(),
        "description": description.strip(),
        "added_by": user,
        "added_at": now,
    }


def delete_custom_lov(entry_id: str, user: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM custom_lovs WHERE id=?", (entry_id,)
        ).fetchone()
        if not row:
            return False
        con.execute("DELETE FROM custom_lovs WHERE id=?", (entry_id,))
        con.execute(
            "INSERT INTO lov_history (id, action, attribute, key, description, user, ts) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                "delete",
                row["attribute"],
                row["key"],
                row["description"],
                user,
                time.time(),
            ),
        )
    return True


def get_history(limit: int = 200) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM lov_history ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
