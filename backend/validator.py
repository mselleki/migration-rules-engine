"""Orchestrates validation across all domain migration files."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd

from rules.global_rules import ALL_GLOBAL_RULES
from rules.local_rules import ALL_LOCAL_RULES
from rules.customer_rules import (
    ALL_INVOICE_RULES as C_INVOICE_RULES,
    ALL_LEA_INVOICE_RULES as C_LEA_INVOICE_RULES,
    ALL_OS_RULES as C_OS_RULES,
    ALL_LEA_OS_RULES as C_LEA_OS_RULES,
    ALL_EMP_INVOICE_RULES, ALL_EMP_OS_RULES, ALL_PT_RULES,
    rule_copy_invoice_address_match,
)
from rules.vendor_rules import (
    ALL_INVOICE_RULES as V_INVOICE_RULES,
    ALL_LEA_INVOICE_RULES as V_LEA_INVOICE_RULES,
    ALL_OS_RULES as V_OS_RULES,
    ALL_LEA_OS_RULES as V_LEA_OS_RULES,
)


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

    try:
        df = xls.parse(xls.sheet_names[0])
        return df
    except Exception as exc:
        report.warnings.append(f"Could not read sheet from '{label}': {exc}")
        return None


def _run_rules(df: pd.DataFrame, rules: list, label: str, report: ValidationReport) -> int:
    """Apply a list of rule functions to df; return row count."""
    if df is None or df.empty:
        return 0
    row_count = len(df)
    for rule_fn in rules:
        try:
            report.errors.extend(rule_fn(df))
        except Exception as exc:
            report.warnings.append(f"Rule '{rule_fn.__name__}' error in '{label}': {exc}")
    return row_count


def validate(
    global_file_bytes: bytes | None,
    local_file_bytes: bytes | None,
) -> ValidationReport:
    """Validate Products domain (Global + Local Product Data)."""
    report = ValidationReport()

    if global_file_bytes is not None:
        df = _parse_file(global_file_bytes, "Global Product Data", report)
        report.global_row_count = _run_rules(df, ALL_GLOBAL_RULES, "Global Product Data", report)

    if local_file_bytes is not None:
        df = _parse_file(local_file_bytes, "Local Product Data", report)
        report.local_row_count = _run_rules(df, ALL_LOCAL_RULES, "Local Product Data", report)

    return report


def validate_customer(files: dict[str, bytes | None]) -> ValidationReport:
    """
    Validate Customers domain.

    Expected keys in `files`:
      pt, invoice, lea_invoice, os, lea_os, employee_invoice, employee_os
    """
    report = ValidationReport()

    sheet_rules = {
        "pt":               (ALL_PT_RULES,         "PT"),
        "invoice":          (C_INVOICE_RULES,       "Invoice"),
        "lea_invoice":      (C_LEA_INVOICE_RULES,   "LEA Invoice"),
        "os":               (C_OS_RULES,            "OS"),
        "lea_os":           (C_LEA_OS_RULES,        "LEA OS"),
        "employee_invoice": (ALL_EMP_INVOICE_RULES, "Employee Invoice"),
        "employee_os":      (ALL_EMP_OS_RULES,      "Employee OS"),
    }

    dfs: dict[str, pd.DataFrame | None] = {}
    for key, (rules, label) in sheet_rules.items():
        file_bytes = files.get(key)
        if file_bytes is None:
            continue
        df = _parse_file(file_bytes, label, report)
        dfs[key] = df
        rows = _run_rules(df, rules, label, report)
        report.global_row_count += rows

    # Cross-sheet rule: Employee OS address must match Invoice address
    df_invoice = dfs.get("invoice")
    df_emp_os  = dfs.get("employee_os")
    if df_invoice is not None and df_emp_os is not None:
        try:
            report.errors.extend(rule_copy_invoice_address_match(df_emp_os, df_invoice))
        except Exception as exc:
            report.warnings.append(f"Rule 'rule_copy_invoice_address_match' error: {exc}")

    return report


def validate_vendor(files: dict[str, bytes | None]) -> ValidationReport:
    """
    Validate Vendors domain.

    Expected keys: invoice, lea_invoice, os, lea_os
    Rules: Search Name, Intercompany, Method of Payment, VAT Group,
    Delivery Terms, Mode of Delivery, Status.
    """
    report = ValidationReport()
    sheet_rules = {
        "invoice":     (V_INVOICE_RULES,     "Invoice"),
        "lea_invoice": (V_LEA_INVOICE_RULES, "LEA Invoice"),
        "os":          (V_OS_RULES,          "OS"),
        "lea_os":      (V_LEA_OS_RULES,      "LEA OS"),
    }
    for key, (rules, label) in sheet_rules.items():
        file_bytes = files.get(key)
        if file_bytes is None:
            continue
        df = _parse_file(file_bytes, label, report)
        rows = _run_rules(df, rules, label, report)
        report.global_row_count += rows

    return report
