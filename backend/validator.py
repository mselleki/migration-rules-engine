"""Orchestrates validation across both sheets of a Sysco migration Excel file."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd

from rules.global_rules import ALL_GLOBAL_RULES
from rules.local_rules import ALL_LOCAL_RULES

GLOBAL_SHEET = "Global Product Data"
LOCAL_SHEET = "Local Product Data"


@dataclass
class ValidationReport:
    """Container for the full validation output."""

    global_row_count: int = 0
    local_row_count: int = 0
    errors: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return self.global_row_count + self.local_row_count

    @property
    def total_errors(self) -> int:
        return len(self.errors)

    @property
    def errors_by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for err in self.errors:
            counts[err["rule"]] = counts.get(err["rule"], 0) + 1
        return counts

    @property
    def errors_df(self) -> pd.DataFrame:
        if not self.errors:
            return pd.DataFrame(columns=["sheet", "row", "supc", "rule", "message"])
        return pd.DataFrame(self.errors)


def _parse_file(file_bytes: bytes, label: str, report: ValidationReport) -> pd.DataFrame | None:
    """Open an Excel file and return its first sheet as a DataFrame."""
    try:
        xls = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    except Exception as exc:
        report.warnings.append(f"Failed to open '{label}' as an Excel workbook: {exc}")
        return None

    if not xls.sheet_names:
        report.warnings.append(f"'{label}' contains no sheets.")
        return None

    sheet_name = xls.sheet_names[0]
    try:
        df = xls.parse(sheet_name)
        return df
    except Exception as exc:
        report.warnings.append(f"Could not read sheet '{sheet_name}' from '{label}': {exc}")
        return None


def validate(
    global_file_bytes: bytes | None,
    local_file_bytes: bytes | None,
) -> ValidationReport:
    """
    Run all validation rules against the two migration files.

    Parameters
    ----------
    global_file_bytes:
        Raw bytes of the Global Product Data .xlsx file.
    local_file_bytes:
        Raw bytes of the Local Product Data .xlsx file.
    """
    report = ValidationReport()

    # --- Global Product Data ---
    if global_file_bytes is not None:
        global_df = _parse_file(global_file_bytes, "Global Product Data", report)
        if global_df is not None:
            if global_df.empty:
                report.warnings.append("The Global Product Data file is empty.")
            else:
                report.global_row_count = len(global_df)
                for rule_fn in ALL_GLOBAL_RULES:
                    try:
                        report.errors.extend(rule_fn(global_df))
                    except Exception as exc:
                        report.warnings.append(
                            f"Rule '{rule_fn.__name__}' raised an unexpected error: {exc}"
                        )

    # --- Local Product Data ---
    if local_file_bytes is not None:
        local_df = _parse_file(local_file_bytes, "Local Product Data", report)
        if local_df is not None:
            if local_df.empty:
                report.warnings.append("The Local Product Data file is empty.")
            else:
                report.local_row_count = len(local_df)
                for rule_fn in ALL_LOCAL_RULES:
                    try:
                        report.errors.extend(rule_fn(local_df))
                    except Exception as exc:
                        report.warnings.append(
                            f"Rule '{rule_fn.__name__}' raised an unexpected error: {exc}"
                        )

    return report
