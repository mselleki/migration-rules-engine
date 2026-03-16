"""Shared utility functions for the migration rules engine."""

import pandas as pd


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
    """Convert a 0-based DataFrame index to an Excel row number (1-based header + data)."""
    return df_index + 2
