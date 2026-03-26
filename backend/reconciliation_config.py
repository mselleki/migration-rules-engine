"""Reconciliation configuration: legal entities, ERP mapping, and SharePoint URLs.

URLs are stored in DATA_DIR/reconciliation_config.json and can be updated
via the /reconcile/config endpoints (DET role).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_DATA_DIR = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
)
_CONFIG_PATH = _DATA_DIR / "reconciliation_config.json"

# Ordered list of all legal entities.
LEGAL_ENTITIES: list[str] = [
    "Brakes",
    "Classic_Drinks",
    "Ekofisk",
    "Fresh_Direct",
    "Fruktservice",
    "KFF",
    "LAG",
    "Medina",
    "Menigo",
    "Ready_Chef",
    "Servicestyckarna",
    "Sysco_France",
    "Sysco_Northern_Ireland",
    "Sysco_ROI",
]

# ERP system per legal entity.
ERP_MAP: dict[str, str] = {
    "Brakes": "SAP",
    "Classic_Drinks": "AX",
    "Ekofisk": "Jeeves",
    "Fresh_Direct": "Prophet",
    "Fruktservice": "ASW",
    "KFF": "Chorus",
    "LAG": "SAP",
    "Medina": "AX",
    "Menigo": "ASW",
    "Ready_Chef": "Prophet",
    "Servicestyckarna": "ASW",
    "Sysco_France": "SAP",
    "Sysco_Northern_Ireland": "AX",
    "Sysco_ROI": "AX",
}

DOMAINS: list[str] = ["Product", "Vendor", "Customer"]
SOURCES: list[str] = ["ct", "erp", "stibo"]


def _empty_entity() -> dict:
    return {domain: {src: "" for src in SOURCES} for domain in DOMAINS}


def _default_config() -> dict:
    return {entity: _empty_entity() for entity in LEGAL_ENTITIES}


def load_config() -> dict:
    """Load config from JSON file. Creates and returns default if file is missing."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _CONFIG_PATH.exists():
        cfg = _default_config()
        _save(cfg)
        return cfg
    try:
        with open(_CONFIG_PATH) as f:
            cfg = json.load(f)
        # Forward-fill any missing keys added since last save.
        default = _default_config()
        for entity in LEGAL_ENTITIES:
            if entity not in cfg:
                cfg[entity] = default[entity]
            else:
                for domain in DOMAINS:
                    if domain not in cfg[entity]:
                        cfg[entity][domain] = default[entity][domain]
                    else:
                        for src in SOURCES:
                            cfg[entity][domain].setdefault(src, "")
        return cfg
    except Exception:
        return _default_config()


def _save(cfg: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_urls(entity: str, domain: str) -> dict[str, str]:
    """Return {ct, erp, stibo} URL dict for a given entity + domain."""
    return load_config().get(entity, {}).get(domain, {src: "" for src in SOURCES})


def update_urls(entity: str, domain: str, urls: dict[str, str]) -> None:
    """Persist SharePoint URLs for one entity + domain."""
    cfg = load_config()
    cfg.setdefault(entity, _empty_entity())
    cfg[entity].setdefault(domain, {src: "" for src in SOURCES})
    for src in SOURCES:
        if src in urls:
            cfg[entity][domain][src] = urls[src].strip()
    _save(cfg)


def config_status() -> dict:
    """Return {entity: {domain: {src: bool}}} — whether each URL is configured."""
    cfg = load_config()
    return {
        entity: {
            domain: {src: bool(cfg[entity][domain][src]) for src in SOURCES}
            for domain in DOMAINS
        }
        for entity in LEGAL_ENTITIES
    }
