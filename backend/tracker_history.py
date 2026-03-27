"""SQLite store for tracker completion snapshots (time-series for progress chart)."""

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
_DB_PATH = _DB_DIR / "tracker_history.db"


@contextmanager
def _conn():
    _DB_DIR.mkdir(parents=True, exist_ok=True)
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
            CREATE TABLE IF NOT EXISTS tracker_snapshots (
                id           TEXT PRIMARY KEY,
                domain       TEXT NOT NULL,
                ts           REAL NOT NULL,
                pct_complete REAL NOT NULL,
                total_attrs  INTEGER NOT NULL,
                uncleansed   INTEGER NOT NULL
            );
        """)


def record(domain: str, report: dict) -> None:
    """Extract completion stats from a tracker report and persist a snapshot."""
    completion = report.get("completion") or []
    total_attrs = 0
    uncleansed = 0
    for sheet in completion:
        for col in sheet.get("columns", []):
            total_attrs += 1
            if col.get("rate", 1.0) < 1.0:
                uncleansed += 1

    if total_attrs == 0:
        return  # nothing to record

    pct = (total_attrs - uncleansed) / total_attrs
    with _conn() as con:
        con.execute(
            "INSERT INTO tracker_snapshots (id, domain, ts, pct_complete, total_attrs, uncleansed) "
            "VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), domain, time.time(), pct, total_attrs, uncleansed),
        )


def get_history(domain: str, limit: int = 90) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT ts, pct_complete, total_attrs, uncleansed "
            "FROM tracker_snapshots WHERE domain=? ORDER BY ts ASC LIMIT ?",
            (domain, limit),
        ).fetchall()
    return [dict(r) for r in rows]
