"""Validation rules for the Local Product Data sheet.

Each rule function signature: (df: pd.DataFrame) -> list[dict]
Register new rules in ALL_LOCAL_RULES at the bottom of this file.
"""

import re
import pandas as pd
from utils.helpers import is_empty, make_result, get_supc, excel_row
from rules.vendor_rules import LEGAL_ENTITY_LOV, ITEM_BUYER_GROUP_LOV

SHEET = "Local Product Data"


# =============================================================================
# LOVs
# =============================================================================

STATUS_LOV       = {"Active", "Delisted", "Archived"}
YES_NO_LOV       = {"Yes", "No"}
TEMPERATURE_LOV  = {"TEMP18", "TEMP0", "TEMP5", "TEMP8"}
ITEM_VAT_LOV     = {"I-STD", "I-ZERO", "I-RED"}

YES_NO_COLS      = ["Proprietary Product?", "Split Product"]
TEMPERATURE_COLS = ["Min Temperature", "Max Temperature"]
ITEM_VAT_COLS    = ["Item VAT - Purchasing", "Item VAT - Selling"]

STORAGE_AREA_LOV = {"F", "C", "D"}   # F=Freezer, C=Cooler, D=Dry

PRODUCT_SOURCE_TYPE_LOV = {"STOCKED", "JUST_IN_TIME", "LEAD_TIME", "MAKE_TO_ORDER"}

ECOM_HIERARCHY_LOV = {
    "1000100","1000110","1000120","1000130","1000140","1000150","1000160","1000170","1000180","1000190","1000200","1000210",
    "1100100","1100110","1100120","1100130","1100140","1100150","1100160","1100170","1100180","1100190","1100200","1100210",
    "1100220","1100230","1100240","1100250","1100260","1100270","1100280","1100290","1100300","1100310","1100320","1100330","1100340",
    "1200100","1200110","1200120","1200130","1200140","1200150","1200160","1200170","1200180","1200190","1200200",
    "1300100","1300110","1300120","1300130","1300140","1300150","1300160","1300170","1300180","1300190","1300200","1300210","1300220","1300230","1300240","1300250","1300260",
    "1400100","1400110","1400120","1400130","1400140","1400150","1400160","1400170","1400180",
    "1500100","1500110","1500120","1500130","1500140","1500150","1500160",
    "1600100","1600110","1600120","1600130","1600140","1600150","1600160","1600170","1600180","1600190","1600200","1600210","1600220",
    "1700100","1700110","1700120","1700130","1700140","1700150","1700160","1700170","1700180","1700190","1700200","1700210","1700220","1700230","1700240","1700250","1700260",
    "1800100","1800110","1800120","1800130","1800140","1800150","1800160","1800170","1800180","1800190","1800200","1800210",
    "1900100","1900110","1900120","1900130","1900140","1900150","1900160","1900170","1900180","1900190","1900200","1900210","1900220","1900230","1900240","1900250","1900260","1900270","1900280",
    "2000100","2000110","2000120","2000130",
    "2100100","2100110","2100120","2100130","2100140",
    "2200100","2200110","2200120","2200130","2200140","2200150","2200160","2200170","2200180","2200190","2200200","2200210",
    "2300100","2300110","2300120",
    "2400100","2400110","2400120","2400130","2400140","2400150","2400160","2400170",
    "2500100","2500110","2500120","2500130","2500140","2500150","2500160","2500170","2500180","2500190","2500200","2500210",
    "2600100","2600110","2600120","2600130",
    "2700100","2700110","2700120","2700130","2700140","2700150","2700160","2700170","2700180","2700190","2700200",
    "2800100","2800110","2800120","2800130","2800140","2800150","2800160","2800170","2800180",
    "2900100","2900110","2900120","2900130","2900140","2900150","2900160",
}

# Free-text columns subject to the same special-character rule as Global F7
_ACCENTS = "áÁàÀâÂäÄåÅæÆçÇéÉèÈêÊëËíÍìÌîÎïÏñÑóÓòÒôÔöÖúÚùÙûÛüÜßÿØÝ"
_SPECIAL  = r"%&()*+\-./™®Ø"
_TEXT_ALLOWED_RE  = re.compile(rf"^[a-zA-Z0-9{_ACCENTS} {_SPECIAL}]*$")
_TEXT_ALLOWED_CHR = re.compile(rf"[a-zA-Z0-9{_ACCENTS} {_SPECIAL}]")

TEXT_COLS = ["Local Product Description", "Ecom Description"]


# =============================================================================
# Rules
# =============================================================================

def rule_supc_unique(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-U0 — SUPC must be unique within the Local Product Data sheet."""
    rule_name = "Rule LCL-U0 — SUPC uniqueness"
    col = "SUPC"
    results = []
    if col not in df.columns:
        return results
    dupes = df[df.duplicated(subset=[col], keep=False)]
    for idx, row in dupes.iterrows():
        val = row.get(col)
        if is_empty(val):
            continue
        results.append(make_result(
            sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
            rule=rule_name,
            message=f"Row {excel_row(idx)} — SUPC '{str(val).strip()}' is duplicated.",
        ))
    return results


def rule_step_id_unique(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-U1 — STEP ID must be unique within the Local Product Data sheet."""
    rule_name = "Rule LCL-U1 — STEP ID uniqueness"
    col = "STEP ID"
    results = []
    if col not in df.columns:
        return results
    dupes = df[df.duplicated(subset=[col], keep=False)]
    for idx, row in dupes.iterrows():
        val = row.get(col)
        if is_empty(val):
            continue
        results.append(make_result(
            sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
            rule=rule_name,
            message=f"Row {excel_row(idx)} — STEP ID '{str(val).strip()}' is duplicated.",
        ))
    return results


def rule_text_special_chars(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-F1 — Free-text columns must not contain disallowed special characters.

    Applies to: Ecom Description (same allowed set as Global Rule F7).
    """
    rule_name = "Rule LCL-F1 — Special characters"
    results = []
    present = [c for c in TEXT_COLS if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            val_str = str(raw)
            if not _TEXT_ALLOWED_RE.match(val_str):
                bad_chars = sorted({ch for ch in val_str if not _TEXT_ALLOWED_CHR.match(ch)})
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' contains disallowed character(s): {bad_chars}.",
                ))
    return results


def rule_lov_legal_entity(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L1 — Legal Entity must be a valid entity name."""
    rule_name = "Rule LCL-L1 — Legal Entity LOV"
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
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Legal Entity' value '{str(raw).strip()}' is not a recognised entity. Allowed: {', '.join(sorted(LEGAL_ENTITY_LOV))}.",
            ))
    return results


def rule_lov_status(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L2 — Status: Active, Delisted, Archived."""
    rule_name = "Rule LCL-L2 — Status LOV"
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
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Status' value '{str(raw).strip()}' is invalid. Allowed: Active, Delisted, Archived.",
            ))
    return results


def rule_lov_yes_no(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L3 — Yes/No fields: Proprietary Product?, Split Product."""
    rule_name = "Rule LCL-L3 — Yes/No LOV"
    results = []
    present = [c for c in YES_NO_COLS if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in YES_NO_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: Yes, No.",
                ))
    return results


def rule_lov_temperature(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L4 — Min/Max Temperature must be a valid temperature code."""
    rule_name = "Rule LCL-L4 — Temperature LOV"
    results = []
    present = [c for c in TEMPERATURE_COLS if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in TEMPERATURE_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: TEMP18 (-18°C), TEMP0 (0°C), TEMP5 (5°C), TEMP8 (8°C).",
                ))
    return results


def rule_lov_item_vat(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L5 — Item VAT (Purchasing + Selling): I-STD, I-ZERO, I-RED."""
    rule_name = "Rule LCL-L5 — Item VAT LOV"
    results = []
    present = [c for c in ITEM_VAT_COLS if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in ITEM_VAT_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: I-STD, I-ZERO, I-RED.",
                ))
    return results


def rule_lov_ecom_hierarchy(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L9 — Ecom Hierarchy Level 2 ID must be a valid code."""
    rule_name = "Rule LCL-L9 — Ecom Hierarchy Level 2 ID LOV"
    col = "Ecom Hierarchy Level 2 ID"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        # Normalise: Excel may read as integer/float
        val = str(raw).strip()
        if val.endswith(".0"):
            val = val[:-2]
        if val not in ECOM_HIERARCHY_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Ecom Hierarchy Level 2 ID' value '{val}' is not a recognised hierarchy code.",
            ))
    return results


def rule_lov_product_source_type(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L8 — Product Source Type: STOCKED, JUST_IN_TIME, LEAD_TIME, MAKE_TO_ORDER."""
    rule_name = "Rule LCL-L8 — Product Source Type LOV"
    col = "Product Source Type"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in PRODUCT_SOURCE_TYPE_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Product Source Type' value '{str(raw).strip()}' is invalid. Allowed: STOCKED (Stocked), JUST_IN_TIME (Just In Time), LEAD_TIME (Lead Time), MAKE_TO_ORDER (Make to Order).",
            ))
    return results


def rule_lov_storage_area(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L7 — Storage Area: F (Freezer), C (Cooler), D (Dry)."""
    rule_name = "Rule LCL-L7 — Storage Area LOV"
    col = "Storage Area"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in STORAGE_AREA_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Storage Area' value '{str(raw).strip()}' is invalid. Allowed: F (Freezer), C (Cooler), D (Dry).",
            ))
    return results


def rule_lov_item_buyer_group(df: pd.DataFrame) -> list[dict]:
    """Rule LCL-L6 — Item Buyer Group must be a valid ID from reference/Buyer Group.xlsx."""
    rule_name = "Rule LCL-L6 — Item Buyer Group LOV"
    col = "Item Buyer Group"
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
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Item Buyer Group' value '{str(raw).strip()}' is not a recognised buyer group ID.",
            ))
    return results


# =============================================================================
# Registry — all local rules in execution order
# =============================================================================

ALL_LOCAL_RULES: list = [
    rule_supc_unique,           # Rule LCL-U0
    rule_step_id_unique,        # Rule LCL-U1
    rule_text_special_chars,    # Rule LCL-F1
    rule_lov_legal_entity,      # Rule LCL-L1
    rule_lov_status,            # Rule LCL-L2
    rule_lov_yes_no,            # Rule LCL-L3
    rule_lov_temperature,       # Rule LCL-L4
    rule_lov_item_vat,          # Rule LCL-L5
    rule_lov_ecom_hierarchy,        # Rule LCL-L9
    rule_lov_product_source_type,  # Rule LCL-L8
    rule_lov_storage_area,         # Rule LCL-L7
    rule_lov_item_buyer_group,  # Rule LCL-L6
]
