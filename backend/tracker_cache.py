"""Persistent cache for tracker validation results.

Results are stored in DATA_DIR/tracker_cache.json (same volume as SQLite).
The in-memory dict is the primary store; the file is loaded at startup
and written on every update so results survive Railway restarts.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_DB_DIR = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
)
_CACHE_FILE = _DB_DIR / "tracker_cache.json"

_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load() -> None:
    """Load persisted cache from disk at startup."""
    try:
        if _CACHE_FILE.exists():
            data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            _cache.update(data)
    except Exception:
        pass  # non-fatal — cache will be rebuilt on first refresh


def get(domain: str) -> dict | None:
    return _cache.get(domain)


def get_all() -> dict[str, dict]:
    return dict(_cache)


def set_result(domain: str, report: dict) -> None:
    _cache[domain] = {
        "report": report,
        "error": None,
        "updated_at": time.time(),
    }
    _persist()
    try:
        import tracker_history

        tracker_history.record(domain, report)
    except Exception:
        pass  # non-fatal


def set_error(domain: str, error: str) -> None:
    _cache[domain] = {
        "report": None,
        "error": error,
        "updated_at": time.time(),
    }
    _persist()


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _persist() -> None:
    try:
        _DB_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(_cache, default=_json_default, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass  # non-fatal


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)
