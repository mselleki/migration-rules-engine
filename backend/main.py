"""FastAPI backend for the Sysco Migration Rules Engine."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from validator import validate
from utils.lov_extractor import extract_lovs_from_excel, extract_attribute_groups, extract_brands

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Sysco Migration Rules Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "reference"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_lovs_df():
    import pandas as pd

    dfs = []

    flat_path = REFERENCE_DIR / "lovs_flat.csv"
    if flat_path.exists():
        dfs.append(pd.read_csv(flat_path))
    else:
        lovs_path = REFERENCE_DIR / "LOVs.xlsx"
        if lovs_path.exists():
            dfs.append(extract_lovs_from_excel(str(lovs_path)))

    already = set(dfs[0]["attribute"].unique()) if dfs else set()

    attr_path = REFERENCE_DIR / "Attribute Group.xlsx"
    if attr_path.exists() and "Attribute Group ID" not in already:
        dfs.append(extract_attribute_groups(str(attr_path)))

    brands_path = REFERENCE_DIR / "Brands.xlsx"
    if brands_path.exists() and "Sysco Brand Code" not in already:
        dfs.append(extract_brands(str(brands_path)))

    return pd.concat(dfs, ignore_index=True) if dfs else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate")
async def validate_files(
    domain: str = Form("Product"),
    legal_entity: str = Form(""),
    global_file: UploadFile | None = File(None),
    local_file: UploadFile | None = File(None),
):
    """
    Validate Global and/or Local Product Data Excel files.

    - **domain**: one of Product, Vendor, Customer
    - **legal_entity**: free-text identifier for the legal entity / ERP source
    - **global_file**: Global Product Data .xlsx (optional)
    - **local_file**: Local Product Data .xlsx (optional)
    """
    if global_file is None and local_file is None:
        raise HTTPException(status_code=400, detail="Upload at least one file.")

    global_bytes = await global_file.read() if global_file else None
    local_bytes = await local_file.read() if local_file else None

    report = validate(global_bytes, local_bytes)

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
    domain: str = Form("Product"),
    legal_entity: str = Form(""),
    global_file: UploadFile | None = File(None),
    local_file: UploadFile | None = File(None),
):
    """Run validation and return errors as a downloadable CSV."""
    global_bytes = await global_file.read() if global_file else None
    local_bytes = await local_file.read() if local_file else None

    report = validate(global_bytes, local_bytes)

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
    """Return LOV rows, optionally filtered by attribute name and/or text search."""
    df = _load_lovs_df()
    if df is None:
        raise HTTPException(status_code=404, detail="LOV reference data not found.")

    if attribute:
        df = df[df["attribute"].astype(str).str.strip() == attribute]
    if q:
        mask = (
            df["key"].astype(str).str.contains(q, case=False, na=False)
            | df["description"].astype(str).str.contains(q, case=False, na=False)
        )
        df = df[mask]

    return df.fillna("").to_dict(orient="records")


@app.get("/lovs/attributes")
def get_lov_attributes():
    """Return sorted list of all attribute names."""
    df = _load_lovs_df()
    if df is None:
        raise HTTPException(status_code=404, detail="LOV reference data not found.")
    attributes = sorted(df["attribute"].dropna().astype(str).str.strip().unique().tolist())
    return attributes
