"""SharePoint connector — downloads tracker files via Office365 REST API.

Authentication uses an Azure AD App Registration (client credentials flow):
  SHAREPOINT_CLIENT_ID     — Azure AD application (client) ID
  SHAREPOINT_CLIENT_SECRET — Azure AD client secret
"""

from __future__ import annotations

import io
import os
import re
import ssl
import urllib3
from urllib.parse import parse_qs, unquote, urlparse

# Disable SSL verification for corporate proxy environments (same pattern as
# other Sysco internal tools).
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
os.environ.setdefault("CURL_CA_BUNDLE", "")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context  # noqa: SLF001

import requests  # noqa: E402 (must come after env vars are set)

_orig_request = requests.Session.request


def _patched_request(self, *args, **kwargs):
    kwargs["verify"] = False
    return _orig_request(self, *args, **kwargs)


requests.Session.request = _patched_request  # type: ignore[method-assign]

from office365.runtime.auth.client_credential import ClientCredential  # noqa: E402
from office365.sharepoint.client_context import ClientContext  # noqa: E402


def _credentials() -> ClientCredential:
    client_id = os.getenv("SHAREPOINT_CLIENT_ID", "").strip()
    client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise EnvironmentError(
            "SHAREPOINT_CLIENT_ID and SHAREPOINT_CLIENT_SECRET environment variables must be set."
        )
    return ClientCredential(client_id, client_secret)


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
    ctx = ClientContext(site_url).with_credentials(creds)  # type: ignore[arg-type]

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
