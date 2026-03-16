"""Validation rules for Vendor domain templates.

Vendor migration files contain 4 sheets:
  Invoice, LEA_Invoice, OS, LEA_OS

Each rule function signature: (df: pd.DataFrame) -> list[dict]
Register new rules in the appropriate list at the bottom of this file.
"""

import re
import pandas as pd
from utils.helpers import is_empty, make_result, get_supc, excel_row

SHEET_INVOICE     = "Invoice"
SHEET_LEA_INVOICE = "LEA_Invoice"
SHEET_OS          = "OS"
SHEET_LEA_OS      = "LEA_OS"

# Search Name regex (no spaces, ≤20 chars, allowed chars + accents)
_SEARCH_NAME_RE = re.compile(
    r"^[a-zA-Z0-9"
    r"áÁàÀâÂäÄåÅæÆÇçéÉèÈêÊëËíÍìÌîÎïÏñÑóÓòÒôÔöÖúÚùÙûÛüÜßÿØÝ"
    r"%&()*+\-./\u2122\u00ae"
    r"]{1,20}$"
)


# =============================================================================
# Invoice rules
# =============================================================================

def rule_lov_intercompany_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-L1 — Intercompany/Trading Partner must be a valid entity code."""
    rule_name = "Rule V-L1 — Intercompany/Trading Partner LOV"
    LOV = {
        "GB01", "GB57", "GB58", "GB59", "GB80",
        "IE01", "IE02", "IE03", "IE90",
        "HK91", "HK92",
        "SE99", "SE01", "SE02", "SE03", "SE04", "SE05",
    }
    col = "Intercompany/Trading Partner"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Intercompany/Trading Partner' value '{str(raw).strip()}' is not a recognised entity code.",
            ))
    return results


def rule_search_name_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-F1 — Search Name: ≤20 chars, no spaces, allowed chars only."""
    rule_name = "Rule V-F1 — Search Name format"
    col = "Search Name"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
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
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Search Name' is invalid: {'; '.join(reasons)}.",
            ))
    return results


ALL_INVOICE_RULES: list = [
    rule_lov_intercompany_invoice,   # Rule V-L1
    rule_search_name_invoice,        # Rule V-F1
]


# =============================================================================
# LEA Invoice rules
# =============================================================================

def rule_lov_method_of_payment(df: pd.DataFrame) -> list[dict]:
    """Rule V-L2 — Method of Payment must be a valid code."""
    rule_name = "Rule V-L2 — Method of Payment LOV"
    LOV = {
        "C_DD_BASE", "C_DD_OTHER", "C_CASH", "C_CARD", "C_STRDCARD",
        "C_BANK", "C_SWISH", "C_AUTOGIRO", "C_CHEQUE", "C_CONTRA",
        "V_BACS_BAS", "V_BACS_OTH", "V_CASH", "V_CARD", "V_SWISH",
        "V_AUTOGIRO", "V_BANK", "V_CONTRA", "V_DD_BASE", "V_DD_OTHER", "V_CHEQUE",
    }
    col = "Method of Payment"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Method of Payment' value '{str(raw).strip()}' is not a recognised payment method code.",
            ))
    return results


def rule_lov_vat_group(df: pd.DataFrame) -> list[dict]:
    """Rule V-L3 — VAT Group: I-STD, I-ZERO, I-RED."""
    rule_name = "Rule V-L3 — VAT Group LOV"
    LOV = {"I-STD", "I-ZERO", "I-RED"}
    col = "VAT Group"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'VAT Group' value '{str(raw).strip()}' is invalid. Allowed: I-STD, I-ZERO, I-RED.",
            ))
    return results


def rule_lov_status_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-L4 — Status: Active, Delisted, Archived."""
    rule_name = "Rule V-L4 — Status LOV"
    LOV = {"Active", "Delisted", "Archived"}
    col = "Status"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Status' value '{str(raw).strip()}' is invalid. Allowed: Active, Delisted, Archived.",
            ))
    return results


ALL_LEA_INVOICE_RULES: list = [
    rule_lov_method_of_payment,    # Rule V-L2
    rule_lov_vat_group,            # Rule V-L3
    rule_lov_status_lea_invoice,   # Rule V-L4
]


# =============================================================================
# OS rules
# =============================================================================

def rule_search_name_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-F2 — Search Name (OS): ≤20 chars, no spaces, allowed chars only."""
    rule_name = "Rule V-F2 — Search Name format"
    col = "Search Name"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
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
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Search Name' is invalid: {'; '.join(reasons)}.",
            ))
    return results


ALL_OS_RULES: list = [
    rule_search_name_os,   # Rule V-F2
]


# =============================================================================
# LEA OS rules
# =============================================================================

def rule_lov_delivery_terms(df: pd.DataFrame) -> list[dict]:
    """Rule V-L5 — Delivery Terms must be a valid Incoterms code."""
    rule_name = "Rule V-L5 — Delivery Terms LOV"
    LOV = {"CFR", "CIF", "CIP", "CPT", "DAP", "DDP", "DPU", "EXW", "FAS", "FCA", "FOB"}
    col = "Delivery Terms"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Delivery Terms' value '{str(raw).strip()}' is not a recognised Incoterms code.",
            ))
    return results


def rule_lov_mode_of_delivery(df: pd.DataFrame) -> list[dict]:
    """Rule V-L6 — Mode of Delivery must be a valid code."""
    rule_name = "Rule V-L6 — Mode of Delivery LOV"
    LOV = {
        "3PL", "AIR", "AMB_TRK", "ANY", "BACK_HAUL", "BICYCLE", "BOAT",
        "BULK_CRR", "COLD_STRG", "CONSOL", "CONT_SHIP", "COURIER",
        "CROSS_DOCK", "CUST_COLL", "DIRECT", "DRON_DLV", "FROZ_TRK",
        "INTERMOD", "PICKUP", "PIPELINE", "REFR_TRK", "TRAIN", "TRUCK",
    }
    col = "Mode of Delivery"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Mode of Delivery' value '{str(raw).strip()}' is not a recognised delivery mode code.",
            ))
    return results


def rule_lov_status_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-L7 — Status: Active, Delisted, Archived."""
    rule_name = "Rule V-L7 — Status LOV"
    LOV = {"Active", "Delisted", "Archived"}
    col = "Status"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Status' value '{str(raw).strip()}' is invalid. Allowed: Active, Delisted, Archived.",
            ))
    return results


ALL_LEA_OS_RULES: list = [
    rule_lov_delivery_terms,    # Rule V-L5
    rule_lov_mode_of_delivery,  # Rule V-L6
    rule_lov_status_lea_os,     # Rule V-L7
]
