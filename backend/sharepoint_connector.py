"""SharePoint connector — downloads tracker files via Office365 REST API.

Authentication uses delegated credentials (SHAREPOINT_USER / SHAREPOINT_PASSWORD
environment variables). No Azure AD app registration required.
"""

from __future__ import annotations

import io
import os
import re
from urllib.parse import parse_qs, unquote, urlparse

from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext


def _credentials() -> UserCredential:
    user = os.getenv("SHAREPOINT_USER", "").strip()
    password = os.getenv("SHAREPOINT_PASSWORD", "").strip()
    if not user or not password:
        raise EnvironmentError(
            "SHAREPOINT_USER and SHAREPOINT_PASSWORD environment variables must be set."
        )
    return UserCredential(user, password)


def parse_sharepoint_url(url: str) -> dict:
    """Extract site_url, file_name, and file_guid from a SharePoint viewer URL.

    Works with both:
      - Viewer URLs:  https://tenant.sharepoint.com/:x:/r/sites/Site/_layouts/15/Doc.aspx?sourcedoc=...&file=...
      - Direct URLs:  https://tenant.sharepoint.com/sites/Site/Lib/file.xlsx
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Site path: /sites/SomeName  (stops before /_layouts or /Lib/...)
    m = re.search(r"(/sites/[^/_?#]+)", parsed.path)
    site_path = m.group(1) if m else ""
    site_url = base + site_path

    # File name from query string (viewer URLs carry ?file=...)
    qs = parse_qs(parsed.query)
    file_name = unquote(qs.get("file", [""])[0])

    # GUID from ?sourcedoc={GUID}
    guid_raw = unquote(qs.get("sourcedoc", [""])[0])
    file_guid = guid_raw.strip("{}") if guid_raw else ""

    # Fallback: file name from path (direct URLs)
    if not file_name and "/" in parsed.path:
        file_name = unquote(parsed.path.rsplit("/", 1)[-1])

    return {
        "site_url": site_url,
        "site_path": site_path,
        "file_name": file_name,
        "file_guid": file_guid,
    }


def download_tracker_file(sharepoint_url: str) -> tuple[bytes, str]:
    """Download a tracker file from SharePoint.

    Returns (file_bytes, file_name).
    Tries to fetch by GUID first (most reliable for viewer URLs), then falls
    back to a search across common document libraries.
    """
    info = parse_sharepoint_url(sharepoint_url)
    site_url = info["site_url"]
    file_name = info["file_name"]
    file_guid = info["file_guid"]

    if not site_url:
        raise ValueError(
            f"Could not extract a SharePoint site URL from: {sharepoint_url}"
        )

    creds = _credentials()
    ctx = ClientContext(site_url).with_credentials(creds)

    # ── Strategy 1: fetch by unique GUID ────────────────────────────────────
    if file_guid:
        try:
            buf = io.BytesIO()
            ctx.web.get_file_by_id(file_guid).download(buf).execute_query()
            data = buf.getvalue()
            if data:
                return data, file_name
        except Exception:
            pass  # fall through to strategy 2

    # ── Strategy 2: server-relative URL across common libraries ─────────────
    candidates = [
        f"{info['site_path']}/Shared Documents/{file_name}",
        f"{info['site_path']}/Documents/{file_name}",
        f"{info['site_path']}/Tracker/{file_name}",
        f"{info['site_path']}/{file_name}",
    ]
    last_exc: Exception | None = None
    for rel_url in candidates:
        try:
            buf = io.BytesIO()
            ctx.web.get_file_by_server_relative_url(rel_url).download(
                buf
            ).execute_query()
            data = buf.getvalue()
            if data:
                return data, file_name
        except Exception as exc:
            last_exc = exc
            continue

    raise FileNotFoundError(
        f"Could not download '{file_name}' from {site_url}. " f"Last error: {last_exc}"
    )
