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
from rules.vendor_rules import LEGAL_ENTITY_LOV, ISO2_COUNTRY_LOV, COST_CENTRE_LOV, WAREHOUSE_CODE_LOV

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

def rule_unique_step_id_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-U1 — Step ID must be unique within the Invoice sheet."""
    rule_name = "Rule C-U1 — Step ID uniqueness"
    col = "Step ID"
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
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Step ID '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


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


def rule_lov_country_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-L14 — Country must be a valid ISO 3166-1 alpha-2 code (Invoice)."""
    rule_name = "Rule C-L14 — Country ISO-2 LOV"
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


def rule_lov_customer_type(df: pd.DataFrame) -> list[dict]:
    """Rule C-L18 — Customer Type must be 'Customer' or 'Employee'."""
    rule_name = "Rule C-L18 — Customer Type LOV"
    LOV = {"Customer", "Employee"}
    col = "Customer Type"
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
                message=f"Row {excel_row(idx)} — 'Customer Type' value '{str(raw).strip()}' is invalid. Allowed: Customer, Employee.",
            ))
    return results


def rule_employee_fields_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-B1 — When Customer Type = 'Employee':
       Required (must be filled):   First Name, Last Name, Employee Number.
       Must be empty: Invoice Customer Name, VAT Registration Number,
                      Legal Name - Invoice, Search Name - Invoice, Limited Address.
       Is Customer a Registered Company must be 'No' → Company Registration Number must be empty.
    """
    rule_name = "Rule C-B1 — Employee fields conditional"
    col_type = "Customer Type"
    results = []
    if col_type not in df.columns:
        return results

    REQUIRED = ["First Name", "Last Name", "Employee Number"]
    MUST_BE_EMPTY = [
        "Invoice Customer Name", "VAT Registration Number",
        "Legal Name - Invoice", "Search Name - Invoice", "Limited Address",
        "Company Registration Number",
    ]

    for idx, row in df.iterrows():
        if str(row.get(col_type, "")).strip() != "Employee":
            continue

        # Fields that must be filled
        for col in REQUIRED:
            if col in df.columns and is_empty(row.get(col)):
                results.append(make_result(
                    sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — Customer Type is 'Employee' but '{col}' is empty.",
                ))

        # Fields that must be empty
        for col in MUST_BE_EMPTY:
            if col in df.columns and not is_empty(row.get(col)):
                results.append(make_result(
                    sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — Customer Type is 'Employee' but '{col}' must be empty.",
                ))

        # Is Customer a Registered Company must be 'No'
        col_reg = "Is Customer a Registered Company"
        if col_reg in df.columns and not is_empty(row.get(col_reg)):
            if str(row.get(col_reg, "")).strip() != "No":
                results.append(make_result(
                    sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — Customer Type is 'Employee' but 'Is Customer a Registered Company' must be 'No'.",
                ))

    return results


def rule_lov_is_registered_company(df: pd.DataFrame) -> list[dict]:
    """Rule C-L19 — 'Is Customer a Registered Company' must be 'Yes' or 'No'."""
    rule_name = "Rule C-L19 — Is Customer a Registered Company LOV"
    LOV = {"Yes", "No"}
    col = "Is Customer a Registered Company"
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
                message=f"Row {excel_row(idx)} — 'Is Customer a Registered Company' value '{str(raw).strip()}' is invalid. Allowed: Yes, No.",
            ))
    return results


def rule_company_registration_conditional(df: pd.DataFrame) -> list[dict]:
    """Rule C-B2 — If 'Is Customer a Registered Company' = 'Yes', then
       'Company Registration Number' must be filled.
    """
    rule_name = "Rule C-B2 — Company Registration Number conditional"
    col_reg = "Is Customer a Registered Company"
    col_crn = "Company Registration Number"
    results = []
    if col_reg not in df.columns or col_crn not in df.columns:
        return results
    for idx, row in df.iterrows():
        if str(row.get(col_reg, "")).strip() == "Yes" and is_empty(row.get(col_crn)):
            results.append(make_result(
                sheet=SHEET_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Is Customer a Registered Company' is Yes but 'Company Registration Number' is empty.",
            ))
    return results


ALL_INVOICE_RULES: list = [
    rule_unique_step_id_invoice,             # Rule C-U1
    rule_lov_intercompany_trading_partner,   # Rule C-L1
    rule_lov_customer_group,                 # Rule C-L2
    rule_lov_country_invoice,                # Rule C-L14
    rule_search_name_invoice,                # Rule C-F1
    rule_lov_customer_type,                  # Rule C-L18
    rule_employee_fields_invoice,            # Rule C-B1
    rule_lov_is_registered_company,          # Rule C-L19
    rule_company_registration_conditional,   # Rule C-B2
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


def rule_lov_legal_entity_lea_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-L12 — Legal Entity must be a valid entity name (LEA Invoice)."""
    rule_name = "Rule C-L12 — Legal Entity LOV"
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
    """Rule C-L17 — Cost Centre must be a valid cost centre code (LEA Invoice)."""
    rule_name = "Rule C-L17 — Cost Centre LOV"
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


ALL_LEA_INVOICE_RULES: list = [
    rule_lov_legal_entity_lea_invoice,  # Rule C-L12
    rule_lov_division,                  # Rule C-L3
    rule_lov_method_of_payment,         # Rule C-L4
    rule_lov_vat_group_lea_invoice,     # Rule C-L7
    rule_lov_seasonal_lea_invoice,      # Rule C-L8
    rule_lov_status_lea_invoice,        # Rule C-L9
    rule_lov_cost_centre_lea_invoice,   # Rule C-L17
]
def rule_lov_segment(df: pd.DataFrame) -> list[dict]:
    """Rule C-L25 — Segment must be a valid segment code (OS)."""
    rule_name = "Rule C-L25 — Segment LOV"
    col = "Segment"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in SEGMENT_LOV:
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Segment' value '{str(raw).strip()}' is not a recognised segment code. Allowed: {', '.join(sorted(SEGMENT_LOV))}.",
            ))
    return results


def rule_lov_subsegment(df: pd.DataFrame) -> list[dict]:
    """Rule C-L26 — Subsegment must be a valid subsegment code (OS)."""
    rule_name = "Rule C-L26 — Subsegment LOV"
    col = "Subsegment"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in SUBSEGMENT_LOV:
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Subsegment' value '{str(raw).strip()}' is not a recognised subsegment code.",
            ))
    return results


def rule_lov_company_prefix_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L22 — Company Prefix in OS must be a valid code (same LOV as PT)."""
    rule_name = "Rule C-L22 — Company Prefix LOV"
    col = "Company Prefix"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in COMPANY_PREFIX_LOV:
            results.append(make_result(
                sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Company Prefix' value '{str(raw).strip()}' is not a recognised prefix. Allowed: {', '.join(sorted(COMPANY_PREFIX_LOV))}.",
            ))
    return results


def rule_unique_ordering_shipping_code_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-U3 — Ordering/Shipping Customer Code must be unique within the OS sheet."""
    rule_name = "Rule C-U3 — Ordering/Shipping Customer Code uniqueness"
    col = "Ordering/Shipping Customer Code"
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
                message=f"Row {excel_row(idx)} — 'Ordering/Shipping Customer Code' '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


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


def rule_lov_country_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L15 — Country must be a valid ISO 3166-1 alpha-2 code (OS)."""
    rule_name = "Rule C-L15 — Country ISO-2 LOV"
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


def rule_employee_fields_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-B3 — When First Name AND Last Name are both filled (employee row):
       'Ordering/Shipping Customer Name', 'Legal Name - Delivery', and
       'Search Name  - Delivery' must be empty.
    """
    rule_name = "Rule C-B3 — Employee OS fields conditional"
    col_first = "First Name"
    col_last  = "Last Name"
    MUST_BE_EMPTY = [
        "Ordering/Shipping Customer Name",
        "Legal Name - Delivery",
        "Search Name  - Delivery",
    ]
    results = []
    if col_first not in df.columns or col_last not in df.columns:
        return results
    for idx, row in df.iterrows():
        if is_empty(row.get(col_first)) or is_empty(row.get(col_last)):
            continue  # not an employee row
        for col in MUST_BE_EMPTY:
            if col in df.columns and not is_empty(row.get(col)):
                results.append(make_result(
                    sheet=SHEET_OS, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — First Name and Last Name are filled (employee) but '{col}' must be empty.",
                ))
    return results


ALL_OS_RULES: list = [
    rule_lov_company_prefix_os,               # Rule C-L22
    rule_unique_ordering_shipping_code_os,    # Rule C-U3
    rule_lov_country_os,                      # Rule C-L15
    rule_search_name_os,                      # Rule C-F2
    rule_employee_fields_os,                  # Rule C-B3
    rule_lov_segment,                         # Rule C-L25
    rule_lov_subsegment,                      # Rule C-L26
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


COMPANY_PREFIX_LOV: set[str] = {
    "GBBR", "GBFD", "GBKF", "GBMD",
    "SWME", "SWEK", "SWFS", "SWSS",
    "IRRI", "IRNI", "IRRC", "IRCD",
    "FRFR", "FRLG",
}

SEGMENT_LOV: dict[str, str] = {
    "EDU":  "Education",
    "HEA":  "Healthcare",
    "LOD":  "Lodging",
    "NTR":  "Non Trade",
    "OTH":  "Other Food Locations",
    "REC":  "Recreation",
    "RES":  "Restaurant",
    "PUB":  "Pubs & Bars",
    "RET":  "Retail Food",
    "MISC": "Miscellaneous",
}

SUBSEGMENT_LOV: dict[str, str] = {
    # Education (EDU)
    "E10": "University",
    "E11": "College",
    "E12": "Education Centre",
    "E20": "Private - Primary",
    "E21": "Private - Secondary",
    "E22": "Nursery",
    "E23": "Primary",
    "E24": "Secondary",
    # Healthcare (HEA)
    "H10": "Hospitals - Public",
    "H11": "Hospitals - Private",
    "H20": "Long Term Care",
    "H30": "Other",
    "H40": "Retirement Communities",
    # Lodging (LOD)
    "L10": "Bed & Breakfast",
    "L20": "Hotels & Motels - Full Serve",
    "L30": "Hotels & Motels - Limited Service",
    "L40": "Other Lodging",
    "L50": "Resorts",
    # Non Trade (NTR)
    "N10": "Competitors",
    "N20": "Employee",
    "N30": "Sysco Intercompany",
    "N40": "Sysco Internal",
    "N50": "Vendors",
    # Other Food Locations (OTH)
    "O10": "Cafeterias & Corporate Dining",
    "O15": "Construction, Logging, Oil, Mining Camps",
    "O20": "Correction Facilities",
    "O25": "Ghost Kitchen",
    "O26": "Contract Distrib",
    "O30": "Government",
    "O35": "Military",
    "O40": "Other",
    "O45": "Production Facilities",
    "O50": "Shelters & Food Banks",
    "O55": "Transportation",
    "O60": "First Nations",
    "O65": "Export",
    # Recreation (REC)
    "S05": "Arena, Stadiums, Ballparks",
    "S10": "Casino & Gambling",
    "S15": "Catering",
    "S20": "Golf Courses",
    "S25": "Indoor Sports (Bowl, Fitness, Rec Ctr, etc)",
    "S30": "Museums & Art Locations",
    "S35": "Nightclub / Lounge",
    "S40": "Other Clubs & Recreation",
    "S45": "Outdoor Sports (Bike, Ski, Soccer, etc)",
    "S50": "Recreational Camps",
    "S55": "Shipping & Cruise Lines",
    "S60": "Theatre (Cinema or Live)",
    "S65": "Wineries",
    # Restaurant (RES)
    "R05": "Casual Dining",
    "R10": "Fast Casual inc Café & Snack Bar",
    "R11": "Cafes inc Coffee, Tea Shops and Snack Bars",
    "R15": "Fine Dining",
    "R20": "Food Trucks, Street Vendors, Mobile Caterers",
    "R25": "Quick Serve inc Takeaway, Grab & Go",
    # Pubs & Bars (PUB)
    "P30": "Pubs & Bars (Food Led)",
    "P31": "Pubs & Bars (Drink Led)",
    # Retail Food (RET)
    "T05": "Bakery",
    "T06": "Bake Off",
    "T10": "C-Store & Gas Stations",
    "T15": "Meat, Deli, Groceries - Halal",
    "T20": "Meat, Deli, Groceries - Non Halal",
    "T25": "Non Grocery Retailer",
    "T30": "Retail Grocers",
    "T35": "Symbol Groups",
    "T40": "Truckloads",
    "T50": "Sysco @ Home",
    # Miscellaneous (MISC)
    "M0":  "Miscellaneous",
}

SALES_AREA_MANAGER_LOV: dict[str, str] = {
    "ASM20000": "Andrew Collins",
    "ASM20001": "Andy Newland",
    "ASM20002": "Cameron Downes",
    "ASM20003": "Chris Jeffery",
    "ASM20004": "Cory Williams",
    "ASM20005": "Dan Scott",
    "ASM20006": "Distribution",
    "ASM20007": "Emma Foster",
    "ASM20008": "Festival",
    "ASM20009": "Lance Griffiths",
    "ASM20010": "Private",
    "ASM20011": "Simon Humphrey",
    "ASM20012": "Steve Ross",
    "ASM20013": "Suppliers",
    "ASM20014": "Unallocated",
    "ASM20015": "Vacant Mainland",
    "ASM20016": "Jack Norris",
    "ASM20017": "Jennifer Ford",
    "ASM20018": "Staff Sales",
    "ASM20019": "Reka Elford",
    "ASM20020": "Martin Bigwood",
    "ASM25000": "Anders Rudefors Berg",
    "ASM25001": "Carolin Nilsson",
    "ASM25002": "Fredrik Gastineau",
    "ASM25003": "Jay Tran",
    "ASM25004": "Jesper Askild",
    "ASM25005": "Ken Mannerström",
    "ASM25006": "Samuel Wallin",
    "ASM25007": "Vakant",
    "ASM25008": "Staff Sales",
}


def rule_lov_warehouse_code(df: pd.DataFrame) -> list[dict]:
    """Rule C-L23 — Warehouse Code must be a valid warehouse code (LEA OS)."""
    rule_name = "Rule C-L23 — Warehouse Code LOV"
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


def rule_lov_sales_area_manager_code(df: pd.DataFrame) -> list[dict]:
    """Rule C-L24 — Sales Area Manager Code must be a valid ASM code (LEA OS)."""
    rule_name = "Rule C-L24 — Sales Area Manager Code LOV"
    col = "Sales Area Manager Code"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in SALES_AREA_MANAGER_LOV:
            results.append(make_result(
                sheet=SHEET_LEA_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Sales Area Manager Code' value '{str(raw).strip()}' is not a recognised ASM code.",
            ))
    return results


def rule_unique_ordering_shipping_code_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-U4 — Ordering/Shipping Customer Code must be unique within the LEA OS sheet."""
    rule_name = "Rule C-U4 — Ordering/Shipping Customer Code uniqueness"
    col = "Ordering/Shipping Customer Code"
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
                message=f"Row {excel_row(idx)} — 'Ordering/Shipping Customer Code' '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


def rule_lov_legal_entity_lea_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L13 — Legal Entity must be a valid entity name (LEA OS)."""
    rule_name = "Rule C-L13 — Legal Entity LOV"
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


ALL_LEA_OS_RULES: list = [
    rule_unique_ordering_shipping_code_lea_os,  # Rule C-U4
    rule_lov_legal_entity_lea_os,               # Rule C-L13
    rule_lov_mode_of_delivery,                  # Rule C-L5
    rule_lov_delivery_terms,                    # Rule C-L6
    rule_lov_seasonal_lea_os,                   # Rule C-L10
    rule_lov_status_lea_os,                     # Rule C-L11
    rule_lov_warehouse_code,                    # Rule C-L23
    rule_lov_sales_area_manager_code,           # Rule C-L24
]
def rule_unique_step_id_emp_invoice(df: pd.DataFrame) -> list[dict]:
    """Rule C-U2 — STEP ID must be unique within the Employee Invoice sheet."""
    rule_name = "Rule C-U2 — STEP ID uniqueness"
    col = "STEP ID"
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
                sheet=SHEET_EMP_INVOICE, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — STEP ID '{val}' is a duplicate (first seen at row {seen[val]}).",
            ))
        else:
            seen[val] = excel_row(idx)
    return results


ALL_EMP_INVOICE_RULES: list = [
    rule_unique_step_id_emp_invoice,  # Rule C-U2
]


def rule_lov_copy_invoice_code(df: pd.DataFrame) -> list[dict]:
    """Rule C-L20 — Copy Invoice Code must be 'Yes' or 'No' (Employee OS)."""
    rule_name = "Rule C-L20 — Copy Invoice Code LOV"
    LOV = {"Yes", "No"}
    col = "Copy Invoice Code"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_EMP_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Copy Invoice Code' value '{str(raw).strip()}' is invalid. Allowed: Yes, No.",
            ))
    return results


def rule_lov_copy_invoice_address(df: pd.DataFrame) -> list[dict]:
    """Rule C-L21 — Copy Invoice Address must be 'Yes' or 'No' (Employee OS)."""
    rule_name = "Rule C-L21 — Copy Invoice Address LOV"
    LOV = {"Yes", "No"}
    col = "Copy Invoice Address"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in LOV:
            results.append(make_result(
                sheet=SHEET_EMP_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Copy Invoice Address' value '{str(raw).strip()}' is invalid. Allowed: Yes, No.",
            ))
    return results


# Cross-sheet rule — called directly from validator.py with two DataFrames.
ADDRESS_FIELDS = [
    "Address Line 1", "Address Line 2", "Town/City",
    "County/District", "Zip/PostalCode", "Country",
]


def rule_copy_invoice_address_match(
    df_emp_os: pd.DataFrame,
    df_invoice: pd.DataFrame,
) -> list[dict]:
    """Rule C-B4 — When 'Copy Invoice Address' = 'Yes' in Employee OS, all address
    fields must exactly match the corresponding Invoice row (matched by
    'Invoice Customer Code' in Employee OS → 'EU Master Customer Code' in Invoice).
    """
    rule_name = "Rule C-B4 — Copy Invoice Address match"
    col_flag   = "Copy Invoice Address"
    col_emp_id = "Invoice Customer Code"
    col_inv_id = "EU Master Customer Code"

    results = []
    if col_flag not in df_emp_os.columns or col_emp_id not in df_emp_os.columns:
        return results
    if col_inv_id not in df_invoice.columns:
        return results

    # Build lookup: EU Master Customer Code → row dict
    invoice_lookup: dict[str, dict] = {}
    for _, inv_row in df_invoice.iterrows():
        key_raw = inv_row.get(col_inv_id)
        if is_empty(key_raw):
            continue
        key = str(key_raw).strip()
        if key.endswith(".0"):
            key = key[:-2]
        invoice_lookup[key] = inv_row.to_dict()

    for idx, row in df_emp_os.iterrows():
        if str(row.get(col_flag, "")).strip() != "Yes":
            continue

        emp_id_raw = row.get(col_emp_id)
        if is_empty(emp_id_raw):
            continue
        emp_id = str(emp_id_raw).strip()
        if emp_id.endswith(".0"):
            emp_id = emp_id[:-2]

        inv_row = invoice_lookup.get(emp_id)
        if inv_row is None:
            results.append(make_result(
                sheet=SHEET_EMP_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Copy Invoice Address' is Yes but no matching Invoice row found for Invoice Customer Code '{emp_id}'.",
            ))
            continue

        for field in ADDRESS_FIELDS:
            emp_val = str(row.get(field, "") or "").strip()
            inv_val = str(inv_row.get(field, "") or "").strip()
            if emp_val != inv_val:
                results.append(make_result(
                    sheet=SHEET_EMP_OS, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=(
                        f"Row {excel_row(idx)} — 'Copy Invoice Address' is Yes but '{field}' "
                        f"does not match Invoice (Employee OS: '{emp_val}', Invoice: '{inv_val}')."
                    ),
                ))
    return results


def rule_lov_invoice_company_prefix_emp_os(df: pd.DataFrame) -> list[dict]:
    """Rule C-L27 — Invoice Company Prefix in Employee OS must be a valid code (same LOV as PT/OS Company Prefix)."""
    rule_name = "Rule C-L27 — Invoice Company Prefix LOV"
    col = "Invoice Company Prefix"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in COMPANY_PREFIX_LOV:
            results.append(make_result(
                sheet=SHEET_EMP_OS, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Invoice Company Prefix' value '{str(raw).strip()}' is not a recognised prefix. Allowed: {', '.join(sorted(COMPANY_PREFIX_LOV))}.",
            ))
    return results


ALL_EMP_OS_RULES: list = [
    rule_lov_invoice_company_prefix_emp_os,  # Rule C-L27
    rule_lov_copy_invoice_code,              # Rule C-L20
    rule_lov_copy_invoice_address,           # Rule C-L21
]


def rule_lov_company_prefix(df: pd.DataFrame) -> list[dict]:
    """Rule C-L16 — Company Prefix must be a valid code (PT sheet)."""
    rule_name = "Rule C-L16 — Company Prefix LOV"
    col = "Company Prefix"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in COMPANY_PREFIX_LOV:
            results.append(make_result(
                sheet=SHEET_PT, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Company Prefix' value '{str(raw).strip()}' is not a recognised prefix. Allowed: {', '.join(sorted(COMPANY_PREFIX_LOV))}.",
            ))
    return results


ALL_PT_RULES: list = [
    rule_lov_company_prefix,   # Rule C-L16
]
