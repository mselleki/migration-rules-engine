"""SQLite store for reconciliation run history.

Stored in DATA_DIR/reconciliations.db (same volume as custom_lovs.db).
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

_DB_DIR = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
)
_DB_PATH = _DB_DIR / "reconciliations.db"


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
            CREATE TABLE IF NOT EXISTS reconciliation_runs (
                id          TEXT PRIMARY KEY,
                created_at  REAL NOT NULL,
                user_name   TEXT NOT NULL,
                markets     TEXT NOT NULL,
                domain      TEXT NOT NULL,
                rec_type    TEXT NOT NULL,
                status      TEXT NOT NULL,
                metrics     TEXT NOT NULL DEFAULT '{}',
                warnings    TEXT NOT NULL DEFAULT '{}',
                results     TEXT NOT NULL DEFAULT '{}'
            );
        """)


def save_run(
    user_name: str,
    markets: list[str],
    domain: str,
    rec_type: str,
    status: str,
    metrics: dict,
    warnings: dict,
    results: dict,
) -> str:
    run_id = str(uuid.uuid4())
    with _conn() as con:
        con.execute(
            "INSERT INTO reconciliation_runs "
            "(id, created_at, user_name, markets, domain, rec_type, status, metrics, warnings, results) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                time.time(),
                user_name,
                json.dumps(markets),
                domain,
                rec_type,
                status,
                json.dumps(metrics),
                json.dumps(warnings),
                json.dumps(results),
            ),
        )
    return run_id


def get_history(limit: int = 50) -> list[dict]:
    """Return recent runs without the heavy results blob."""
    with _conn() as con:
        rows = con.execute(
            "SELECT id, created_at, user_name, markets, domain, rec_type, status, metrics, warnings "
            "FROM reconciliation_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["markets"] = json.loads(d["markets"])
        d["metrics"] = json.loads(d["metrics"])
        d["warnings"] = json.loads(d["warnings"])
        out.append(d)
    return out


def get_run(run_id: str) -> dict | None:
    """Return a single run including full results."""
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM reconciliation_runs WHERE id=?", (run_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["markets"] = json.loads(d["markets"])
    d["metrics"] = json.loads(d["metrics"])
    d["warnings"] = json.loads(d["warnings"])
    d["results"] = json.loads(d["results"])
    return d
