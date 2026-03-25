"""Tracker file validator for P1 Data Cleansing tracker Excel files.

Supports Products, Vendors, and Customers domains.
Tracker files have a different structure than migration files:
  - Vendor/Customer sheets have metadata rows before the header
  - Each attribute has three adjacent columns: [Attr | Complete.X | Valid.X]
  - Row 0 may contain Yes/No/N/A mandatory indicators
"""

from __future__ import annotations

import re
from io import BytesIO
from typing import Optional

import pandas as pd

from utils.helpers import is_empty, make_result
from validator import ValidationReport
from rules.global_rules import ALL_GLOBAL_RULES
from rules.vendor_rules import ISO2_COUNTRY_LOV, ITEM_BUYER_GROUP_LOV, COST_CENTRE_LOV

# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------

_SEARCH_NAME_RE = re.compile(
    r"^[a-zA-Z0-9"
    r"áÁàÀâÂäÄåÅæÆÇçéÉèÈêÊëËíÍìÌîÎïÏñÑóÓòÒôÔöÖúÚùÙûÛüÜßÿØÝ"
    r"%&()*+\-./\u2122\u00ae"
    r"]{1,20}$"
)

# ---------------------------------------------------------------------------
# Inline LOV constants (copied from vendor_rules / customer_rules)
# ---------------------------------------------------------------------------

_INTERCOMPANY_LOV = {
    "GB01",
    "GB57",
    "GB58",
    "GB59",
    "GB80",
    "IE01",
    "IE02",
    "IE03",
    "IE90",
    "HK91",
    "HK92",
    "SE99",
    "SE01",
    "SE02",
    "SE03",
    "SE04",
    "SE05",
}

_METHOD_OF_PAYMENT_LOV = {
    "C_DD_BASE",
    "C_DD_OTHER",
    "C_CASH",
    "C_CARD",
    "C_STRDCARD",
    "C_BANK",
    "C_SWISH",
    "C_AUTOGIRO",
    "C_CHEQUE",
    "C_CONTRA",
    "V_BACS_BAS",
    "V_BACS_OTH",
    "V_CASH",
    "V_CARD",
    "V_SWISH",
    "V_AUTOGIRO",
    "V_BANK",
    "V_CONTRA",
    "V_DD_BASE",
    "V_DD_OTHER",
    "V_CHEQUE",
}

_TRADE_INDIRECT_LOV = {"Trade", "Indirect"}

_VAT_GROUP_LOV = {"I-STD", "I-ZERO", "I-RED"}

_DELIVERY_TERMS_LOV = {
    "CFR",
    "CIF",
    "CIP",
    "CPT",
    "DAP",
    "DDP",
    "DPU",
    "EXW",
    "FAS",
    "FCA",
    "FOB",
}

_MODE_OF_DELIVERY_LOV = {
    "3PL",
    "AIR",
    "AMB_TRK",
    "ANY",
    "BACK_HAUL",
    "BICYCLE",
    "BOAT",
    "BULK_CRR",
    "COLD_STRG",
    "CONSOL",
    "CONT_SHIP",
    "COURIER",
    "CROSS_DOCK",
    "CUST_COLL",
    "DIRECT",
    "DRON_DLV",
    "FROZ_TRK",
    "INTERMOD",
    "PICKUP",
    "PIPELINE",
    "REFR_TRK",
    "TRAIN",
    "TRUCK",
}

_CUSTOMER_GROUP_LOV = {"TRS", "TRP", "LCC", "CMU", "OTH", "WHL", "MIS"}

_DIVISION_LOV = {
    "BRAKES",
    "COUNTRY_CHOICE",
    "BCE",
    "KFF",
    "FRESH_DIRECT",
    "MEDINA",
    "SYSCO_ROI",
    "SYSCO_NI",
    "CLASSIC_DRINKS",
    "READY_CHEF",
    "MENIGO",
    "SERVICESTYCKARNA",
    "FRUKTSERVICE",
    "EKOFISK",
    "SYSCO_FRANCE",
    "LAG",
}

_SEASONAL_LOV = {"01", "02", "03", "04", "05", "06", "07", "99"}

_STATUS_LOV = {"Active", "Delisted", "Archived"}

# Keywords used to detect the header row in tracker sheets
_HEADER_KEYWORDS = {
    "invoice suvc",
    "o/s suvc",
    "stepid",
    "step id",
    "vendor name",
    "customer name",
    "search name",
}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _detect_header_row(xl: pd.ExcelFile, sheet: str) -> int:
    """Find the 0-based row index that contains the column headers.

    Scans row by row looking for a row that contains at least one known keyword.
    Falls back to row 0 if none found.
    """
    try:
        raw = xl.parse(sheet, header=None)
    except Exception:
        return 0

    for i, row in raw.iterrows():
        row_lower = {str(v).strip().lower() for v in row if not is_empty(v)}
        if row_lower & _HEADER_KEYWORDS:
            return int(i)
    return 0


def _parse_tracker_sheet(
    xl: pd.ExcelFile,
    sheet: str,
) -> tuple[Optional[pd.DataFrame], set[str]]:
    """Parse a tracker sheet with metadata rows above the header.

    Returns (df, mandatory_cols) where mandatory_cols is the set of column
    names whose row-0 indicator was 'Yes'.
    Returns (None, set()) if the sheet cannot be parsed.
    """
    if sheet not in xl.sheet_names:
        return None, set()

    try:
        raw = xl.parse(sheet, header=None)
    except Exception:
        return None, set()

    header_row = _detect_header_row(xl, sheet)

    # Row 0 holds mandatory indicators (Yes/No/N/A) aligned to column positions
    mandatory_cols: set[str] = set()
    if header_row > 0:
        indicator_row = raw.iloc[0]
        header_values = raw.iloc[header_row]
        for col_idx, indicator in enumerate(indicator_row):
            if str(indicator).strip().lower() == "yes":
                col_name = header_values.iloc[col_idx]
                if not is_empty(col_name):
                    mandatory_cols.add(str(col_name).strip())

    # Parse again using the detected header row
    try:
        df = xl.parse(sheet, header=header_row)
    except Exception:
        return None, set()

    # Drop Complete.X and Valid.X helper columns
    cols_to_drop = [
        c for c in df.columns if re.match(r"^(Complete|Valid)\.", str(c), re.IGNORECASE)
    ]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    return df, mandatory_cols


def _col(df: pd.DataFrame, name: str) -> Optional[str]:
    """Return the actual column name in df that matches `name` case-insensitively.

    Returns None if not found.
    """
    name_lower = name.strip().lower()
    for c in df.columns:
        if str(c).strip().lower() == name_lower:
            return c
    return None


def _get_id(row: pd.Series, df: pd.DataFrame) -> str:
    """Extract the best available row identifier for error reporting."""
    for candidate in (
        "SUPC",
        "Invoice SUVC",
        "O/S SUVC",
        "Customer Code",
        "StepID",
        "Step ID",
        "SUVC Invoice",
        "SUVC Ordering/Shipping",
    ):
        actual = _col(df, candidate)
        if actual and not is_empty(row.get(actual)):
            val = str(row.get(actual)).strip()
            if val.endswith(".0"):
                val = val[:-2]
            return val
    return "N/A"


# ---------------------------------------------------------------------------
# Completion helpers
# ---------------------------------------------------------------------------


def _compute_completion(df: pd.DataFrame, sheet_name: str) -> dict:
    """Return per-column fill rates for completion analysis."""
    total = len(df)
    columns = []
    for col in df.columns:
        filled = int(df[col].apply(lambda v: not is_empty(v)).sum())
        columns.append(
            {
                "attribute": str(col).strip(),
                "filled": filled,
                "rate": round(filled / total, 4) if total > 0 else 0.0,
            }
        )
    return {"sheet": sheet_name, "total_rows": total, "columns": columns}


# ---------------------------------------------------------------------------
# Generic check helpers
# ---------------------------------------------------------------------------


def _check_lov(
    df: pd.DataFrame,
    col_name: str,
    lov_set: set,
    rule_name: str,
    sheet: str,
) -> list[dict]:
    actual = _col(df, col_name)
    if actual is None:
        return []
    results = []
    for idx, row in df.iterrows():
        raw = row.get(actual)
        if is_empty(raw):
            continue
        if str(raw).strip() not in lov_set:
            results.append(
                make_result(
                    sheet=sheet,
                    row=idx + 2,
                    supc=_get_id(row, df),
                    rule=rule_name,
                    message=f"Row {idx + 2} - '{col_name}' value '{str(raw).strip()}' is not in the allowed list.",
                )
            )
    return results


def _check_iso_country(
    df: pd.DataFrame,
    col_name: str,
    sheet: str,
    rule_name: str,
) -> list[dict]:
    actual = _col(df, col_name)
    if actual is None:
        return []
    results = []
    for idx, row in df.iterrows():
        raw = row.get(actual)
        if is_empty(raw):
            continue
        if str(raw).strip().upper() not in ISO2_COUNTRY_LOV:
            results.append(
                make_result(
                    sheet=sheet,
                    row=idx + 2,
                    supc=_get_id(row, df),
                    rule=rule_name,
                    message=f"Row {idx + 2} - 'Country' value '{str(raw).strip()}' is not a valid ISO 3166-1 alpha-2 code.",
                )
            )
    return results


def _check_search_name(
    df: pd.DataFrame,
    sheet: str,
    rule_name: str,
) -> list[dict]:
    actual = _col(df, "Search Name")
    if actual is None:
        return []
    results = []
    for idx, row in df.iterrows():
        raw = row.get(actual)
        if is_empty(raw):
            continue
        val = str(raw).strip()
        reasons = []
        if len(val) > 20:
            reasons.append(f"exceeds 20 characters ({len(val)})")
        if " " in val:
            reasons.append("contains spaces")
        if not _SEARCH_NAME_RE.match(val):
            reasons.append("contains disallowed characters")
        if reasons:
            results.append(
                make_result(
                    sheet=sheet,
                    row=idx + 2,
                    supc=_get_id(row, df),
                    rule=rule_name,
                    message=f"Row {idx + 2} - 'Search Name' is invalid: {'; '.join(reasons)}.",
                )
            )
    return results


def _check_mandatory(
    df: pd.DataFrame,
    mandatory_cols: set[str],
    sheet: str,
    rule_name: str,
) -> list[dict]:
    results = []
    for col_name in mandatory_cols:
        actual = _col(df, col_name)
        if actual is None:
            continue
        for idx, row in df.iterrows():
            if is_empty(row.get(actual)):
                results.append(
                    make_result(
                        sheet=sheet,
                        row=idx + 2,
                        supc=_get_id(row, df),
                        rule=rule_name,
                        message=f"Row {idx + 2} - '{col_name}' is mandatory but empty.",
                    )
                )
    return results


# ---------------------------------------------------------------------------
# Column rename maps (tracker col name -> rule col name)
# ---------------------------------------------------------------------------

_VENDOR_COL_MAP = {
    "Invoice SUVC": "SUVC Invoice",
    "O/S SUVC": "SUVC Ordering/Shipping",
    "Delivery Term": "Delivery Terms",
    "Mode Of Delivery": "Mode of Delivery",
    "Method Of Payment": "Method of Payment",
    "Vendor Status": "Status",
}

_CUSTOMER_COL_MAP = {
    "Invoice SUVC": "SUVC Invoice",
    "O/S SUVC": "SUVC Ordering/Shipping",
    "Delivery Term": "Delivery Terms",
    "Mode Of Delivery": "Mode of Delivery",
    "Method Of Payment": "Method of Payment",
    "Customer Status": "Status",
}


def _rename_tracker_cols(df: pd.DataFrame, col_map: dict[str, str]) -> pd.DataFrame:
    """Rename tracker-specific column names to the canonical names expected by rules."""
    rename = {}
    for tracker_name, rule_name in col_map.items():
        actual = _col(df, tracker_name)
        if actual:
            rename[actual] = rule_name
    return df.rename(columns=rename)


# ---------------------------------------------------------------------------
# Sheet-specific validators
# ---------------------------------------------------------------------------


def _validate_vendor_invoice(df: pd.DataFrame, mandatory_cols: set[str]) -> list[dict]:
    sheet = "Invoice"
    errors: list[dict] = []

    errors += _check_lov(
        df,
        "Intercompany/Trading Partner",
        _INTERCOMPANY_LOV,
        "Tracker - Intercompany/Trading Partner LOV",
        sheet,
    )
    errors += _check_lov(
        df,
        "Trade/Indirect Vendor",
        _TRADE_INDIRECT_LOV,
        "Tracker - Trade/Indirect Vendor LOV",
        sheet,
    )
    errors += _check_iso_country(df, "Country", sheet, "Tracker - Country ISO-2")
    errors += _check_lov(
        df, "VAT Group", _VAT_GROUP_LOV, "Tracker - VAT Group LOV", sheet
    )
    errors += _check_lov(
        df,
        "Method of Payment",
        _METHOD_OF_PAYMENT_LOV,
        "Tracker - Method of Payment LOV",
        sheet,
    )
    errors += _check_search_name(df, sheet, "Tracker - Search Name format")

    # Hard-coded mandatory fields for vendor invoice (in addition to row-0 indicators)
    hard_mandatory = {
        "Company Registration Number",
        "Address Line 1",
        "Town/City",
        "Zip/Postal Code",
    }
    errors += _check_mandatory(
        df, hard_mandatory | mandatory_cols, sheet, "Tracker - Mandatory field"
    )

    return errors


def _validate_vendor_os(df: pd.DataFrame, mandatory_cols: set[str]) -> list[dict]:
    sheet = "OrderingShipping"
    errors: list[dict] = []

    errors += _check_iso_country(df, "Country", sheet, "Tracker - Country ISO-2")
    errors += _check_lov(
        df, "Delivery Terms", _DELIVERY_TERMS_LOV, "Tracker - Delivery Terms LOV", sheet
    )
    errors += _check_lov(
        df,
        "Mode of Delivery",
        _MODE_OF_DELIVERY_LOV,
        "Tracker - Mode of Delivery LOV",
        sheet,
    )
    errors += _check_lov(
        df, "Buyer Group", ITEM_BUYER_GROUP_LOV, "Tracker - Buyer Group LOV", sheet
    )
    errors += _check_search_name(df, sheet, "Tracker - Search Name format")
    errors += _check_mandatory(df, mandatory_cols, sheet, "Tracker - Mandatory field")

    return errors


def _validate_customer_invoice(
    df: pd.DataFrame, mandatory_cols: set[str]
) -> list[dict]:
    sheet = "Invoice"
    errors: list[dict] = []

    errors += _check_lov(
        df,
        "Intercompany/Trading Partner",
        _INTERCOMPANY_LOV,
        "Tracker - Intercompany/Trading Partner LOV",
        sheet,
    )
    errors += _check_lov(
        df, "Customer Group", _CUSTOMER_GROUP_LOV, "Tracker - Customer Group LOV", sheet
    )
    errors += _check_lov(df, "Division", _DIVISION_LOV, "Tracker - Division LOV", sheet)
    errors += _check_lov(df, "Seasonal", _SEASONAL_LOV, "Tracker - Seasonal LOV", sheet)
    errors += _check_iso_country(df, "Country", sheet, "Tracker - Country ISO-2")
    errors += _check_lov(
        df,
        "Method of Payment",
        _METHOD_OF_PAYMENT_LOV,
        "Tracker - Method of Payment LOV",
        sheet,
    )
    errors += _check_lov(
        df, "Cost Centre", COST_CENTRE_LOV, "Tracker - Cost Centre LOV", sheet
    )
    errors += _check_search_name(df, sheet, "Tracker - Search Name format")
    errors += _check_mandatory(df, mandatory_cols, sheet, "Tracker - Mandatory field")

    return errors


def _validate_customer_os(df: pd.DataFrame, mandatory_cols: set[str]) -> list[dict]:
    sheet = "OrderingShipping"
    errors: list[dict] = []

    errors += _check_lov(
        df, "Delivery Terms", _DELIVERY_TERMS_LOV, "Tracker - Delivery Terms LOV", sheet
    )
    errors += _check_lov(
        df,
        "Mode of Delivery",
        _MODE_OF_DELIVERY_LOV,
        "Tracker - Mode of Delivery LOV",
        sheet,
    )
    errors += _check_iso_country(df, "Country", sheet, "Tracker - Country ISO-2")
    errors += _check_lov(df, "Seasonal", _SEASONAL_LOV, "Tracker - Seasonal LOV", sheet)
    errors += _check_mandatory(df, mandatory_cols, sheet, "Tracker - Mandatory field")

    return errors


def _validate_customer_employee(
    df: pd.DataFrame, mandatory_cols: set[str]
) -> list[dict]:
    sheet = "Employee"
    errors: list[dict] = []

    errors += _check_iso_country(df, "Country", sheet, "Tracker - Country ISO-2")
    errors += _check_lov(
        df,
        "Method of Payment",
        _METHOD_OF_PAYMENT_LOV,
        "Tracker - Method of Payment LOV",
        sheet,
    )
    errors += _check_lov(
        df, "Customer Group", _CUSTOMER_GROUP_LOV, "Tracker - Customer Group LOV", sheet
    )
    errors += _check_lov(
        df, "Cost Centre", COST_CENTRE_LOV, "Tracker - Cost Centre LOV", sheet
    )
    errors += _check_lov(df, "Status", _STATUS_LOV, "Tracker - Status LOV", sheet)
    errors += _check_mandatory(df, mandatory_cols, sheet, "Tracker - Mandatory field")

    return errors


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def validate_tracker(
    domain: str, file_bytes: bytes, filename: str = ""
) -> ValidationReport:
    """Validate a tracker Excel file for the given domain.

    Args:
        domain: "Products", "Vendors", or "Customers"
        file_bytes: raw bytes of the uploaded .xlsx file

    Returns:
        ValidationReport with errors and warnings populated.
    """
    report = ValidationReport()

    engine = "pyxlsb" if filename.lower().endswith(".xlsb") else "openpyxl"
    try:
        xl = pd.ExcelFile(BytesIO(file_bytes), engine=engine)
    except Exception as exc:
        report.warnings.append(
            f"Failed to open tracker file as an Excel workbook: {exc}"
        )
        return report

    if domain == "Products":
        _validate_product_tracker(xl, report)
    elif domain == "Vendors":
        _validate_vendor_tracker(xl, report)
    elif domain == "Customers":
        _validate_customer_tracker(xl, report)
    else:
        report.warnings.append(f"Unknown domain '{domain}'.")

    return report


def _validate_product_tracker(xl: pd.ExcelFile, report: ValidationReport) -> None:
    sheet = "in"
    if sheet not in xl.sheet_names:
        report.warnings.append(
            f"Sheet '{sheet}' not found in tracker file. Available: {xl.sheet_names}"
        )
        return

    try:
        df = xl.parse(sheet)
    except Exception as exc:
        report.warnings.append(f"Could not read sheet '{sheet}': {exc}")
        return

    # Normalize XML-encoded column names: <gt/> -> >
    df.columns = [str(c).replace("<gt/>", ">") for c in df.columns]

    df = df.dropna(how="all").reset_index(drop=True)
    report.global_row_count = len(df)
    report.completion.append(_compute_completion(df, sheet))

    for rule_fn in ALL_GLOBAL_RULES:
        try:
            report.errors.extend(rule_fn(df))
        except Exception as exc:
            report.warnings.append(
                f"Rule '{rule_fn.__name__}' error on tracker 'in' sheet: {exc}"
            )


def _validate_vendor_tracker(xl: pd.ExcelFile, report: ValidationReport) -> None:
    sheet_configs = [
        ("Invoice", _validate_vendor_invoice, _VENDOR_COL_MAP),
        ("OrderingShipping", _validate_vendor_os, _VENDOR_COL_MAP),
    ]

    for sheet_name, validate_fn, col_map in sheet_configs:
        if sheet_name not in xl.sheet_names:
            report.warnings.append(
                f"Sheet '{sheet_name}' not found in vendor tracker. Available: {xl.sheet_names}"
            )
            continue

        df, mandatory_cols = _parse_tracker_sheet(xl, sheet_name)
        if df is None or df.empty:
            report.warnings.append(
                f"Sheet '{sheet_name}' is empty or could not be parsed."
            )
            continue

        df = _rename_tracker_cols(df, col_map)
        report.global_row_count += len(df)
        report.completion.append(_compute_completion(df, sheet_name))

        try:
            report.errors.extend(validate_fn(df, mandatory_cols))
        except Exception as exc:
            report.warnings.append(f"Validation error on sheet '{sheet_name}': {exc}")


def _validate_customer_tracker(xl: pd.ExcelFile, report: ValidationReport) -> None:
    sheet_configs = [
        ("Invoice", _validate_customer_invoice, _CUSTOMER_COL_MAP),
        ("OrderingShipping", _validate_customer_os, _CUSTOMER_COL_MAP),
        ("Employee", _validate_customer_employee, _CUSTOMER_COL_MAP),
    ]

    for sheet_name, validate_fn, col_map in sheet_configs:
        if sheet_name not in xl.sheet_names:
            report.warnings.append(
                f"Sheet '{sheet_name}' not found in customer tracker. Available: {xl.sheet_names}"
            )
            continue

        df, mandatory_cols = _parse_tracker_sheet(xl, sheet_name)
        if df is None or df.empty:
            report.warnings.append(
                f"Sheet '{sheet_name}' is empty or could not be parsed."
            )
            continue

        df = _rename_tracker_cols(df, col_map)
        report.global_row_count += len(df)
        report.completion.append(_compute_completion(df, sheet_name))

        try:
            report.errors.extend(validate_fn(df, mandatory_cols))
        except Exception as exc:
            report.warnings.append(f"Validation error on sheet '{sheet_name}': {exc}")
