"""Validation rules for the Global Product Data sheet.

Rules are organised into three categories:
  A. Business Rules   — logical / conditional constraints
  B. Formatting Rules — numeric types, integer checks, field lengths
  C. LOV Rules        — List-of-Values enforcement

Each rule function signature: (df: pd.DataFrame) -> list[dict]
Register new rules in ALL_GLOBAL_RULES at the bottom of this file.
"""

import re
import pandas as pd
from utils.helpers import is_empty, make_result, get_supc, excel_row

SHEET = "Global Product Data"

# =============================================================================
# CONSTANTS — LOVs and column groups
# Update these lists as new values are confirmed by the business.
# =============================================================================

# ---------------------------------------------------------------------------
# Rule 5 — Food product Attribute Group IDs
# Products whose Attribute Group ID is NOT in this set are treated as non-food
# and must have all nutritional columns empty.
# ---------------------------------------------------------------------------
FOOD_ATTRIBUTE_GROUP_IDS = {
    # Grocery / ambient food
    "10000248", "10000249", "10000250", "10000251", "10000252", "10000253",
    # Chilled & frozen
    "10000260", "10000261", "10000262", "10000263",
    # Bakery
    "10000270", "10000271",
    # Produce
    "10000280", "10000281",
    # Meat & seafood
    "10000290", "10000291", "10000292",
    # Dairy
    "10000300", "10000301",
    # Beverages (food-grade)
    "10000310", "10000311",
}

# ---------------------------------------------------------------------------
# LOV — Yes / No columns
# ---------------------------------------------------------------------------
YES_NO_LOV = {"Yes", "No"}

YES_NO_COLS = [
    "Customer Branded",
    "Multi Language Packaging",
    "EU Hub",
    "Constellation",
    "Legally packaged to be sold as a split?",
    "Catch Weight",
    "Dairy Free",
    "Gluten Free",
    "Halal",
    "Kosher",
    "Organic",
    "Vegan",
    "Vegetarian",
    "Biodegradable or Compostable",
    "Recyclable",
    "Hazardous Material",
    "Product Warranty",
    "Perishable Product/Date Tracked",
    "Does Product Have A Taric Code?",
]

# ---------------------------------------------------------------------------
# LOV — Allergen columns (allowed values: 0 = Contains, 1 = May Contain, 2 = Does Not Contain)
# ---------------------------------------------------------------------------
ALLERGEN_LOV = {0, 1, 2}

ALLERGEN_COLS = [
    "Almonds",
    "Barley",
    "Brazil Nuts",
    "Cashew Nuts",
    "Celery and products thereof",
    "Gluten at <gt/> 20 ppm",
    "Crustaceans and products thereof",
    "Eggs and products thereof",
    "Fish and products thereof",
    "Hazelnuts",
    "Kamut",
    "Lupin and products thereof",
    "Macadamia Nuts/Queensland Nuts",
    "Milk and products thereof",
    "Molluscs and products thereof",
    "Mustard and products thereof",
    "Nuts",
    "Oats",
    "Peanuts and products thereof",
    "Pecan Nuts",
    "Pistachio Nuts",
    "Rye",
    "Sesame seeds and products thereof",
    "Soybeans and products thereof",
    "Spelt",
    "Sulphur Dioxide <gt/> 10 ppm",
    "Walnuts",
    "Wheat",
]

# ---------------------------------------------------------------------------
# LOV — Unit of Measure (Stibo IDs)
# Extend this list as new UOM codes are confirmed.
# ---------------------------------------------------------------------------
UOM_LOV = {"GM", "ML", "KG", "EA", "L", "CL", "DL", "LB", "OZ"}

UOM_COLS = [
    "Case UOM",
    "Split UOM",
]

# ---------------------------------------------------------------------------
# LOV — Item Group
# Extend this list as new Item Group codes are confirmed.
# ---------------------------------------------------------------------------
ITEM_GROUP_LOV = {
    "FG-Freezer",
    "FG-Dry",
    "FG-Cooler",
    "FG-Ambient",
}

# ---------------------------------------------------------------------------
# LOV — Nutritional Unit (Stibo IDs)
# Extend this list as new codes are confirmed.
# ---------------------------------------------------------------------------
NUTRITIONAL_UNIT_LOV = {"G", "ML"}

# ---------------------------------------------------------------------------
# Mandatory columns — must be non-null/non-empty for every row
# ---------------------------------------------------------------------------
MANDATORY_COLS = [
    "SUPC",
    "Attribute Group ID",
    "Brand Key",
    "Customer Branded",
    "Sysco Finance Category",
    "True Vendor Name",
    "First & Second Word",
    "Marketing Description",
    "Warehouse Description",
    "Invoice Description",
    "Item Group",
    "Item Model Group Id",
    "Multi Language Packaging",
    "EU Hub",
    "Constellation",
    "Case Pack",
    "Case Size",
    "Case UOM",
    "Legally packaged to be sold as a split?",
    "Case Net Weight",
    "Case Length",
    "Case Width",
    "Case Height",
    "Catch Weight",
    "Cases per Layer (Standard Pallet)",
    "Layers per Pallet (Standard Pallet)",
    "Dairy Free",
    "Gluten Free",
    "Halal",
    "Kosher",
    "Organic",
    "Vegan",
    "Vegetarian",
    "Biodegradable or Compostable",
    "Recyclable",
    "Hazardous Material",
    "Product Warranty",
    "Perishable Product/Date Tracked",
    "Shelf Life Period In Days (Manufacturer)",
    "Shelf Life Period in Days (Sysco)",
    "Does Product Have A Taric Code?",
    "Country Of Origin - Manufactured",
    "Country Of Origin - Packed",
    "Country Of Origin - Sold From",
    "Country Of Origin - Raw Ingredients",
]

# ---------------------------------------------------------------------------
# Split attributes — required when sold as a split
# ---------------------------------------------------------------------------
SPLIT_REQUIRED_COLS = [
    "GTIN-Inner",
    "Split Pack",
    "Split Size",
    "Split UOM",
    "Split Net Weight",
    "Split Tare Weight",
    "Split Length",
    "Split Width",
    "Split Height",
    "Splits Per Case",
]

SPLIT_DIMENSION_PAIRS = [
    ("Split Length", "Case Length"),
    ("Split Width", "Case Width"),
    ("Split Height", "Case Height"),
    ("Split Net Weight", "Case Net Weight"),
]

# ---------------------------------------------------------------------------
# Numeric-only columns (must be numeric, no specific decimal constraint)
# ---------------------------------------------------------------------------
NUMERIC_COLS = [
    "Case Size",
    "Split Size",
    "Case Net Weight",
    "Case Tare Weight",
    "Case True Net Weight (Drained/Glazed)",
    "Case Catch Weight Range From",
    "Case Catch Weight Range To",
    "Split Net Weight",
    "Split Tare Weight",
    "Split True Net Weight (Drained/Glazed)",
    "Case Length",
    "Case Width",
    "Case Height",
    "Split Length",
    "Split Width",
    "Split Height",
    "Energy Kcal",
    "Energy KJ",
    "Fat",
    "Of which Saturates",
    "Of which Mono-Unsaturates",
    "Of which Polyunsaturates",
    "Of which Trans Fats",
    "Carbohydrate",
    "Of which Sugars",
    "Of which Polyols",
    "Of which Starch",
    "Fibre",
    "Protein",
    "Salt",
    "Sodium",
]

# ---------------------------------------------------------------------------
# Integer-only columns (must be whole numbers)
# ---------------------------------------------------------------------------
INTEGER_COLS = [
    "SUPC",
    "Case Pack",
    "Split Pack",
    "Splits Per Case",
    "Cases per Layer (Standard Pallet)",
    "Layers per Pallet (Standard Pallet)",
    "Cases per Layer (Euro Pallet)",
    "Layers per Pallet (Euro Pallet)",
    "Shelf Life Period In Days (Manufacturer)",
    "Shelf Life Period in Days (Sysco)",
    "Shelf Life Period in Days (Customer)",
]

# ---------------------------------------------------------------------------
# Country of Origin columns — must be ISO 3166-1 alpha-2 (2 uppercase letters)
# ---------------------------------------------------------------------------
COUNTRY_OF_ORIGIN_COLS = [
    "Country Of Origin - Manufactured",
    "Country Of Origin - Packed",
    "Country Of Origin - Sold From",
    "Country Of Origin - Raw Ingredients",
]

# Nutritional columns (for Rule 5)
NUTRITIONAL_COLS = [
    "Energy Kcal", "Energy KJ", "Fat", "Of which Saturates",
    "Of which Mono-Unsaturates", "Of which Polyunsaturates", "Of which Trans Fats",
    "Carbohydrate", "Of which Sugars", "Of which Polyols", "Of which Starch",
    "Fibre", "Protein", "Salt", "Sodium",
]

# Column name shorthands
COL_SOLD_AS_SPLIT = "Legally packaged to be sold as a split?"
COL_GTIN_OUTER = "GTIN-Outer"
COL_GTIN_INNER = "GTIN-Inner"
COL_SHELF_CUSTOMER = "Shelf Life Period in Days (Customer)"
COL_SHELF_SYSCO = "Shelf Life Period in Days (Sysco)"
COL_SHELF_MANUFACTURER = "Shelf Life Period In Days (Manufacturer)"
COL_ATTRIBUTE_GROUP_ID = "Attribute Group ID"
COL_CATCH_WEIGHT = "Catch Weight"
COL_CATCH_FROM = "Case Catch Weight Range From"
COL_CATCH_TO = "Case Catch Weight Range To"
COL_HAS_TARIC = "Does Product Have A Taric Code?"
COL_TARIC = "Taric Code/Commodity Code"

VALID_GTIN_LENGTHS = {8, 12, 13, 14}


# =============================================================================
# A. BUSINESS RULES
# =============================================================================

def rule_split_attributes_required(df: pd.DataFrame) -> list[dict]:
    """
    Rule 1 — Split attributes required when sold as split.
    If 'Legally packaged to be sold as a split?' == 'Yes', all split attribute
    columns must be non-null and non-empty.
    """
    rule_name = "Rule 1 — Split attributes required when sold as split"
    results = []
    if COL_SOLD_AS_SPLIT not in df.columns:
        return results

    available = [c for c in SPLIT_REQUIRED_COLS if c in df.columns]
    split_rows = df[df[COL_SOLD_AS_SPLIT].astype(str).str.strip() == "Yes"]

    for idx, row in split_rows.iterrows():
        missing = [c for c in available if is_empty(row.get(c))]
        if missing:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Split product is missing required split attribute(s): {', '.join(missing)}",
            ))
    return results


def rule_split_dimensions_within_case(df: pd.DataFrame) -> list[dict]:
    """
    Rule 2 — Split dimensions must not exceed Case dimensions.
    Split Length/Width/Height/Net Weight must be ≤ their Case equivalents.
    Only checked when both values are present.
    """
    rule_name = "Rule 2 — Split dimensions must not exceed Case dimensions"
    results = []
    if COL_SOLD_AS_SPLIT not in df.columns:
        return results

    split_rows = df[df[COL_SOLD_AS_SPLIT].astype(str).str.strip() == "Yes"]
    for idx, row in split_rows.iterrows():
        for split_col, case_col in SPLIT_DIMENSION_PAIRS:
            if split_col not in df.columns or case_col not in df.columns:
                continue
            split_val, case_val = row.get(split_col), row.get(case_col)
            if is_empty(split_val) or is_empty(case_val):
                continue
            try:
                split_num, case_num = float(split_val), float(case_val)
            except (ValueError, TypeError):
                continue
            if split_num > case_num:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — {split_col} ({split_num}) exceeds {case_col} ({case_num})",
                ))
    return results


def rule_shelf_life_order(df: pd.DataFrame) -> list[dict]:
    """
    Rule 4 — Shelf Life order.
    When all three values are present: Customer < Sysco < Manufacturer.
    """
    rule_name = "Rule 4 — Shelf Life order"
    results = []
    required = [COL_SHELF_CUSTOMER, COL_SHELF_SYSCO, COL_SHELF_MANUFACTURER]
    if any(c not in df.columns for c in required):
        return results

    for idx, row in df.iterrows():
        c_raw, s_raw, m_raw = row.get(COL_SHELF_CUSTOMER), row.get(COL_SHELF_SYSCO), row.get(COL_SHELF_MANUFACTURER)
        if is_empty(c_raw) or is_empty(s_raw) or is_empty(m_raw):
            continue
        try:
            c, s, m = int(float(c_raw)), int(float(s_raw)), int(float(m_raw))
        except (ValueError, TypeError):
            continue
        if not (c < s < m):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Shelf Life order invalid: Customer ({c}) must be < Sysco ({s}) must be < Manufacturer ({m})",
            ))
    return results


def rule_no_nutrition_for_non_food(df: pd.DataFrame) -> list[dict]:
    """
    Rule 5 — Nutritional data must be empty for non-food products.
    If Attribute Group ID is not in FOOD_ATTRIBUTE_GROUP_IDS, all nutritional
    columns must be null or empty.
    """
    rule_name = "Rule 5 — Nutritional data must be empty for non-food products"
    results = []
    if COL_ATTRIBUTE_GROUP_ID not in df.columns:
        return results

    available_nutrition = [c for c in NUTRITIONAL_COLS if c in df.columns]
    for idx, row in df.iterrows():
        attr_id = row.get(COL_ATTRIBUTE_GROUP_ID)
        if is_empty(attr_id):
            continue
        if str(attr_id).strip() in FOOD_ATTRIBUTE_GROUP_IDS:
            continue
        if any(not is_empty(row.get(c)) for c in available_nutrition):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Non-food product (Attribute Group ID: {str(attr_id).strip()}) has nutritional data populated",
            ))
    return results


def rule_catch_weight_conditional(df: pd.DataFrame) -> list[dict]:
    """
    Rule 8 — Catch Weight range required when Catch Weight is Yes.
    If 'Catch Weight' == 'Yes', then both range fields must be populated.
    """
    rule_name = "Rule 8 — Catch Weight range required"
    results = []
    if COL_CATCH_WEIGHT not in df.columns:
        return results

    catch_rows = df[df[COL_CATCH_WEIGHT].astype(str).str.strip() == "Yes"]
    for idx, row in catch_rows.iterrows():
        missing = []
        if COL_CATCH_FROM in df.columns and is_empty(row.get(COL_CATCH_FROM)):
            missing.append(COL_CATCH_FROM)
        if COL_CATCH_TO in df.columns and is_empty(row.get(COL_CATCH_TO)):
            missing.append(COL_CATCH_TO)
        if missing:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Catch Weight product is missing: {', '.join(missing)}",
            ))
    return results


def rule_taric_code_conditional(df: pd.DataFrame) -> list[dict]:
    """
    Rule 9 — Taric Code required when 'Does Product Have A Taric Code?' is Yes.
    """
    rule_name = "Rule 9 — Taric Code required when flagged"
    results = []
    if COL_HAS_TARIC not in df.columns:
        return results

    taric_rows = df[df[COL_HAS_TARIC].astype(str).str.strip() == "Yes"]
    for idx, row in taric_rows.iterrows():
        if COL_TARIC in df.columns and is_empty(row.get(COL_TARIC)):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Does Product Have A Taric Code?' is Yes but '{COL_TARIC}' is empty",
            ))
    return results


def rule_mandatory_fields(df: pd.DataFrame) -> list[dict]:
    """
    Rule 10 — Mandatory fields must be populated.
    All columns listed in MANDATORY_COLS must be non-null and non-empty.
    """
    rule_name = "Rule 10 — Mandatory fields"
    results = []
    present = [c for c in MANDATORY_COLS if c in df.columns]

    for idx, row in df.iterrows():
        missing = [c for c in present if is_empty(row.get(c))]
        if missing:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Missing mandatory field(s): {', '.join(missing)}",
            ))
    return results


# =============================================================================
# B. FORMATTING RULES
# =============================================================================

def rule_gtin_outer_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule 3 — GTIN-Outer format.
    Must be numeric and exactly 8, 12, 13, or 14 digits.
    Null/empty values are skipped.
    """
    rule_name = "Rule 3 — GTIN-Outer format"
    results = []
    if COL_GTIN_OUTER not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_GTIN_OUTER)
        if is_empty(raw):
            continue
        gtin_str = str(int(raw)) if isinstance(raw, float) and raw == int(raw) else str(raw).strip()
        if not re.fullmatch(r"\d+", gtin_str) or len(gtin_str) not in VALID_GTIN_LENGTHS:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — GTIN-Outer '{gtin_str}' is invalid. Must be 8, 12, 13 or 14 digits.",
            ))
    return results


def rule_gtin_inner_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule F1 — GTIN-Inner format.
    When populated, must be numeric and exactly 8, 12, 13, or 14 digits.
    """
    rule_name = "Rule F1 — GTIN-Inner format"
    results = []
    if COL_GTIN_INNER not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_GTIN_INNER)
        if is_empty(raw):
            continue
        gtin_str = str(int(raw)) if isinstance(raw, float) and raw == int(raw) else str(raw).strip()
        if not re.fullmatch(r"\d+", gtin_str) or len(gtin_str) not in VALID_GTIN_LENGTHS:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — GTIN-Inner '{gtin_str}' is invalid. Must be 8, 12, 13 or 14 digits.",
            ))
    return results


def rule_attribute_group_id_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule F2 — Attribute Group ID must be exactly 8 digits.
    """
    rule_name = "Rule F2 — Attribute Group ID format"
    results = []
    if COL_ATTRIBUTE_GROUP_ID not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_ATTRIBUTE_GROUP_ID)
        if is_empty(raw):
            continue
        val_str = str(int(raw)) if isinstance(raw, float) and raw == int(raw) else str(raw).strip()
        if not re.fullmatch(r"\d{8}", val_str):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Attribute Group ID '{val_str}' must be exactly 8 digits.",
            ))
    return results


def rule_taric_code_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule F3 — Taric Code/Commodity Code must be exactly 8 digits when populated.
    """
    rule_name = "Rule F3 — Taric Code format"
    results = []
    if COL_TARIC not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_TARIC)
        if is_empty(raw):
            continue
        val_str = str(int(raw)) if isinstance(raw, float) and raw == int(raw) else str(raw).strip()
        if not re.fullmatch(r"\d{8}", val_str):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Taric Code '{val_str}' must be exactly 8 digits.",
            ))
    return results


def rule_integer_fields(df: pd.DataFrame) -> list[dict]:
    """
    Rule F4 — Integer fields must be whole numbers.
    Columns listed in INTEGER_COLS must not have decimal parts when populated.
    """
    rule_name = "Rule F4 — Integer fields must be whole numbers"
    results = []
    present = [c for c in INTEGER_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            try:
                num = float(raw)
            except (ValueError, TypeError):
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' must be a whole number, got '{raw}'",
                ))
                continue
            if num != int(num):
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' must be a whole number, got '{raw}'",
                ))
    return results


def rule_numeric_fields(df: pd.DataFrame) -> list[dict]:
    """
    Rule F5 — Numeric fields must be valid numbers.
    Columns listed in NUMERIC_COLS must parse as float when populated.
    """
    rule_name = "Rule F5 — Numeric fields must be valid numbers"
    results = []
    present = [c for c in NUMERIC_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            try:
                float(raw)
            except (ValueError, TypeError):
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' must be a number, got '{raw}'",
                ))
    return results


def rule_country_of_origin_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule F6 — Country of Origin must be a valid ISO 3166-1 alpha-2 code (2 uppercase letters).
    """
    rule_name = "Rule F6 — Country of Origin format"
    results = []
    present = [c for c in COUNTRY_OF_ORIGIN_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            val_str = str(raw).strip()
            if not re.fullmatch(r"[A-Z]{2}", val_str):
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{val_str}' must be a 2-letter ISO country code (e.g. GB, FR, DE).",
                ))
    return results


# =============================================================================
# C. LOV RULES
# =============================================================================

def rule_lov_yes_no(df: pd.DataFrame) -> list[dict]:
    """
    Rule L1 — Yes/No columns must contain only 'Yes' or 'No'.
    """
    rule_name = "Rule L1 — Yes/No LOV"
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
                    message=f"Row {excel_row(idx)} — '{col}' value '{raw}' is invalid. Allowed values: Yes, No.",
                ))
    return results


def rule_lov_allergens(df: pd.DataFrame) -> list[dict]:
    """
    Rule L2 — Allergen columns must contain only 0, 1, or 2.
      0 = Contains  |  1 = May Contain  |  2 = Does Not Contain
    """
    rule_name = "Rule L2 — Allergen LOV (0, 1, 2)"
    results = []
    present = [c for c in ALLERGEN_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            try:
                int_val = int(float(raw))
            except (ValueError, TypeError):
                int_val = None

            if int_val not in ALLERGEN_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{raw}' is invalid. Allowed values: 0 (Contains), 1 (May Contain), 2 (Does Not Contain).",
                ))
    return results


def rule_lov_uom(df: pd.DataFrame) -> list[dict]:
    """
    Rule L3 — Unit of Measure columns must contain a valid Stibo UOM code.
    Allowed: GM, ML, KG, EA, L, CL, DL, LB, OZ (extend UOM_LOV as needed).
    """
    rule_name = "Rule L3 — UOM LOV"
    results = []
    present = [c for c in UOM_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in UOM_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{raw}' is not a recognised UOM code. Allowed: {', '.join(sorted(UOM_LOV))}.",
                ))
    return results


def rule_lov_item_group(df: pd.DataFrame) -> list[dict]:
    """
    Rule L4 — Item Group must be one of the allowed values.
    Extend ITEM_GROUP_LOV as new codes are confirmed.
    """
    rule_name = "Rule L4 — Item Group LOV"
    results = []
    col = "Item Group"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in ITEM_GROUP_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Item Group' value '{raw}' is invalid. Allowed: {', '.join(sorted(ITEM_GROUP_LOV))}.",
            ))
    return results


def rule_lov_nutritional_unit(df: pd.DataFrame) -> list[dict]:
    """
    Rule L5 — Nutritional Unit must be 'G' or 'ML' when populated.
    Extend NUTRITIONAL_UNIT_LOV as new codes are confirmed.
    """
    rule_name = "Rule L5 — Nutritional Unit LOV"
    results = []
    col = "Nutritional Unit"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in NUTRITIONAL_UNIT_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Nutritional Unit' value '{raw}' is invalid. Allowed: {', '.join(sorted(NUTRITIONAL_UNIT_LOV))}.",
            ))
    return results


# =============================================================================
# Registry — all global rules in execution order
# =============================================================================

ALL_GLOBAL_RULES = [
    # A. Business Rules
    rule_split_attributes_required,       # Rule 1
    rule_split_dimensions_within_case,    # Rule 2
    rule_shelf_life_order,                # Rule 4
    rule_no_nutrition_for_non_food,       # Rule 5
    rule_catch_weight_conditional,        # Rule 8
    rule_taric_code_conditional,          # Rule 9
    rule_mandatory_fields,               # Rule 10
    # B. Formatting Rules
    rule_gtin_outer_format,              # Rule 3 / F0
    rule_gtin_inner_format,              # Rule F1
    rule_attribute_group_id_format,      # Rule F2
    rule_taric_code_format,              # Rule F3
    rule_integer_fields,                 # Rule F4
    rule_numeric_fields,                 # Rule F5
    rule_country_of_origin_format,       # Rule F6
    # C. LOV Rules
    rule_lov_yes_no,                     # Rule L1
    rule_lov_allergens,                  # Rule L2
    rule_lov_uom,                        # Rule L3
    rule_lov_item_group,                 # Rule L4
    rule_lov_nutritional_unit,           # Rule L5
]
