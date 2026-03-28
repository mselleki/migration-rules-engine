"""FastAPI backend for the Sysco Migration Rules Engine."""

from __future__ import annotations

import csv
import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from validator import (
    validate,
    validate_customer,
    validate_vendor,
    validate_combined_products,
    validate_combined_vendor,
    validate_combined_customer,
)
from utils.lov_extractor import (
    get_hardcoded_lovs,
    extract_attribute_groups,
    extract_brands,
    extract_buyer_groups,
    extract_commodity_codes,
)
from diff import run_diff, DIFF_CONFIG
from reconcile import (
    load_ct_product,
    load_stibo_product,
    load_erp_product,
    reconcile_products,
    reconcile_invoice_os,
)
from lov_store import (
    init_db,
    add_custom_lov,
    delete_custom_lov,
    get_custom_lovs,
    get_history as get_lov_history,
)
import tracker_cache
import tracker_history
import tracker_config
import reconciliation_config
import reconcile_store
import reconcile as reconcile_mod
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scheduler helpers
# ---------------------------------------------------------------------------


def _report_to_dict(report) -> dict:
    return {
        "summary": {
            "total_rows": report.total_rows,
            "total_errors": report.total_errors,
            "errors_by_rule": report.errors_by_rule,
        },
        "errors": report.errors,
        "warnings": report.warnings,
        "completion": report.completion,
        "rows": list(getattr(report, "tracker_rows", None) or []),
    }


async def _refresh_domain(domain: str) -> None:
    """Fetch the SharePoint tracker for one domain and update the cache."""
    from tracker_validator import validate_tracker
    from sharepoint_connector import download_tracker_file

    url = tracker_config.TRACKER_URLS.get(domain, "")
    if not url:
        return

    try:
        file_bytes, filename = download_tracker_file(url)
        report = validate_tracker(domain, file_bytes, filename=filename)
        result = _report_to_dict(report)
        result["source"] = {"type": "sharepoint", "filename": filename}
        tracker_cache.set_result(domain, result)
        logger.info("Tracker cache updated for domain '%s' (%s)", domain, filename)
    except Exception as exc:
        tracker_cache.set_error(domain, str(exc))
        logger.error("Tracker refresh failed for domain '%s': %s", domain, exc)


async def _daily_refresh() -> None:
    for domain in tracker_config.TRACKER_URLS:
        await _refresh_domain(domain)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    tracker_cache.load()
    _scheduler.add_job(
        _daily_refresh,
        CronTrigger(hour=tracker_config.REFRESH_HOUR, minute=0),
        id="daily_tracker_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — tracker auto-refresh at %02d:00 UTC",
        tracker_config.REFRESH_HOUR,
    )
    yield
    # Shutdown
    _scheduler.shutdown(wait=False)


app = FastAPI(title="Sysco Migration Rules Engine", version="1.0.0", lifespan=lifespan)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,https://migration-rules-engine.vercel.app,https://migration-rules-engine-msellekis-projects.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "reference"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

init_db()  # LOV SQLite tables
reconcile_store.init_db()  # reconciliation history table
tracker_history.init_db()  # tracker completion snapshots

# ---------------------------------------------------------------------------
# LOV cache — reference data loaded once at startup
# ---------------------------------------------------------------------------

_REF_LOV_DF = None


def _get_ref_lovs_df():
    global _REF_LOV_DF
    if _REF_LOV_DF is not None:
        return _REF_LOV_DF

    import pandas as pd

    dfs = [get_hardcoded_lovs()]

    for fname, fn in [
        ("Attribute Group.xlsx", extract_attribute_groups),
        ("Brands.xlsx", extract_brands),
        ("Buyer Group.xlsx", extract_buyer_groups),
        ("Commodity code.xlsx", extract_commodity_codes),
    ]:
        p = REFERENCE_DIR / fname
        if p.exists():
            dfs.append(fn(str(p)))

    _REF_LOV_DF = pd.concat(dfs, ignore_index=True)
    return _REF_LOV_DF


def _get_lovs_df():
    """Merge reference LOVs (cached) with custom LOVs (always fresh)."""
    import pandas as pd

    ref = _get_ref_lovs_df()[["attribute", "key", "description"]].copy()
    ref["source"] = "reference"
    ref["id"] = ""
    ref["added_by"] = ""

    custom = get_custom_lovs()
    if not custom:
        return ref

    custom_df = pd.DataFrame(custom)[
        ["id", "attribute", "key", "description", "added_by"]
    ].copy()
    custom_df["source"] = "custom"
    return pd.concat([ref, custom_df], ignore_index=True)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


async def _read(f: UploadFile | None) -> bytes | None:
    return await f.read() if f else None


@app.post("/validate")
async def validate_files(
    domain: str = Form("Products"),
    legal_entity: str = Form(""),
    # Combined-file mode (single XLSX with multiple sheets)
    combined_file: UploadFile | None = File(None),
    # Products (individual mode)
    global_file: UploadFile | None = File(None),
    local_file: UploadFile | None = File(None),
    # Vendors & Customers (shared field names, individual mode)
    invoice: UploadFile | None = File(None),
    lea_invoice: UploadFile | None = File(None),
    os: UploadFile | None = File(None),
    lea_os: UploadFile | None = File(None),
    # Customers only (individual mode)
    pt: UploadFile | None = File(None),
    employee_invoice: UploadFile | None = File(None),
    employee_os: UploadFile | None = File(None),
):
    """Validate migration files for Products, Vendors, or Customers domain."""

    if domain == "Products":
        if combined_file:
            report = validate_combined_products(await _read(combined_file))
        else:
            if global_file is None and local_file is None:
                raise HTTPException(status_code=400, detail="Upload at least one file.")
            report = validate(await _read(global_file), await _read(local_file))

    elif domain == "Vendors":
        if combined_file:
            report = validate_combined_vendor(await _read(combined_file))
        else:
            files = {
                "invoice": await _read(invoice),
                "lea_invoice": await _read(lea_invoice),
                "os": await _read(os),
                "lea_os": await _read(lea_os),
            }
            if not any(files.values()):
                raise HTTPException(status_code=400, detail="Upload at least one file.")
            report = validate_vendor(files)

    elif domain == "Customers":
        if combined_file:
            report = validate_combined_customer(await _read(combined_file))
        else:
            files = {
                "pt": await _read(pt),
                "invoice": await _read(invoice),
                "lea_invoice": await _read(lea_invoice),
                "os": await _read(os),
                "lea_os": await _read(lea_os),
                "employee_invoice": await _read(employee_invoice),
                "employee_os": await _read(employee_os),
            }
            if not any(files.values()):
                raise HTTPException(status_code=400, detail="Upload at least one file.")
            report = validate_customer(files)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown domain '{domain}'.")

    return {
        "domain": domain,
        "legal_entity": legal_entity,
        "global_row_count": report.global_row_count,
        "local_row_count": report.local_row_count,
        "total_rows": report.total_rows,
        "total_errors": report.total_errors,
        "errors_by_rule": report.errors_by_rule,
        "errors": report.errors,
        "warnings": report.warnings,
    }


@app.post("/validate/export-csv")
async def export_csv(
    domain: str = Form("Products"),
    legal_entity: str = Form(""),
    combined_file: UploadFile | None = File(None),
    global_file: UploadFile | None = File(None),
    local_file: UploadFile | None = File(None),
    invoice: UploadFile | None = File(None),
    lea_invoice: UploadFile | None = File(None),
    os: UploadFile | None = File(None),
    lea_os: UploadFile | None = File(None),
    pt: UploadFile | None = File(None),
    employee_invoice: UploadFile | None = File(None),
    employee_os: UploadFile | None = File(None),
):
    """Run validation and return errors as a downloadable CSV."""
    if domain == "Products":
        report = (
            validate_combined_products(await _read(combined_file))
            if combined_file
            else validate(await _read(global_file), await _read(local_file))
        )
    elif domain == "Vendors":
        report = (
            validate_combined_vendor(await _read(combined_file))
            if combined_file
            else validate_vendor(
                {
                    "invoice": await _read(invoice),
                    "lea_invoice": await _read(lea_invoice),
                    "os": await _read(os),
                    "lea_os": await _read(lea_os),
                }
            )
        )
    elif domain == "Customers":
        report = (
            validate_combined_customer(await _read(combined_file))
            if combined_file
            else validate_customer(
                {
                    "pt": await _read(pt),
                    "invoice": await _read(invoice),
                    "lea_invoice": await _read(lea_invoice),
                    "os": await _read(os),
                    "lea_os": await _read(lea_os),
                    "employee_invoice": await _read(employee_invoice),
                    "employee_os": await _read(employee_os),
                }
            )
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown domain '{domain}'.")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["sheet", "row", "supc", "rule", "message"])
    writer.writeheader()
    writer.writerows(report.errors)
    buf.seek(0)

    filename = f"validation_errors_{domain}_{legal_entity or 'unknown'}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/lovs")
def get_lovs(attribute: str | None = None, q: str | None = None):
    """Return LOV rows filtered by attribute (required) and optional text search."""
    if not attribute and not q:
        return []  # never dump all 20K rows at once

    df = _get_lovs_df()

    if attribute:
        df = df[df["attribute"].astype(str).str.strip() == attribute]
    if q:
        mask = df["key"].astype(str).str.contains(q, case=False, na=False) | df[
            "description"
        ].astype(str).str.contains(q, case=False, na=False)
        df = df[mask]

    return df.fillna("").to_dict(orient="records")


@app.get("/lovs/attributes")
def get_lov_attributes():
    """Return sorted list of all attribute names."""
    df = _get_lovs_df()
    attributes = sorted(
        df["attribute"].dropna().astype(str).str.strip().unique().tolist()
    )
    return attributes


@app.get("/lovs/preview")
def get_lov_preview():
    """Return per-attribute summary: name, total count, and first 3 example keys."""
    df = _get_lovs_df()
    result = []
    for attr, group in df.groupby("attribute"):
        keys = group["key"].dropna().astype(str).str.strip().tolist()
        result.append(
            {
                "attribute": str(attr).strip(),
                "count": len(keys),
                "examples": keys[:3],
            }
        )
    result.sort(key=lambda x: x["attribute"])
    return result


# ---------------------------------------------------------------------------
# Custom LOV endpoints (DET write access)
# ---------------------------------------------------------------------------


class CustomLovIn(BaseModel):
    attribute: str
    key: str
    description: str = ""
    user: str


@app.get("/lovs/custom")
def list_custom_lovs():
    return get_custom_lovs()


@app.post("/lovs/custom", status_code=201)
def create_custom_lov(body: CustomLovIn):
    if not body.attribute.strip() or not body.key.strip() or not body.user.strip():
        raise HTTPException(400, "attribute, key, and user are required")
    return add_custom_lov(body.attribute, body.key, body.description, body.user)


@app.delete("/lovs/custom/{entry_id}")
def remove_custom_lov(entry_id: str, user: str, reason: str = ""):
    if not user.strip():
        raise HTTPException(400, "user is required")
    if not delete_custom_lov(entry_id, user, reason):
        raise HTTPException(404, "Entry not found")
    return {"ok": True}


@app.get("/lovs/history")
def list_lov_history(limit: int = 200):
    return get_lov_history(limit)


# ---------------------------------------------------------------------------
# Diff endpoints
# ---------------------------------------------------------------------------


@app.post("/validate/tracker")
async def validate_tracker_endpoint(
    domain: str = Form(...),
    file: UploadFile = File(...),
):
    """Validate a P1 Data Cleansing tracker file for Products, Vendors, or Customers."""
    from tracker_validator import validate_tracker

    file_bytes = await file.read()
    report = validate_tracker(domain, file_bytes, filename=file.filename or "")
    out = _report_to_dict(report)
    out["source"] = {
        "type": "upload",
        "filename": file.filename or "",
    }
    return out


class SharePointTrackerIn(BaseModel):
    domain: str
    sharepoint_url: str


@app.post("/validate/tracker/sharepoint")
async def validate_tracker_sharepoint(body: SharePointTrackerIn):
    """Fetch a tracker file directly from SharePoint and validate it."""
    from tracker_validator import validate_tracker
    from sharepoint_connector import download_tracker_file

    try:
        file_bytes, filename = download_tracker_file(body.sharepoint_url)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SharePoint error: {exc}")

    report = validate_tracker(body.domain, file_bytes, filename=filename)
    out = _report_to_dict(report)
    out["source"] = {
        "type": "sharepoint",
        "filename": filename,
        "url": body.sharepoint_url,
    }
    return out


# ---------------------------------------------------------------------------
# Tracker dashboard (cached results + manual refresh)
# ---------------------------------------------------------------------------


@app.get("/tracker/dashboard")
def get_tracker_dashboard():
    """Return cached validation results and config status for all domains."""
    result = {}
    for domain, url in tracker_config.TRACKER_URLS.items():
        result[domain] = {
            "configured": bool(url),
            "cached": tracker_cache.get(domain),
        }
    return result


@app.get("/tracker/history")
def get_tracker_history(domain: str, limit: int = 90):
    return tracker_history.get_history(domain, limit)


@app.post("/tracker/refresh")
async def refresh_tracker(domain: str):
    """Manually trigger a SharePoint fetch + validation for one domain."""
    if domain not in tracker_config.TRACKER_URLS:
        raise HTTPException(400, f"Unknown domain '{domain}'")
    if not tracker_config.TRACKER_URLS[domain]:
        raise HTTPException(400, f"No SharePoint URL configured for domain '{domain}'")

    await _refresh_domain(domain)

    cached = tracker_cache.get(domain)
    if cached and cached.get("error"):
        raise HTTPException(502, cached["error"])

    return {
        "configured": True,
        "cached": cached,
    }


# ---------------------------------------------------------------------------
# Reconciliation — SharePoint-based run endpoints
# ---------------------------------------------------------------------------

import asyncio


class ReconciliationRunIn(BaseModel):
    user_name: str
    markets: list[str]
    domain: str  # "Product" | "Vendor" | "Customer"
    rec_type: str = "range"


def _empty_entity_metrics() -> dict:
    return {
        "total": 0,
        "in_all_3": 0,
        "missing_stibo": 0,
        "missing_ct": 0,
        "missing_erp": 0,
    }


async def _fetch(url: str) -> bytes:
    """Download a SharePoint file in a thread (sync client)."""
    from sharepoint_connector import download_tracker_file

    data, _ = await asyncio.to_thread(download_tracker_file, url)
    return data


async def _run_market(market: str, domain: str) -> tuple[dict, list[str]]:
    """Fetch files from SharePoint and run range reconciliation for one market.

    Returns (result_dict, warnings_list).  Never raises — errors become warnings
    so the overall run can still collect results from other markets.
    """
    warnings: list[str] = []
    urls = reconciliation_config.get_urls(market, domain)
    erp_name = reconciliation_config.ERP_MAP.get(market, "ERP")

    async def _safe_fetch(src: str) -> bytes | None:
        url = urls.get(src, "")
        if not url:
            warnings.append(f"{src.upper()} {domain} URL not configured for {market}")
            return None
        try:
            return await _fetch(url)
        except Exception as exc:
            warnings.append(f"{src.upper()}: download failed — {exc}")
            return None

    ct_bytes, erp_bytes, stibo_bytes = await asyncio.gather(
        _safe_fetch("ct"), _safe_fetch("erp"), _safe_fetch("stibo")
    )

    try:
        if domain == "Product":
            ct_codes = reconcile_mod.load_ct_product(ct_bytes) if ct_bytes else []
            stibo_codes = (
                reconcile_mod.load_stibo_product(stibo_bytes) if stibo_bytes else []
            )
            try:
                erp_codes = (
                    reconcile_mod.load_erp_product(erp_bytes, erp_name)
                    if erp_bytes
                    else []
                )
            except NotImplementedError:
                erp_codes = []
                warnings.append(
                    f"ERP type '{erp_name}' not yet supported for Product loading — ERP column will be empty"
                )
            result = reconcile_mod.reconcile_products(
                ct_codes, erp_codes, stibo_codes, erp_name
            )

        elif domain == "Vendor":
            try:
                raw = reconcile_mod.reconcile_invoice_os(
                    erp_name=erp_name,
                    ct_vendor_bytes=ct_bytes,
                    ct_customer_bytes=None,
                    erp_vendor_bytes=erp_bytes,
                    erp_customer_bytes=None,
                    stibo_vendor_invoice_bytes=stibo_bytes,
                    stibo_vendor_os_bytes=stibo_bytes,
                    stibo_customer_invoice_bytes=None,
                    stibo_customer_os_bytes=None,
                )
                result = {
                    "invoice": raw["invoice"]["vendor"],
                    "ordering_shipping": raw["ordering_shipping"]["vendor"],
                    "erp_name": erp_name,
                }
            except NotImplementedError as exc:
                warnings.append(str(exc))
                result = {
                    "invoice": {"rows": [], "metrics": _empty_entity_metrics()},
                    "ordering_shipping": {
                        "rows": [],
                        "metrics": _empty_entity_metrics(),
                    },
                    "erp_name": erp_name,
                }

        elif domain == "Customer":
            try:
                raw = reconcile_mod.reconcile_invoice_os(
                    erp_name=erp_name,
                    ct_vendor_bytes=None,
                    ct_customer_bytes=ct_bytes,
                    erp_vendor_bytes=None,
                    erp_customer_bytes=erp_bytes,
                    stibo_vendor_invoice_bytes=None,
                    stibo_vendor_os_bytes=None,
                    stibo_customer_invoice_bytes=stibo_bytes,
                    stibo_customer_os_bytes=stibo_bytes,
                )
                result = {
                    "invoice": raw["invoice"]["customer"],
                    "ordering_shipping": raw["ordering_shipping"]["customer"],
                    "erp_name": erp_name,
                }
            except NotImplementedError as exc:
                warnings.append(str(exc))
                result = {
                    "invoice": {"rows": [], "metrics": _empty_entity_metrics()},
                    "ordering_shipping": {
                        "rows": [],
                        "metrics": _empty_entity_metrics(),
                    },
                    "erp_name": erp_name,
                }
        else:
            raise ValueError(f"Unknown domain '{domain}'")

    except (ValueError, KeyError) as exc:
        warnings.append(f"Reconciliation error: {exc}")
        result = {"erp_name": erp_name, "error": str(exc)}

    return result, warnings


@app.post("/reconcile/run")
async def run_reconciliation(body: ReconciliationRunIn):
    """Fetch SharePoint files and run range reconciliation for one or more markets."""
    if not body.user_name.strip():
        raise HTTPException(400, "user_name is required")
    if not body.markets:
        raise HTTPException(400, "At least one market must be selected")
    if body.domain not in reconciliation_config.DOMAINS:
        raise HTTPException(400, f"Unknown domain '{body.domain}'")
    if body.rec_type != "range":
        raise HTTPException(400, "Only 'range' reconciliation is currently supported")

    # Run all markets concurrently.
    tasks = [_run_market(m, body.domain) for m in body.markets]
    market_results = await asyncio.gather(*tasks)

    results: dict = {}
    warnings: dict = {}
    errors: dict = {}

    for market, (result, warns) in zip(body.markets, market_results):
        if "error" in result:
            errors[market] = result["error"]
        else:
            results[market] = result
        if warns:
            warnings[market] = warns

    # Build compact per-market metrics for history.
    metrics: dict = {}
    for market, result in results.items():
        if body.domain == "Product":
            metrics[market] = result.get("metrics", _empty_entity_metrics())
        else:
            metrics[market] = {
                "invoice": result.get("invoice", {}).get(
                    "metrics", _empty_entity_metrics()
                ),
                "ordering_shipping": result.get("ordering_shipping", {}).get(
                    "metrics", _empty_entity_metrics()
                ),
            }

    status = "completed" if not errors else ("partial" if results else "error")

    run_id = reconcile_store.save_run(
        user_name=body.user_name.strip(),
        markets=body.markets,
        domain=body.domain,
        rec_type=body.rec_type,
        status=status,
        metrics=metrics,
        warnings=warnings,
        results={**results, **{f"_error_{m}": e for m, e in errors.items()}},
    )

    return {
        "run_id": run_id,
        "domain": body.domain,
        "rec_type": body.rec_type,
        "markets": body.markets,
        "results": results,
        "warnings": warnings,
        "errors": errors,
        "metrics": metrics,
        "status": status,
    }


@app.get("/reconcile/history")
def get_reconciliation_history(limit: int = 50):
    return reconcile_store.get_history(limit)


@app.get("/reconcile/history/{run_id}")
def get_reconciliation_run(run_id: str):
    run = reconcile_store.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run '{run_id}' not found")
    return run


@app.get("/reconcile/config")
def get_reconcile_config():
    """Return per-entity/domain config status (whether each SharePoint URL is set)."""
    return {
        "entities": reconciliation_config.LEGAL_ENTITIES,
        "erp_map": reconciliation_config.ERP_MAP,
        "status": reconciliation_config.config_status(),
    }


class ReconcileUrlsIn(BaseModel):
    ct: str = ""
    erp: str = ""
    stibo: str = ""


@app.put("/reconcile/config/{entity}/{domain}")
def update_reconcile_config(entity: str, domain: str, body: ReconcileUrlsIn):
    """Update SharePoint URLs for one entity + domain (DET only)."""
    if entity not in reconciliation_config.LEGAL_ENTITIES:
        raise HTTPException(400, f"Unknown entity '{entity}'")
    if domain not in reconciliation_config.DOMAINS:
        raise HTTPException(400, f"Unknown domain '{domain}'")
    reconciliation_config.update_urls(
        entity, domain, {"ct": body.ct, "erp": body.erp, "stibo": body.stibo}
    )
    return {"ok": True, "entity": entity, "domain": domain}


# ---------------------------------------------------------------------------
# Reconciliation — manual file upload endpoints (kept for local/dev use)
# ---------------------------------------------------------------------------


@app.post("/reconcile/product")
async def reconcile_product_endpoint(
    erp_type: str = Form("Jeeves"),
    ct_file: UploadFile = File(...),
    erp_file: UploadFile = File(...),
    stibo_file: UploadFile = File(...),
):
    """Range reconciliation: compare product codes across CT, ERP, and STIBO."""
    ct_bytes = await ct_file.read()
    erp_bytes = await erp_file.read()
    stibo_bytes = await stibo_file.read()
    try:
        ct_codes = load_ct_product(ct_bytes, ct_file.filename or "")
        stibo_codes = load_stibo_product(stibo_bytes)
        erp_codes = load_erp_product(erp_bytes, erp_type, erp_file.filename or "")
    except (ValueError, NotImplementedError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return reconcile_products(ct_codes, erp_codes, stibo_codes, erp_name=erp_type)


@app.post("/reconcile/invoice-os")
async def reconcile_invoice_os_endpoint(
    erp_type: str = Form("Jeeves"),
    ct_vendor_file: UploadFile | None = File(None),
    ct_customer_file: UploadFile | None = File(None),
    erp_vendor_file: UploadFile | None = File(None),
    erp_customer_file: UploadFile | None = File(None),
    stibo_vendor_invoice: UploadFile | None = File(None),
    stibo_vendor_os: UploadFile | None = File(None),
    stibo_customer_invoice: UploadFile | None = File(None),
    stibo_customer_os: UploadFile | None = File(None),
):
    """Invoice + Ordering-Shipping reconciliation for Vendor and Customer codes."""

    async def _read(f: UploadFile | None) -> bytes | None:
        return await f.read() if f else None

    try:
        result = reconcile_invoice_os(
            erp_name=erp_type,
            ct_vendor_bytes=await _read(ct_vendor_file),
            ct_customer_bytes=await _read(ct_customer_file),
            erp_vendor_bytes=await _read(erp_vendor_file),
            erp_customer_bytes=await _read(erp_customer_file),
            stibo_vendor_invoice_bytes=await _read(stibo_vendor_invoice),
            stibo_vendor_os_bytes=await _read(stibo_vendor_os),
            stibo_customer_invoice_bytes=await _read(stibo_customer_invoice),
            stibo_customer_os_bytes=await _read(stibo_customer_os),
        )
    except (ValueError, NotImplementedError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@app.get("/diff/config")
def get_diff_config(type: str):
    """Return available sheet names for the given diff type."""
    cfg = DIFF_CONFIG.get(type)
    if cfg is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown diff type '{type}'. Valid: {list(DIFF_CONFIG)}",
        )
    return {"sheets": list(cfg["sheets"].keys())}


@app.post("/diff")
async def diff_files(
    original: UploadFile = File(...),
    modified: UploadFile = File(...),
    type: str = Form(...),
    sheet: str = Form(...),
):
    """Diff two Excel files for a given type and sheet."""
    original_bytes = await original.read()
    modified_bytes = await modified.read()
    try:
        result = run_diff(original_bytes, modified_bytes, type, sheet)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result
