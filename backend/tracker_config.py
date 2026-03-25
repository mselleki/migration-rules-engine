"""Static configuration for tracker SharePoint URLs.

Add one env var per domain in Railway:
  TRACKER_URL_PRODUCTS   = <sharepoint link>
  TRACKER_URL_VENDORS    = <sharepoint link>
  TRACKER_URL_CUSTOMERS  = <sharepoint link>

TRACKER_REFRESH_HOUR controls the daily auto-refresh time (UTC, default 6).
"""

from __future__ import annotations

import os

TRACKER_URLS: dict[str, str] = {
    "Products": os.getenv("TRACKER_URL_PRODUCTS", ""),
    "Vendors": os.getenv("TRACKER_URL_VENDORS", ""),
    "Customers": os.getenv("TRACKER_URL_CUSTOMERS", ""),
}

REFRESH_HOUR: int = int(os.getenv("TRACKER_REFRESH_HOUR", "6"))
