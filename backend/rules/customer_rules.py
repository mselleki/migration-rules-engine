"""Validation rules for Customer domain templates.

Customer migration files contain up to 7 sheets:
  PT, Invoice, LEA_Invoice, OS, LEA_OS, EmployeeInvoice, EmployeeOS

Each rule function signature: (df: pd.DataFrame) -> list[dict]
The SHEET constant in each rule identifies which sheet the rule applies to.
Register new rules in the appropriate list at the bottom of this file.
"""

import re
import pandas as pd
from utils.helpers import is_empty, make_result, get_supc, excel_row

# Search Name: ≤20 chars, no spaces, allowed chars (letters, digits, accents, approved specials)
_SEARCH_NAME_RE = re.compile(
    r"^[a-zA-Z0-9"
    r"áÁàÀâÂäÄåÅæÆÇçéÉèÈêÊëËíÍìÌîÎïÏñÑóÓòÒôÔöÖúÚùÙûÛüÜßÿØÝ"
    r"%&()*+\-./\u2122\u00ae"
    r"]{1,20}$"
)

# Sheet names
SHEET_INVOICE      = "Invoice"
SHEET_LEA_INVOICE  = "LEA_Invoice"
SHEET_OS           = "OS"
SHEET_LEA_OS       = "LEA_OS"
SHEET_EMP_INVOICE  = "EmployeeInvoice"
SHEET_EMP_OS       = "EmployeeOS"
SHEET_PT           = "PT"


# =============================================================================
# Invoice sheet rules
# =============================================================================

def rule_lov_intercompany_trading_partner(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L1 — Intercompany/Trading Partner must be a valid company code.
      GB01 = Sysco GB (old Brake Bros Ltd)
      GB57 = Medina Quay Meats Limited
      GB58 = Fresh Direct UK Ltd
      GB59 = Kent Frozen Foods
      GB80 = Sysco Foods NI Limited
      IE01 = Sysco Foods Ireland UC
      IE02 = Classic Drinks
      IE03 = Ready Chef
      IE90 = SMS Int'l Resources Ireland Unlimited
      HK91 = SMS GPC International Limited
      HK92 = SMS GPC International Resources Limited
      SE99 = Menigo Group
      SE01 = Menigo Food Service AB
      SE02 = Fruktservice i Helsingborg AB
      SE03 = Ekofisk
      SE04 = Servicestyckarna AB
      SE05 = Restaurangakademien

    Applies to: Invoice sheet only.
    """
    rule_name = "Rule C-L1 — Intercompany/Trading Partner LOV"
    TRADING_PARTNER_LOV = {
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
        if str(raw).strip() not in TRADING_PARTNER_LOV:
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Intercompany/Trading Partner' value '{str(raw).strip()}' is not a recognised company code.",
            ))
    return results


# =============================================================================
# Registries — rules grouped by sheet
# =============================================================================

def rule_lov_customer_group(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L2 — Customer Group must be a valid code.
      TRS = Territory Street Accounts
      TRP = Territory Program
      LCC = Local Contract Customer
      CMU = Corporate Multi Unit
      OTH = Bid & Other
      WHL = Wholesale
      MIS = Miscellaneous

    Applies to: Invoice sheet only.
    """
    rule_name = "Rule C-L2 — Customer Group LOV"
    CUSTOMER_GROUP_LOV = {"TRS", "TRP", "LCC", "CMU", "OTH", "WHL", "MIS"}
    col = "Customer Group"
    results = []
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in CUSTOMER_GROUP_LOV:
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Customer Group' value '{str(raw).strip()}' is invalid. Allowed: {', '.join(sorted(CUSTOMER_GROUP_LOV))}.",
            ))
    return results


def rule_search_name_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-F1 — Search Name - Invoice: ≤20 chars, no spaces, allowed chars only."""
    rule_name = "Rule C-F1 — Search Name - Invoice format"
    col = "Search Name - Invoice"
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
                message=f"Row {excel_row(idx)} — 'Search Name - Invoice' is invalid: {'; '.join(reasons)}.",
            ))
    return results


ALL_INVOICE_RULES: list = [
    rule_lov_intercompany_trading_partner,   # Rule C-L1
    rule_lov_customer_group,                 # Rule C-L2
    rule_search_name_invoice,               # Rule C-F1
]

def rule_lov_division(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L3 — Division must be a valid code.
      BRAKES, COUNTRY_CHOICE, BCE, KFF, FRESH_DIRECT, MEDINA,
      SYSCO_ROI, SYSCO_NI, CLASSIC_DRINKS, READY_CHEF, MENIGO,
      SERVICESTYCKARNA, FRUKTSERVICE, EKOFISK, SYSCO_FRANCE, LAG

    Applies to: LEA_Invoice sheet only.
    """
    rule_name = "Rule C-L3 — Division LOV"
    DIVISION_LOV = {
        "BRAKES", "COUNTRY_CHOICE", "BCE", "KFF", "FRESH_DIRECT", "MEDINA",
        "SYSCO_ROI", "SYSCO_NI", "CLASSIC_DRINKS", "READY_CHEF", "MENIGO",
        "SERVICESTYCKARNA", "FRUKTSERVICE", "EKOFISK", "SYSCO_FRANCE", "LAG",
    }
    col = "Division"
    results = []
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in DIVISION_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Division' value '{str(raw).strip()}' is not a recognised division code.",
            ))
    return results


def rule_lov_method_of_payment(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L4 — Method of Payment must be a valid code.
    C_ prefix = Customer payment methods, V_ prefix = Vendor payment methods.

    Applies to: LEA_Invoice sheet only.
    """
    rule_name = "Rule C-L4 — Method of Payment LOV"
    MOP_LOV = {
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
        if str(raw).strip() not in MOP_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Method of Payment' value '{str(raw).strip()}' is not a recognised payment method code.",
            ))
    return results


def rule_lov_vat_group_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-L7 — VAT Group: I-STD, I-ZERO, I-RED. Applies to LEA_Invoice."""
    rule_name = "Rule C-L7 — VAT Group LOV"
    VAT_LOV = {"I-STD", "I-ZERO", "I-RED"}
    col = "VAT Group"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in VAT_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'VAT Group' value '{str(raw).strip()}' is invalid. Allowed: I-STD, I-ZERO, I-RED.",
            ))
    return results


def rule_lov_seasonal_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-L8 — Seasonal: codes 01–07, 99. Applies to LEA_Invoice."""
    rule_name = "Rule C-L8 — Seasonal LOV"
    SEASONAL_LOV = {"01", "02", "03", "04", "05", "06", "07", "99"}
    col = "Seasonal"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(int(float(str(raw)))).zfill(2) if str(raw).replace(".", "").isdigit() else str(raw).strip()
        if val not in SEASONAL_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Seasonal' value '{val}' is invalid. Allowed: 01–07, 99.",
            ))
    return results


def rule_lov_status_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-L9 — Status: Active, Delisted, Archived. Applies to LEA_Invoice."""
    rule_name = "Rule C-L9 — Status LOV"
    STATUS_LOV = {"Active", "Delisted", "Archived"}
    col = "Status"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in STATUS_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Status' value '{str(raw).strip()}' is invalid. Allowed: Active, Delisted, Archived.",
            ))
    return results


ALL_LEA_INVOICE_RULES: list = [
    rule_lov_division,                # Rule C-L3
    rule_lov_method_of_payment,       # Rule C-L4
    rule_lov_vat_group_lea_invoice,   # Rule C-L7
    rule_lov_seasonal_lea_invoice,    # Rule C-L8
    rule_lov_status_lea_invoice,      # Rule C-L9
]
def rule_search_name_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-F2 — Search Name - Delivery: ≤20 chars, no spaces, allowed chars only."""
    rule_name = "Rule C-F2 — Search Name - Delivery format"
    col = "Search Name  - Delivery"
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
                message=f"Row {excel_row(idx)} — 'Search Name - Delivery' is invalid: {'; '.join(reasons)}.",
            ))
    return results


ALL_OS_RULES: list = [
    rule_search_name_os,   # Rule C-F2
]


def rule_lov_mode_of_delivery(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L5 — Mode Of Delivery must be a valid code.
      3PL, AIR, AMB_TRK, ANY, BACK_HAUL, BICYCLE, BOAT, BULK_CRR,
      COLD_STRG, CONSOL, CONT_SHIP, COURIER, CROSS_DOCK, CUST_COLL,
      DIRECT, DRON_DLV, FROZ_TRK, INTERMOD, PICKUP, PIPELINE,
      REFR_TRK, TRAIN, TRUCK

    Applies to: LEA_OS sheet only.
    """
    rule_name = "Rule C-L5 — Mode Of Delivery LOV"
    MOD_LOV = {
        "3PL", "AIR", "AMB_TRK", "ANY", "BACK_HAUL", "BICYCLE", "BOAT",
        "BULK_CRR", "COLD_STRG", "CONSOL", "CONT_SHIP", "COURIER",
        "CROSS_DOCK", "CUST_COLL", "DIRECT", "DRON_DLV", "FROZ_TRK",
        "INTERMOD", "PICKUP", "PIPELINE", "REFR_TRK", "TRAIN", "TRUCK",
    }
    col = "Mode Of Delivery"
    results = []
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in MOD_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Mode Of Delivery' value '{str(raw).strip()}' is not a recognised delivery mode code.",
            ))
    return results


def rule_lov_delivery_terms(df: pd.DataFrame) -> list[dict]:
    """
    Rule C-L6 — Delivery Terms must be a valid Incoterms code.
      CFR = Cost & Freight (C&F)
      CIF = Cost, Insurance & Freight
      CIP = Carriage & Insurance Paid
      CPT = Carriage Paid To
      DAP = Delivered At Place
      DDP = Delivered Duty Paid
      DPU = Delivered At Place Unloaded
      EXW = Ex Works
      FAS = Free Alongside Ship
      FCA = Free Carrier
      FOB = Free On Board

    Applies to: LEA_OS sheet only.
    """
    rule_name = "Rule C-L6 — Delivery Terms LOV"
    DELIVERY_TERMS_LOV = {"CFR", "CIF", "CIP", "CPT", "DAP", "DDP", "DPU", "EXW", "FAS", "FCA", "FOB"}
    col = "Delivery Terms"
    results = []
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in DELIVERY_TERMS_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Delivery Terms' value '{str(raw).strip()}' is not a recognised Incoterms code. Allowed: {', '.join(sorted(DELIVERY_TERMS_LOV))}.",
            ))
    return results


def rule_lov_seasonal_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L10 — Seasonal: codes 01–07, 99. Applies to LEA_OS."""
    rule_name = "Rule C-L10 — Seasonal LOV"
    SEASONAL_LOV = {"01", "02", "03", "04", "05", "06", "07", "99"}
    col = "Seasonal"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(int(float(str(raw)))).zfill(2) if str(raw).replace(".", "").isdigit() else str(raw).strip()
        if val not in SEASONAL_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Seasonal' value '{val}' is invalid. Allowed: 01–07, 99.",
            ))
    return results


def rule_lov_status_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L11 — Status: Active, Delisted, Archived. Applies to LEA_OS."""
    rule_name = "Rule C-L11 — Status LOV"
    STATUS_LOV = {"Active", "Delisted", "Archived"}
    col = "Status"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in STATUS_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Status' value '{str(raw).strip()}' is invalid. Allowed: Active, Delisted, Archived.",
            ))
    return results


ALL_LEA_OS_RULES: list = [
    rule_lov_mode_of_delivery,   # Rule C-L5
    rule_lov_delivery_terms,     # Rule C-L6
    rule_lov_seasonal_lea_os,    # Rule C-L10
    rule_lov_status_lea_os,      # Rule C-L11
]
ALL_EMP_INVOICE_RULES: list = []
ALL_EMP_OS_RULES:      list = []
ALL_PT_RULES:          list = []
