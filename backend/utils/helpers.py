"""Shared utility functions for the migration rules engine."""

from contextvars import ContextVar

import pandas as pd

# 1-based Excel row of the first data row (default: row 2 — header on row 1).
_excel_first_data_row: ContextVar[int] = ContextVar(
    "_excel_first_data_row", default=2
)


def is_empty(value) -> bool:
    """Return True if value is None, NaN, or an empty/whitespace string."""
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def make_result(sheet: str, row: int, supc, rule: str, message: str) -> dict:
    """Build a standardised validation result object."""
    return {
        "sheet": sheet,
        "row": row,
        "supc": supc,
        "rule": rule,
        "message": message,
    }


def get_supc(row_data: pd.Series) -> str:
    """Extract SUPC from a row, returning a placeholder if not found."""
    for col in ("SUPC", "supc", "Supc"):
        if col in row_data.index and not is_empty(row_data[col]):
            return str(row_data[col])
    return "N/A"


def excel_row(df_index: int) -> int:
    """Map 0-based DataFrame row index to 1-based Excel row (uses first-data-row context)."""
    return _excel_first_data_row.get() + df_index


def push_excel_first_data_row(row_1based: int):
    """Set the Excel row number (1-based) of the first data row; returns token for reset."""
    return _excel_first_data_row.set(row_1based)


def reset_excel_first_data_row(token) -> None:
    """Restore previous first-data-row after push_excel_first_data_row."""
    _excel_first_data_row.reset(token)
