"""FastAPI backend for the Sysco Migration Rules Engine."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path

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
from lov_store import (
    init_db,
    add_custom_lov,
    delete_custom_lov,
    get_custom_lovs,
    get_history as get_lov_history,
)
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Sysco Migration Rules Engine", version="1.0.0")

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

init_db()

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
def remove_custom_lov(entry_id: str, user: str):
    if not user.strip():
        raise HTTPException(400, "user is required")
    if not delete_custom_lov(entry_id, user):
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
    return {
        "summary": {
            "total_rows": report.total_rows,
            "total_errors": report.total_errors,
            "errors_by_rule": report.errors_by_rule,
        },
        "errors": report.errors,
        "warnings": report.warnings,
        "completion": report.completion,
    }


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
    return {
        "summary": {
            "total_rows": report.total_rows,
            "total_errors": report.total_errors,
            "errors_by_rule": report.errors_by_rule,
        },
        "errors": report.errors,
        "warnings": report.warnings,
        "completion": report.completion,
        "source": {
            "type": "sharepoint",
            "filename": filename,
            "url": body.sharepoint_url,
        },
    }


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
