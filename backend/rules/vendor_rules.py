"""Validation rules for Vendor domain templates.

Vendor migration files contain 4 sheets:
  Invoice, LEA_Invoice, OS, LEA_OS

Each rule function signature: (df: pd.DataFrame) -> list[dict]
Register new rules in the appropriate list at the bottom of this file.
"""

import re
from pathlib import Path
import pandas as pd
from utils.helpers import is_empty, make_result, get_supc, excel_row

SHEET_INVOICE     = "Invoice"
SHEET_LEA_INVOICE = "LEA_Invoice"
SHEET_OS          = "OS"
SHEET_LEA_OS      = "LEA_OS"

# Legal Entity LOV — shared across Vendor and Customer domains
LEGAL_ENTITY_LOV = {
    "Brakes", "Fresh_Direct", "Medina", "Classic_Drinks", "Sysco_France",
    "LAG", "Ekofisk", "Sysco_ROI", "Sysco_Northern_Ireland", "Fruktservice",
    "KFF", "Menigo", "Ready_Chef",
}

# ISO 3166-1 alpha-2 country codes — shared across all domains
ISO2_COUNTRY_LOV = {
    "AF","AX","AL","DZ","AS","AD","AO","AI","AQ","AG","AR","AM","AW","AU","AT",
    "AZ","BS","BH","BD","BB","BY","BE","BZ","BJ","BM","BT","BO","BQ","BA","BW",
    "BV","BR","IO","BN","BG","BF","BI","CV","KH","CM","CA","KY","CF","TD","CL",
    "CN","CX","CC","CO","KM","CG","CD","CK","CR","CI","HR","CU","CW","CY","CZ",
    "DK","DJ","DM","DO","EC","EG","SV","GQ","ER","EE","SZ","ET","FK","FO","FJ",
    "FI","FR","GF","PF","TF","GA","GM","GE","DE","GH","GI","GR","GL","GD","GP",
    "GU","GT","GG","GN","GW","GY","HT","HM","VA","HN","HK","HU","IS","IN","ID",
    "IR","IQ","IE","IM","IL","IT","JM","JP","JE","JO","KZ","KE","KI","KP","KR",
    "KW","KG","LA","LV","LB","LS","LR","LY","LI","LT","LU","MO","MG","MW","MY",
    "MV","ML","MT","MH","MQ","MR","MU","YT","MX","FM","MD","MC","MN","ME","MS",
    "MA","MZ","MM","NA","NR","NP","NL","NC","NZ","NI","NE","NG","NU","NF","MK",
    "MP","NO","OM","PK","PW","PS","PA","PG","PY","PE","PH","PN","PL","PT","PR",
    "QA","RE","RO","RU","RW","BL","SH","KN","LC","MF","PM","VC","WS","SM","ST",
    "SA","SN","RS","SC","SL","SG","SX","SK","SI","SB","SO","ZA","GS","SS","ES",
    "LK","SD","SR","SJ","SE","CH","SY","TW","TJ","TZ","TH","TL","TG","TK","TO",
    "TT","TN","TR","TM","TC","TV","UG","UA","AE","GB","UM","US","UY","UZ","VU",
    "VE","VN","VG","VI","WF","EH","YE","ZM","ZW",
}

# Cost Centre LOV — shared across Vendor and Customer LEA Invoice templates
COST_CENTRE_LOV = {
    "W10025", "W10075",                          # Warehouse
    "T15005", "T15015",                          # Transportation
    "N20015", "N20005", "N20020", "N20050",      # Maintenance
    "P50890",                                    # Production
    "E55999", "E55074",                          # Business Technology
    "A30899",                                    # Administration
    "R45831",                                    # Merchandising
    "F35005",                                    # Finance
    "I65005",                                    # Strategic Initiatives
    "H40005",                                    # Human Resources
    "C70999",                                    # Supply Chain
    "X75005",                                    # Executive
    "A30099",                                    # Certain Items - G&A
    "S25070", "S25845", "S25846", "S25847",      # Sales
    "S25849", "S25850", "S25855", "S25999",      # Sales (continued)
    "S25305",                                    # Certain Items - Sales
}

def _load_item_buyer_group_lov() -> set[str]:
    """Load valid Item Buyer Group IDs from reference/Buyer Group.xlsx.
    Falls back to empty set if the file is missing (rule skipped gracefully).
    """
    ref_path = Path(__file__).resolve().parent.parent.parent / "reference" / "Buyer Group.xlsx"
    if not ref_path.exists():
        return set()
    df = pd.read_excel(str(ref_path), sheet_name=0, header=None)
    ids: set[str] = set()
    for val in df.iloc[2:, 1].dropna():   # column index 1 = ID
        ids.add(str(val).strip())
    return ids


ITEM_BUYER_GROUP_LOV: set[str] = _load_item_buyer_group_lov()

# Warehouse Code LOV — shared across Vendor and Customer LEA OS templates
WAREHOUSE_CODE_LOV: dict[str, str] = {
    "IW001": "Local Isle of Wight",
    "MK001": "Millbrook",
    "EK001": "Ekofisk",
}


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

def rule_step_id_unique(df: pd.DataFrame) -> list[dict]:
    """Rule V-U1 — StepID must be unique within the Invoice sheet."""
    rule_name = "Rule V-U1 — StepID uniqueness"
    col = "StepID"
    results = []
    if col not in df.columns:
        return results
    dupes = df[df.duplicated(subset=[col], keep=False)]
    for idx, row in dupes.iterrows():
        val = row.get(col)
        if is_empty(val):
            continue
        results.append(make_result(
            sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
            rule=rule_name,
            message=f"Row {excel_row(idx)} — StepID '{str(val).strip()}' is duplicated.",
        ))
    return results


def rule_mandatory_address_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-B1 — Address Line 1, Town/City, Zip/Postal Code are mandatory in Invoice."""
    rule_name = "Rule V-B1 — Mandatory address fields"
    mandatory = ["Address Line 1", "Town/City", "Zip/Postal Code"]
    results = []
    present = [c for c in mandatory if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            if is_empty(row.get(col)):
                results.append(make_result(
                    sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' is mandatory but empty.",
                ))
    return results


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


def rule_lov_country_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-L11 — Country must be a valid ISO 3166-1 alpha-2 code (Invoice)."""
    rule_name = "Rule V-L11 — Country ISO-2 LOV"
    col = "Country"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip().upper() not in ISO2_COUNTRY_LOV:
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Country' value '{str(raw).strip()}' is not a valid ISO 3166-1 alpha-2 code.",
            ))
    return results


def rule_lov_trade_indirect_vendor(df: pd.DataFrame) -> list[dict]:
    """Rule V-L9 — Trade/Indirect Vendor must be 'Trade' or 'Indirect'."""
    rule_name = "Rule V-L9 — Trade/Indirect Vendor LOV"
    LOV = {"Trade", "Indirect"}
    col = "Trade/Indirect Vendor"
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
                message=f"Row {excel_row(idx)} — 'Trade/Indirect Vendor' value '{str(raw).strip()}' is invalid. Allowed: Trade, Indirect.",
            ))
    return results


def rule_company_registration_number(df: pd.DataFrame) -> list[dict]:
    """Rule V-B2 — Company Registration Number is mandatory and must be unique."""
    rule_name = "Rule V-B2 — Company Registration Number"
    col = "Company Registration Number"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        if is_empty(row.get(col)):
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Company Registration Number' is mandatory but empty.",
            ))
    dupes = df[df.duplicated(subset=[col], keep=False)]
    for idx, row in dupes.iterrows():
        val = row.get(col)
        if is_empty(val):
            continue
        results.append(make_result(
            sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
            rule=rule_name,
            message=f"Row {excel_row(idx)} — 'Company Registration Number' '{str(val).strip()}' is duplicated.",
        ))
    return results


ALL_INVOICE_RULES: list = [
    rule_step_id_unique,                # Rule V-U1
    rule_mandatory_address_invoice,     # Rule V-B1
    rule_company_registration_number,   # Rule V-B2
    rule_lov_intercompany_invoice,      # Rule V-L1
    rule_lov_trade_indirect_vendor,     # Rule V-L9
    rule_lov_country_invoice,           # Rule V-L11
    rule_search_name_invoice,           # Rule V-F1
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


def rule_lov_legal_entity_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-L8 — Legal Entity must be a valid entity name (LEA Invoice)."""
    rule_name = "Rule V-L8 — Legal Entity LOV"
    col = "Legal Entity"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LEGAL_ENTITY_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Legal Entity' value '{str(raw).strip()}' is not a recognised entity. Allowed: {', '.join(sorted(LEGAL_ENTITY_LOV))}.",
            ))
    return results


def rule_lov_cost_centre_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-L13 — Cost Centre must be a valid cost centre code (LEA Invoice)."""
    rule_name = "Rule V-L13 — Cost Centre LOV"
    col = "Cost Centre"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in COST_CENTRE_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Cost Centre' value '{str(raw).strip()}' is not a recognised cost centre code.",
            ))
    return results


def rule_unique_suvc_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule V-U2 — SUVC Invoice must be unique within the LEA Invoice sheet."""
    rule_name = "Rule V-U2 — SUVC Invoice uniqueness"
    col = "SUVC Invoice"
    results = []
    if col not in df.columns:
        return results
    seen: dict[str, int] = {}
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(raw).strip()
        if val.endswith(".0"):
            val = val[:-2]
        if val in seen:
            results.append(make_result(
                sheet=SHEET_LEA_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'SUVC Invoice' '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


ALL_LEA_INVOICE_RULES: list = [
    rule_unique_suvc_invoice,           # Rule V-U2
    rule_lov_legal_entity_lea_invoice,  # Rule V-L8
    rule_lov_method_of_payment,         # Rule V-L2
    rule_lov_vat_group,                 # Rule V-L3
    rule_lov_status_lea_invoice,        # Rule V-L4
    rule_lov_cost_centre_lea_invoice,   # Rule V-L13
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


def rule_lov_country_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-L12 — Country must be a valid ISO 3166-1 alpha-2 code (OS)."""
    rule_name = "Rule V-L12 — Country ISO-2 LOV"
    col = "Country"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip().upper() not in ISO2_COUNTRY_LOV:
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Country' value '{str(raw).strip()}' is not a valid ISO 3166-1 alpha-2 code.",
            ))
    return results


def rule_unique_suvc_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-U3 — SUVC Ordering/Shipping must be unique within the OS sheet."""
    rule_name = "Rule V-U3 — SUVC Ordering/Shipping uniqueness"
    col = "SUVC Ordering/Shipping"
    results = []
    if col not in df.columns:
        return results
    seen: dict[str, int] = {}
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(raw).strip()
        if val.endswith(".0"):
            val = val[:-2]
        if val in seen:
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'SUVC Ordering/Shipping' '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


ALL_OS_RULES: list = [
    rule_unique_suvc_os,   # Rule V-U3
    rule_lov_country_os,   # Rule V-L12
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


def rule_lov_legal_entity_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-L10 — Legal Entity must be a valid entity name (LEA OS)."""
    rule_name = "Rule V-L10 — Legal Entity LOV"
    col = "Legal Entity"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LEGAL_ENTITY_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Legal Entity' value '{str(raw).strip()}' is not a recognised entity. Allowed: {', '.join(sorted(LEGAL_ENTITY_LOV))}.",
            ))
    return results


def rule_unique_suvc_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-U4 — SUVC Ordering/Shipping must be unique within the LEA OS sheet."""
    rule_name = "Rule V-U4 — SUVC Ordering/Shipping uniqueness"
    col = "SUVC Ordering/Shipping"
    results = []
    if col not in df.columns:
        return results
    seen: dict[str, int] = {}
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(raw).strip()
        if val.endswith(".0"):
            val = val[:-2]
        if val in seen:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'SUVC Ordering/Shipping' '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


def rule_lov_warehouse_code_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule V-L15 — Warehouse Code must be a valid warehouse code (LEA OS)."""
    rule_name = "Rule V-L15 — Warehouse Code LOV"
    col = "Warehouse Code"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in WAREHOUSE_CODE_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Warehouse Code' value '{str(raw).strip()}' is not a recognised warehouse code. Allowed: {', '.join(sorted(WAREHOUSE_CODE_LOV))}.",
            ))
    return results


def rule_lov_buyer_group(df: pd.DataFrame) -> list[dict]:
    """Rule V-L14 — Buyer Group must be a valid ID from reference/Buyer Group.xlsx (same LOV as Local Product Data Item Buyer Group)."""
    rule_name = "Rule V-L14 — Buyer Group LOV"
    col = "Buyer Group"
    results = []
    if not ITEM_BUYER_GROUP_LOV:
        return results   # reference file not available — skip gracefully
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in ITEM_BUYER_GROUP_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Buyer Group' value '{str(raw).strip()}' is not a recognised buyer group ID.",
            ))
    return results


ALL_LEA_OS_RULES: list = [
    rule_unique_suvc_lea_os,       # Rule V-U4
    rule_lov_legal_entity_lea_os,  # Rule V-L10
    rule_lov_delivery_terms,       # Rule V-L5
    rule_lov_mode_of_delivery,     # Rule V-L6
    rule_lov_status_lea_os,            # Rule V-L7
    rule_lov_buyer_group,              # Rule V-L14
    rule_lov_warehouse_code_lea_os,    # Rule V-L15
]
