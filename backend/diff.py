"""Excel diff module for the Sysco Migration Rules Engine. """

from __future__ import annotations

import io
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DIFF_CONFIG: dict[str, dict] = {
    "product": {
        "sheets": {
            "Item": "SUPC",
        }
    },
    "vendor": {
        "sheets": {
            "Invoice": "Invoice SUVC",
            "OrderingShipping": "O/S SUVC",
        }
    },
    "customer": {
        "sheets": {
            "Invoice": "Customer Code",
            "OrderingShipping": "O/S Customer Code",
            "Employee": "Customer Code (Employee)",
        }
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_val(v: Any) -> Any:
    """Convert a cell value to a JSON-serialisable type."""
    if v is None:
        return None
    # pandas NA / NaN / NaT
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    # Timestamp → ISO string
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    # numpy int / float → native Python
    try:
        import numpy as np
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            f = float(v)
            if pd.isna(f):
                return None
            return f
        if isinstance(v, np.bool_):
            return bool(v)
    except ImportError:
        pass
    return v


# ---------------------------------------------------------------------------
# Core diff
# ---------------------------------------------------------------------------


def run_diff(
    original_bytes: bytes,
    modified_bytes: bytes,
    diff_type: str,
    sheet: str,
) -> dict:
    """Diff two Excel workbooks on a specific sheet.

    Parameters
    ----------
    original_bytes:
        Raw bytes of the *original* .xlsx file.
    modified_bytes:
        Raw bytes of the *modified* .xlsx file.
    diff_type:
        One of ``"product"``, ``"vendor"``, ``"customer"``.
    sheet:
        Sheet name as defined in ``DIFF_CONFIG``.

    Returns
    -------
    dict
        A structure with ``summary`` and ``rows`` keys.
    """
    # --- validate config ---------------------------------------------------
    type_cfg = DIFF_CONFIG.get(diff_type)
    if type_cfg is None:
        raise ValueError(f"Unknown diff type '{diff_type}'. Valid: {list(DIFF_CONFIG)}")

    sheet_cfg = type_cfg["sheets"]
    if sheet not in sheet_cfg:
        raise ValueError(
            f"Unknown sheet '{sheet}' for type '{diff_type}'. Valid: {list(sheet_cfg)}"
        )

    key_col = sheet_cfg[sheet]

    # --- load DataFrames ---------------------------------------------------
    try:
        df_orig = pd.read_excel(io.BytesIO(original_bytes), sheet_name=sheet, dtype=str)
    except Exception as exc:
        raise ValueError(f"Could not read sheet '{sheet}' from original file: {exc}") from exc

    try:
        df_mod = pd.read_excel(io.BytesIO(modified_bytes), sheet_name=sheet, dtype=str)
    except Exception as exc:
        raise ValueError(f"Could not read sheet '{sheet}' from modified file: {exc}") from exc

    # --- validate key column present --------------------------------------
    if key_col not in df_orig.columns:
        raise ValueError(
            f"Key column '{key_col}' not found in original file sheet '{sheet}'. "
            f"Available columns: {list(df_orig.columns)}"
        )
    if key_col not in df_mod.columns:
        raise ValueError(
            f"Key column '{key_col}' not found in modified file sheet '{sheet}'. "
            f"Available columns: {list(df_mod.columns)}"
        )

    # --- column-level changes ---------------------------------------------
    orig_cols = set(df_orig.columns)
    mod_cols = set(df_mod.columns)

    columns_added = sorted(mod_cols - orig_cols)
    columns_removed = sorted(orig_cols - mod_cols)
    common_cols = [c for c in df_orig.columns if c in mod_cols]

    # type changes (we loaded as str, but detect original numeric/date types by re-loading)
    type_changes: dict[str, dict] = {}
    try:
        df_orig_typed = pd.read_excel(io.BytesIO(original_bytes), sheet_name=sheet)
        df_mod_typed = pd.read_excel(io.BytesIO(modified_bytes), sheet_name=sheet)
        for col in common_cols:
            orig_dtype = str(df_orig_typed[col].dtype)
            mod_dtype = str(df_mod_typed[col].dtype)
            if orig_dtype != mod_dtype:
                type_changes[col] = {"original": orig_dtype, "modified": mod_dtype}
    except Exception:
        pass  # type detection is best-effort

    # --- all columns in output (key first, then union) --------------------
    all_cols_ordered = [key_col] + [
        c for c in df_orig.columns if c != key_col
    ] + [
        c for c in df_mod.columns if c != key_col and c not in set(df_orig.columns)
    ]

    # --- merge on key column (outer join) ---------------------------------
    df_orig = df_orig.set_index(key_col)
    df_mod = df_mod.set_index(key_col)

    merged = df_orig.merge(
        df_mod,
        left_index=True,
        right_index=True,
        how="outer",
        suffixes=("__orig", "__mod"),
    )

    # --- build rows -------------------------------------------------------
    rows_added = 0
    rows_deleted = 0
    rows_modified = 0
    result_rows: list[dict] = []

    non_key_cols = [c for c in all_cols_ordered if c != key_col]

    for key_val, merged_row in merged.iterrows():
        in_orig = key_val in df_orig.index
        in_mod = key_val in df_mod.index

        if in_orig and not in_mod:
            status = "deleted"
            rows_deleted += 1
        elif in_mod and not in_orig:
            status = "added"
            rows_added += 1
        else:
            status = "unchanged"  # may be upgraded to "modified" below

        cells: dict[str, dict] = {}

        for col in non_key_cols:
            orig_key = f"{col}__orig"
            mod_key = f"{col}__mod"

            if col in columns_added:
                # only in modified
                new_val = _safe_val(merged_row.get(mod_key, merged_row.get(col)))
                cells[col] = {"old": None, "new": new_val, "changed": True if new_val is not None else False}
                if new_val is not None and status == "unchanged":
                    status = "modified"
            elif col in columns_removed:
                # only in original
                old_val = _safe_val(merged_row.get(orig_key, merged_row.get(col)))
                cells[col] = {"old": old_val, "new": None, "changed": True if old_val is not None else False}
                if old_val is not None and status == "unchanged":
                    status = "modified"
            else:
                # common column — compare __orig vs __mod
                old_raw = merged_row.get(orig_key, merged_row.get(col))
                new_raw = merged_row.get(mod_key, merged_row.get(col))
                old_val = _safe_val(old_raw)
                new_val = _safe_val(new_raw)

                # string-compare (both loaded as str; treat NaN/None as empty)
                old_str = "" if old_val is None else str(old_val).strip()
                new_str = "" if new_val is None else str(new_val).strip()
                changed = old_str != new_str

                cells[col] = {"old": old_val, "new": new_val, "changed": changed}
                if changed and status == "unchanged":
                    status = "modified"

        if status == "modified":
            rows_modified += 1

        result_rows.append({
            "key": _safe_val(key_val),
            "status": status,
            "cells": cells,
        })

    summary = {
        "type": diff_type,
        "sheet": sheet,
        "key_column": key_col,
        "rows_added": rows_added,
        "rows_deleted": rows_deleted,
        "rows_modified": rows_modified,
        "columns_added": columns_added,
        "columns_removed": columns_removed,
        "type_changes": type_changes,
    }

    return {"summary": summary, "rows": result_rows}
