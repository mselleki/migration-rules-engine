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
# Source: Stibo Master Data Dictionary MVP & Phase 1 (LOVs sheet)
# Update these lists as new values are confirmed by the business.
# =============================================================================

# ---------------------------------------------------------------------------
# Attribute Group ID — full OSD Hierarchy LOV
# IDs are stored as 8-character zero-padded strings (e.g. "01010100").
# Excel may drop the leading zero and store as integer — normalise before check.
# ---------------------------------------------------------------------------
def _load_attribute_group_lov() -> set[str]:
    """Load valid Attribute Group IDs from reference/Attribute Group.xlsx.
    Falls back to an empty set if the file is missing (rule will be skipped gracefully).
    """
    from pathlib import Path
    ref_path = Path(__file__).resolve().parent.parent.parent / "reference" / "Attribute Group.xlsx"
    if not ref_path.exists():
        return set()
    import pandas as pd
    df = pd.read_excel(str(ref_path), sheet_name="Attributes Group", header=None)
    ids: set[str] = set()
    for val in df.iloc[2:, 3].dropna():
        raw = str(val).strip()
        ids.add(str(int(float(raw))).zfill(8) if raw.replace(".", "").isdigit() else raw)
    return ids


ATTRIBUTE_GROUP_ID_LOV = _load_attribute_group_lov()


# ---------------------------------------------------------------------------
# Brand Key — valid Sysco Own Brand codes + Vendor Brand codes
# ---------------------------------------------------------------------------
def _load_brand_lov() -> set[str]:
    """Load valid brand codes from reference/Brands.xlsx.
    A Brand Key is valid if it matches either a Sysco Own Brand Code (col 0)
    or a Vendor Brand Code (col 3). Falls back to empty set if file is missing.
    """
    from pathlib import Path
    ref_path = Path(__file__).resolve().parent.parent.parent / "reference" / "Brands.xlsx"
    if not ref_path.exists():
        return set()
    import pandas as pd
    df = pd.read_excel(str(ref_path), sheet_name=0, header=None)
    codes: set[str] = set()
    for val in df.iloc[2:, 0].dropna():  # Sysco Brand Codes
        codes.add(str(val).strip())
    for val in df.iloc[2:, 3].dropna():  # Vendor Brand Codes
        codes.add(str(val).strip())
    return codes


BRAND_KEY_LOV = _load_brand_lov()

# ---------------------------------------------------------------------------
# Rule 5 — Food product Attribute Group IDs
# Products whose Attribute Group ID IS in this set are treated as food.
# All other IDs (Administrative, Disposables, Supplies & Equipment) are non-food
# and must have all nutritional columns empty.
# Non-food Business Centres: ADMINISTRATIVE (01xxxxxx), DISPOSABLES (10xxxxxx),
#                             SUPPLIES & EQUIPMENT (18xxxxxx)
# ---------------------------------------------------------------------------
FOOD_ATTRIBUTE_GROUP_IDS = {
    # Business Centre 02 — Bakery & Pastry
    "02010100",
    "02020100", "02020200", "02020300", "02020400", "02020500", "02020600", "02020700", "02020800",
    "02030100", "02030200", "02030300",
    "02040100",
    "02050100", "02050200", "02050300",
    "02060100", "02060200",
    "02070100", "02070200", "02070300",
    # Business Centre 03 — Dairy & Eggs
    "03010100",
    "03020100", "03020200", "03020300", "03020400", "03020500", "03020600", "03020700",
    "03030100", "03030200", "03030300", "03030400", "03030500",
    "03040100", "03040200", "03040300", "03040400",
    "03050100", "03050200",
    "03060100", "03060200", "03060300", "03060400", "03060500", "03060600", "03060700",
    "03060900", "03061000",
    "03070100", "03070200", "03070300", "03070400", "03070500", "03070600", "03070700",
    "03080100", "03080200", "03080300", "03080400", "03080500",
    "03090100", "03090200", "03090300", "03090400", "03090500", "03090600", "03090700",
    "03100100",
    "03110100", "03110200",
    "03120100", "03120200",
    # Business Centre 04 — Deli & Charcuterie
    "04010200", "04010300", "04010400", "04010500",
    "04020100",
    "04030100",
    "04040100", "04040200", "04040300",
    "04050100",
    "04060100", "04060200", "04060300", "04060400", "04060500",
    "04070100", "04070200",
    "04080200", "04080300",
    "04090100", "04090200", "04090300",
    # Business Centre 05 — Dry Grocery
    "05010100", "05010200", "05010300",
    "05020400", "05020500", "05020600", "05020700", "05020800", "05020900", "05021000",
    "05021100", "05021200", "05021300",
    "05030300",
    "05040100", "05040200", "05040300", "05040400", "05040500", "05040600", "05040700",
    "05040800", "05040900", "05041000", "05041100", "05041200", "05041300", "05041400",
    "05041500",
    # Business Centre 06 — Fish & Seafood
    "06010100", "06010200", "06010300",
    "06020100", "06020200", "06020300", "06020400", "06020500", "06020600", "06020700",
    "06030100",
    "06040100",
    "06050100",
    "06060100", "06060200", "06060300", "06060400", "06060500", "06060600", "06060700",
    "06060800", "06060900",
    "06070100",
    "06080100", "06080200", "06080300",
    # Business Centre 07 — Frozen
    "07010200",
    "07020100",
    "07030100", "07030200", "07030300", "07030400", "07030500", "07030600",
    "07040100", "07040200", "07040300",
    "07050100", "07050200",
    # Business Centre 08 — Fruit & Vegetables
    "08010100", "08010200", "08010300", "08010400",
    "08020100", "08020200", "08020300",
    "08030100", "08030200",
    "08040100", "08040200",
    "08050100",
    "08060100", "08060200",
    "08070100",
    "08080100", "08080200",
    "08090100", "08090200",
    # Business Centre 09 — Meat & Poultry
    "09010100",
    "09020100",
    "09030100", "09030200", "09030300",
    "09040100", "09040200",
    "09050200", "09050300", "09050400", "09050500", "09050600", "09050700", "09050800",
    "09050900", "09051000", "09051100", "09051300", "09051400", "09051500", "09051600",
    "09060100", "09060200", "09060300", "09060400",
    "09070100", "09070200", "09070300", "09070400",
    "09080100", "09080200", "09080300",
    "09090200",
    "09100100", "09100200",
    "09110100", "09110200", "09110300",
    "09120600",
    # Business Centre 11 — Beverages
    "11010100", "11010300", "11010400", "11010500", "11010600", "11010700", "11010800", "11010900",
    "11021100", "11021200", "11021300", "11021400", "11021500", "11021600", "11021700",
    "11021800", "11021900", "11022000", "11022100", "11022200", "11022300", "11022400",
    # Business Centre 12 — Condiments & Sauces
    "12010100",
    "12020100",
    # Business Centre 13 — Snacks & Confectionery
    "13010100",
    "13020100", "13020200", "13020300", "13020400", "13020500", "13020600", "13020700",
    "13020800", "13020900",
    "13030100", "13030200", "13030300", "13030400", "13030500", "13030600", "13030700",
    "13030800", "13030900",
    "13050100", "13050200",
    "13060100", "13060200",
    "13070100",
    "13080100", "13080200", "13080300", "13080400", "13080500", "13080600", "13080700",
    "13080800",
    "13090100", "13090200", "13090300",
    "13100100",
    "13110100",
    "13120100", "13120200", "13120300",
    "13130100", "13130200",
    "13140100",
    "13150100", "13150200",
    "13160100",
    "13170100", "13170200", "13170300", "13170400", "13170500",
    "13180200",
    "13190100",
    "13200100", "13200200", "13200300", "13200400",
    "13210100", "13210200", "13210300",
    "13220100", "13220200", "13220300", "13220400", "13220500", "13220600", "13220700",
    "13220800",
    "13230100",
    "13240200", "13240300", "13240400", "13240500",
    "13250200",
    "13260100",
    "13270100",
    # Business Centre 14 — Speciality Foods
    "14010100", "14010200", "14010300",
    "14020100", "14020200", "14020300", "14020400", "14020500", "14020600", "14020700",
    "14020800",
    "14030100", "14030200",
    "14040100", "14040200",
    "14050100", "14050200",
    "14060100", "14060300", "14060400", "14060500", "14060600", "14060700", "14060800",
    "14060900",
    "14070100", "14070200",
    "14080100", "14080200", "14080300", "14080400", "14080500",
    "14090200", "14090300", "14090400",
    "14100100", "14100200", "14100300",
    # Business Centre 15 — Ambient & Chilled Meals
    "15010100",
    "15020100", "15020200",
    "15030100", "15030200",
    "15040100", "15040200",
    "15050100", "15050200", "15050300", "15050400", "15050500", "15050600", "15050700",
    "15050800", "15050900",
    "15060100", "15060200", "15060300", "15060400", "15060500", "15060600", "15060700",
    "15060800", "15060900", "15061000", "15061100",
    "15070100", "15070200", "15070300", "15070400",
    "15080100", "15080200", "15080300", "15080400", "15080500", "15080600", "15080700",
    "15090100", "15090200", "15090300", "15090400", "15090500",
    "15100100", "15100200",
    "15110700", "15110800", "15110900", "15111000", "15111100",
    # Business Centre 16 — Oils, Fats & Dressings
    "16010100",
    "16020100", "16020200", "16020300", "16020400", "16020500", "16020600", "16020700",
    "16020800", "16020900", "16021000", "16021100",
    "16030100",
    "16040100",
    "16050100",
    "16060100",
    "16070100", "16070200", "16070300", "16070400", "16070500", "16070600", "16070700",
    "16070800", "16070900", "16071000", "16071100", "16071200", "16071300", "16071400",
    "16071500", "16071600", "16071700", "16071800",
    # Business Centre 17 — Bread & Morning Goods
    "17010100", "17010200",
    "17020100",
    "17030100", "17030200", "17030300", "17030400", "17030500", "17030600", "17030700",
    "17030800", "17030900", "17031000", "17031100",
    "17040100",
    "17050100", "17050200", "17050300", "17050400", "17050500", "17050600",
    "17060100", "17060200",
    # Business Centre 19 — Catering Ingredients
    "19010100", "19010200", "19010300", "19010400",
    "19020100", "19020200",
    "19030100",
    "19040100", "19040200", "19040300", "19040400", "19040500", "19040600", "19040700",
    "19040800", "19040900", "19041000", "19041100",
    "19050100", "19050200", "19050300", "19050400", "19050500", "19050600", "19050700",
    "19050800",
}










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
# Numeric columns (must parse as float when populated)
# ---------------------------------------------------------------------------
NUMERIC_COLS = [
    "Case Size", "Split Size",
    "Case Net Weight", "Case Tare Weight", "Case True Net Weight (Drained/Glazed)",
    "Case Catch Weight Range From", "Case Catch Weight Range To",
    "Split Net Weight", "Split Tare Weight", "Split True Net Weight (Drained/Glazed)",
    "Case Length", "Case Width", "Case Height",
    "Split Length", "Split Width", "Split Height",
    "Energy Kcal", "Energy KJ", "Fat", "Of which Saturates",
    "Of which Mono-Unsaturates", "Of which Polyunsaturates", "Of which Trans Fats",
    "Carbohydrate", "Of which Sugars", "Of which Polyols", "Of which Starch",
    "Fibre", "Protein", "Salt", "Sodium",
]

# ---------------------------------------------------------------------------
# Integer columns (must be whole numbers when populated)
# ---------------------------------------------------------------------------
INTEGER_COLS = [
    "SUPC",
    "Case Pack", "Split Pack", "Splits Per Case",
    "Cases per Layer (Standard Pallet)", "Layers per Pallet (Standard Pallet)",
    "Cases per Layer (Euro Pallet)", "Layers per Pallet (Euro Pallet)",
    "Shelf Life Period In Days (Manufacturer)",
    "Shelf Life Period in Days (Sysco)",
    "Shelf Life Period in Days (Customer)",
]

# ---------------------------------------------------------------------------
# Country of Origin columns
# ---------------------------------------------------------------------------
COUNTRY_OF_ORIGIN_COLS = [
    "Country Of Origin - Manufactured",
    "Country Of Origin - Packed",
    "Country Of Origin - Sold From",
    "Country Of Origin - Raw Ingredients",
]

# Nutritional columns (used by Rule 5)
NUTRITIONAL_COLS = [
    "Energy Kcal", "Energy KJ", "Fat", "Of which Saturates",
    "Of which Mono-Unsaturates", "Of which Polyunsaturates", "Of which Trans Fats",
    "Carbohydrate", "Of which Sugars", "Of which Polyols", "Of which Starch",
    "Fibre", "Protein", "Salt", "Sodium",
]

# ---------------------------------------------------------------------------
# Allowed / forbidden special characters — apply to ALL free-text attributes
#
# Approved special chars : % & ( ) * + - . / ™ ® Ø
# Approved accented chars : á Á à À â Â ä Ä å Å æ Æ ç Ç é É è È ê Ê ë Ë
#                           í Í ì Ì î Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö ú Ú ù Ù
#                           û Û ü Ü ß ÿ Ø Ý
# Spaces are allowed in description fields (but not in Search Name — see F8)
# ---------------------------------------------------------------------------
_ACCENTS = "áÁàÀâÂäÄåÅæÆçÇéÉèÈêÊëËíÍìÌîÎïÏñÑóÓòÒôÔöÖúÚùÙûÛüÜßÿØÝ"
_SPECIAL  = r"%&()*+\-./™®Ø"
TEXT_ALLOWED_RE   = re.compile(rf"^[a-zA-Z0-9{_ACCENTS} {_SPECIAL}]*$")   # with space
_TEXT_ALLOWED_CHR = re.compile(rf"[a-zA-Z0-9{_ACCENTS} {_SPECIAL}]")       # single-char test

# All free-text columns subject to Rule F7
TEXT_COLS = [
    "First & Second Word",
    "Marketing Description",
    "Warehouse Description",
    "Invoice Description",
    "Latin Fish Name",
    "Description Text",
    "True Vendor Name",
    "Cooking Instructions",
    "Defrosting Guidelines",
    "Handling Instructions",
    "Storage Guidelines",
    "Cooking Warning",
    "Food Safety Tips",
]

# Keep old name as alias so nothing else breaks
DESCRIPTION_COLS        = TEXT_COLS
DESCRIPTION_ALLOWED_RE  = TEXT_ALLOWED_RE

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


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _normalise_attr_group_id(raw) -> str:
    """Normalise an Attribute Group ID to an 8-character zero-padded string."""
    if isinstance(raw, float) and raw == int(raw):
        return str(int(raw)).zfill(8)
    return str(raw).strip().zfill(8)


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
    Rule 4 — Shelf Life order (Global sheet).
    When both values are present: Sysco < Manufacturer.
    Note: 'Shelf Life Period in Days (Customer)' lives on the Local Product Data sheet.
    """
    rule_name = "Rule 4 — Shelf Life order"
    results = []
    if COL_SHELF_SYSCO not in df.columns or COL_SHELF_MANUFACTURER not in df.columns:
        return results

    for idx, row in df.iterrows():
        s_raw = row.get(COL_SHELF_SYSCO)
        m_raw = row.get(COL_SHELF_MANUFACTURER)
        if is_empty(s_raw) or is_empty(m_raw):
            continue
        try:
            s, m = int(float(s_raw)), int(float(m_raw))
        except (ValueError, TypeError):
            continue
        if not (s < m):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Shelf Life order invalid: Sysco ({s}) must be < Manufacturer ({m})",
            ))
    return results


def rule_no_nutrition_for_non_food(df: pd.DataFrame) -> list[dict]:
    """
    Rule 5 — Nutritional data must be empty for non-food products.
    If Attribute Group ID is not in FOOD_ATTRIBUTE_GROUP_IDS, all nutritional
    columns must be null or empty.
    Non-food Business Centres: Administrative (01), Disposables (10), Supplies & Equipment (18).
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
        if _normalise_attr_group_id(attr_id) in FOOD_ATTRIBUTE_GROUP_IDS:
            continue
        if any(not is_empty(row.get(c)) for c in available_nutrition):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Non-food product (Attribute Group ID: {_normalise_attr_group_id(attr_id)}) has nutritional data populated",
            ))
    return results


def rule_catch_weight_conditional(df: pd.DataFrame) -> list[dict]:
    """
    Rule 8 — Catch Weight range required when Catch Weight is Yes.
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
        else:
            # Both From and To are present — check From <= To
            from_raw = row.get(COL_CATCH_FROM)
            to_raw = row.get(COL_CATCH_TO)
            if not is_empty(from_raw) and not is_empty(to_raw):
                try:
                    if float(from_raw) > float(to_raw):
                        results.append(make_result(
                            sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                            rule=rule_name,
                            message=f"Row {excel_row(idx)} — Catch Weight Range From ({from_raw}) must be ≤ Range To ({to_raw})",
                        ))
                except (ValueError, TypeError):
                    pass
    return results


def rule_taric_code_conditional(df: pd.DataFrame) -> list[dict]:
    """Rule 9 — Taric Code is conditional on 'Does Product Have A Taric Code?'.

    If Yes → Taric Code/Commodity Code must be filled.
    If No  → Taric Code/Commodity Code must be empty.
    """
    rule_name = "Rule 9 — Taric Code conditional"
    results = []
    if COL_HAS_TARIC not in df.columns:
        return results

    flag_col = df[COL_HAS_TARIC].astype(str).str.strip()

    for idx, row in df[flag_col == "Yes"].iterrows():
        if COL_TARIC in df.columns and is_empty(row.get(COL_TARIC)):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Does Product Have A Taric Code?' is Yes but '{COL_TARIC}' is empty.",
            ))

    for idx, row in df[flag_col == "No"].iterrows():
        if COL_TARIC in df.columns and not is_empty(row.get(COL_TARIC)):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Does Product Have A Taric Code?' is No but '{COL_TARIC}' is filled.",
            ))

    return results


def rule_mandatory_fields(df: pd.DataFrame) -> list[dict]:
    """
    Rule 10 — Mandatory fields must be populated.
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
    Must be numeric and exactly 8, 12, 13, or 14 digits. Null/empty skipped.
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
    Rule F2 — Attribute Group ID must resolve to exactly 8 digits when zero-padded.
    """
    rule_name = "Rule F2 — Attribute Group ID format"
    results = []
    if COL_ATTRIBUTE_GROUP_ID not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_ATTRIBUTE_GROUP_ID)
        if is_empty(raw):
            continue
        normalised = _normalise_attr_group_id(raw)
        if not re.fullmatch(r"\d{8}", normalised):
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Attribute Group ID '{str(raw).strip()}' must be exactly 8 digits.",
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
    Rule F5 — Numeric fields must be valid numbers when populated.
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
    Rule F6 — Country of Origin must be a valid ISO 3166-1 alpha-2 code.
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

def rule_description_special_chars(df: pd.DataFrame) -> list[dict]:
    """
    Rule F7 — Free-text fields must not contain disallowed special characters.

    Allowed : alphanumeric, accented letters, space, % & ( ) * + - . / ™ ® Ø
    Disallowed : , ! " # $ ' : ; < = > ? @ [ \\ ] ^ _ ` { | } ~

    Applies to all free-text columns defined in TEXT_COLS.
    """
    rule_name = "Rule F7 — Special characters"
    results = []
    present = [c for c in TEXT_COLS if c in df.columns]

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            val_str = str(raw)
            if not TEXT_ALLOWED_RE.match(val_str):
                bad_chars = sorted({ch for ch in val_str if not _TEXT_ALLOWED_CHR.match(ch)})
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=(
                        f"Row {excel_row(idx)} — '{col}' contains disallowed "
                        f"character(s): {' '.join(repr(c) for c in bad_chars)}"
                    ),
                ))
    return results


# Search Name: same allowed chars as TEXT_ALLOWED_RE but NO space and max 20 chars
_SEARCH_NAME_ALLOWED = re.compile(rf"^[a-zA-Z0-9{_ACCENTS}{_SPECIAL}]{{1,20}}$")


def rule_search_name_format(df: pd.DataFrame) -> list[dict]:
    """
    Rule F8 — Search Name format.

    Must be:
      - alphanumeric only (no spaces, no special characters)
      - max 20 characters
    """
    rule_name = "Rule F8 — Search Name format"
    col = "Search Name"
    results = []
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val_str = str(raw).strip()
        if not _SEARCH_NAME_ALLOWED.match(val_str):
            issues = []
            if len(val_str) > 20:
                issues.append(f"exceeds 20 characters ({len(val_str)})")
            bad_chars = sorted({ch for ch in val_str if not _TEXT_ALLOWED_CHR.match(ch) or ch == " "})
            if bad_chars:
                issues.append(f"contains disallowed character(s): {' '.join(repr(c) for c in bad_chars)}")
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Search Name' is invalid: {'; '.join(issues)}",
            ))
    return results


def rule_lov_attribute_group_id(df: pd.DataFrame) -> list[dict]:
    """
    Rule L0 — Attribute Group ID must be a valid OSD Hierarchy ID.
    Value is normalised to 8-digit zero-padded string before checking.
    """
    rule_name = "Rule L0 — Attribute Group ID LOV"
    results = []
    if COL_ATTRIBUTE_GROUP_ID not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(COL_ATTRIBUTE_GROUP_ID)
        if is_empty(raw):
            continue
        normalised = _normalise_attr_group_id(raw)
        if normalised not in ATTRIBUTE_GROUP_ID_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Attribute Group ID '{normalised}' is not a recognised OSD Hierarchy ID.",
            ))
    return results


def rule_lov_brand_key(df: pd.DataFrame) -> list[dict]:
    """
    Rule L1 — Brand Key must be a recognised Sysco Own Brand Code or Vendor Brand Code.
    """
    rule_name = "Rule L1 — Brand Key LOV"
    results = []
    col = "Brand Key"
    if col not in df.columns or not BRAND_KEY_LOV:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in BRAND_KEY_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — Brand Key '{str(raw).strip()}' is not a recognised Sysco or Vendor brand code.",
            ))
    return results


def rule_lov_temperature(df: pd.DataFrame) -> list[dict]:
    """
    Rule L6 — Min/Max Temperature must be a valid temp code.
      TEMP18 = -18°C (0°F)
      TEMP0  =   0°C (32°F)
      TEMP5  =   5°C (41°F)
      TEMP8  =   8°C (46.4°F)
    """
    rule_name = "Rule L6 — Temperature LOV"
    TEMP_LOV = {"TEMP18", "TEMP0", "TEMP5", "TEMP8"}
    TEMP_COLS = ["Min Temperature", "Max Temperature"]
    results = []
    present = [c for c in TEMP_COLS if c in df.columns]
    if not present:
        return results

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in TEMP_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: {', '.join(sorted(TEMP_LOV))}.",
                ))
    return results


def rule_lov_vat_group(df: pd.DataFrame) -> list[dict]:
    """
    Rule L5 — Item VAT (Purchasing and Selling) must be a valid vat_group code.
      I-STD  = Standard – 20%
      I-ZERO = Zero Rated – 0%
      I-RED  = Reduced – 5%
    """
    rule_name = "Rule L5 — Item VAT LOV"
    VAT_LOV = {"I-STD", "I-ZERO", "I-RED"}
    VAT_COLS = ["Item VAT - Purchasing", "Item VAT - Selling"]
    results = []
    present = [c for c in VAT_COLS if c in df.columns]
    if not present:
        return results

    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in VAT_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: {', '.join(sorted(VAT_LOV))}.",
                ))
    return results


def rule_lov_item_group(df: pd.DataFrame) -> list[dict]:
    """
    Rule L4 — Item Group must be a valid code.
      RM-DRY     = Raw Materials - Dry
      RM-COOLER  = Raw Materials - Cooler
      RM-FREEZER = Raw Materials - Freezer
      FG-DRY     = Finished Goods - Dry
      FG-COOLER  = Finished Goods - Cooler
      FG-FREEZER = Finished Goods - Freezer
      NON FOOD   = Non Food
    """
    rule_name = "Rule L4 — Item Group LOV"
    ITEM_GROUP_LOV = {"RM-DRY", "RM-COOLER", "RM-FREEZER", "FG-DRY", "FG-COOLER", "FG-FREEZER", "NON FOOD"}
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
                message=f"Row {excel_row(idx)} — 'Item Group' value '{str(raw).strip()}' is invalid. Allowed: {', '.join(sorted(ITEM_GROUP_LOV))}.",
            ))
    return results


def rule_lov_seasonal(df: pd.DataFrame) -> list[dict]:
    """
    Rule L3 — Seasonal must be a valid code.
      01 = Closed for Spring
      02 = Closed for Summer
      03 = Closed for Autumn
      04 = Closed for Winter
      05 = Closed for Summer, Spring
      06 = Closed for Autumn, Winter
      07 = Closed for Autumn, Winter, Spring
      99 = Non-Seasonal
    """
    rule_name = "Rule L3 — Seasonal LOV"
    SEASONAL_LOV = {"01", "02", "03", "04", "05", "06", "07", "99"}
    results = []
    col = "Seasonal"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        # Normalise: Excel may store as integer (1, 2 … 99)
        raw_str = str(int(float(str(raw)))).zfill(2) if str(raw).replace(".", "").isdigit() else str(raw).strip()
        if raw_str not in SEASONAL_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Seasonal' value '{raw_str}' is invalid. Allowed: {', '.join(sorted(SEASONAL_LOV))}.",
            ))
    return results


def rule_lov_status(df: pd.DataFrame) -> list[dict]:
    """
    Rule L2 — Status must be Active, Delisted, or Archived.
    """
    rule_name = "Rule L2 — Status LOV"
    STATUS_LOV = {"Active", "Delisted", "Archived"}
    results = []
    col = "Status"
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


def rule_lov_generic_gtin(df: pd.DataFrame) -> list[dict]:
    """Rule L9 — Generic GTIN must be one of the 8 recognised generic codes."""
    rule_name = "Rule L9 — Generic GTIN LOV"
    GENERIC_GTIN_LOV = {
        "10000000000009", "20000000000009", "30000000000009", "40000000000009",
        "50000000000009", "60000000000009", "70000000000009", "80000000000009",
    }
    col = "Generic GTIN"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        # Normalise: Excel may read as integer, strip decimals
        val = str(raw).strip()
        if val.endswith(".0"):
            val = val[:-2]
        if val not in GENERIC_GTIN_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Generic GTIN' value '{val}' is not a recognised generic GTIN code.",
            ))
    return results


# ---------------------------------------------------------------------------
# Rule L10 — First & Second Word LOV
# The "First & Second Word" field must contain an exact "WORD1 WORD2" pair
# from the approved list. Comparison is case-insensitive; stored in upper case.
# ---------------------------------------------------------------------------
_FIRST_SECOND_WORD_MAP: dict[str, tuple[str, ...]] = {
    "AIR": ("FRESHENER",),
    "ALCOHOL": ("GEL",),
    "ALMOND": ("CHIP","FLAKED","FRESH","GROUND","ICING","SLI","VEGAN","WHL"),
    "ANISE": ("STAR",),
    "APPLE": ("CARAMEL","CRUMBLE","FRESH","GREEN","PACK","RED","SLICES","TREAT"),
    "APRICOT": ("DRIED","HALF","PUREE"),
    "APRON": ("COTTON","PLASTIC"),
    "ARANCINI": ("PEA","PORCINI"),
    "ARROWROOT": ("GROUND",),
    "ARTICHOKE": ("FRESH","HEART"),
    "ASPARAGUS": ("FRESH","FROZEN"),
    "AUBERGINE": ("FRESH",),
    "AVOCADO": ("FRESH",),
    "BABY": ("CHORIZO",),
    "BACON": ("BACK","BIT","CHIP","GREEN","SLI","SMOKED","STRIP","VEGAN"),
    "BAG": ("BAGUETTE","BROWN","FOOD","PACK","PAPER","PLASTIC"),
    "BAGEL": ("MULTISEED","PLAIN"),
    "BAGUETTE": ("BARRA","HINGED"),
    "BAKING": ("ADDITIVE","MIX","SODA"),
    "BANANA": ("FRESH","PUREE"),
    "BAR": ("GRANOLA",),
    "BARLEY": ("PEARL",),
    "BASA": ("FILLETS",),
    "BASE": ("BAKER","BEEF","CAKE","CHICKEN"),
    "BASS": ("SEA",),
    "BAY": ("LEAVES",),
    "BBQ": ("CHICKEN","CHKN"),
    "BEAN": ("BAKED","BLACK","BORLOTTI","BURGER","BUTTER","CANNELLINI","CHILI","CURD","GREEN","HARICOT","KIDNEY","LENTIL","RED","ROLL","VANILLA","WHOLE"),
    "BEAR": ("GROUND",),
    "BEEF": ("AND","BLADE","BONE","BRISKET","BURGER","CHEEK","CORNED","CUBE","DICED","EYE","FAT","FILLET","FORE-RIB","GROUND","KIDNEY","KNUCKLE","LOIN","MEAT","MINCE","RIB","RIBEYE","ROAST","ROLL","ROUND","RUMP","SALT","SHIN","SILVERSIDE","SLI","SLICED","STEAK","STRIP","TAIL","TOMATO","TONGUE","TOP","TRIM","WHOLE"),
    "BEER": ("GINGER","IPA"),
    "BEET": ("FRESH","ROOT"),
    "BERRY": ("DRIED","FRESH","WILD"),
    "BIN": ("WASTE",),
    "BISCUIT": ("CHEESE","MACAROON","MIX","TEA"),
    "BLACKBERRY": ("FRESH",),
    "BLEACH": ("LIQUID",),
    "BLUEBERRY": ("BIT",),
    "BOAR": ("BURGER","GROUND","WILD"),
    "BOARD": ("WOOD",),
    "BOK": ("CHOY",),
    "BOTTLE": ("GLASS","SPRAY"),
    "BOWL": ("PAPER",),
    "BOX": ("COOKIE","FOOD"),
    "BREAD": ("BAGUETTE","BROWN","BUN","CHEESE","CIABATTA","CRUMB","ENGLISH","FLAT","FRENCH","GARLIC","GRAIN","LOAF","PITA","PLAIN","ROLL","SLICED","SOURDOUGH","THICK","WHEAT","WHITE"),
    "BREAM": ("SEA","WHOLE"),
    "BROCCOLI": ("FLORET","FRESH","STEM"),
    "BROOM": ("HEAD",),
    "BROTH": ("BEEF","CHICKEN"),
    "BROWNIE": ("CAKE","CARAMEL","CHOC","CHOCOLATE","FUDGE"),
    "BRUSH": ("PASTRY",),
    "BULGAR": ("WHEAT",),
    "BUN": ("BRIOCHE","BURGER","CHARCOAL","CHOCOLATE","COLA","GLAZED","HIRATA","MINIATURE","ONION","PLAIN","PRETZEL","ROLL","SESAME","WHITE"),
    "BURGER": ("BEEF","BOX","VEGAN","VEGETABLE"),
    "BUTTER": ("BLEND","BUN","PATS","SOLID"),
    "CABBAGE": ("CHINESE","FRESH","GREEN","RED","SAVOY","WHITE"),
    "CAKE": ("ALMOND","ANGEL","APPLE","CARAMEL","CARROT","CHERRY","CHOC","CHOCOLATE","COFFEE","CREAM","CUSTARD","FRUIT","FUDGE","GATEAU","LEMON","LOAF","MINI","RED","SANDWICH","SHEET","SHORT","SPONGE","STRAWBERRY","TEA","TIRAMISU","TOFFEE","TRAY"),
    "CALZONE": ("CHEESE",),
    "CANDLE": ("SET",),
    "CANDY": ("BAR","BEET","CARAMEL","CHERRY","CHOC","CORN","CRACKER","GUMMY","HARD","JELLY","LEMON","LOLLIPOP","LOLLYPOP","MINT","MIX","SPRINKLE","STARBURST","SWEET"),
    "CAP": ("WHITE",),
    "CAPER": ("CAPOTE","WHOLE"),
    "CAPERS": ("BABY",),
    "CARAMEL": ("MINIATURE","NUT"),
    "CARRIER": ("PLASTIC",),
    "CARROT": ("APPLE","BABY","DICED","FRESH","JULIENNE"),
    "CAULIFLOWER": ("FLORET","FRESH"),
    "CELERY": ("FRESH","ROOT"),
    "CEREAL": ("BAG","BRAN","COCOA","CORN","FROSTED","FRUIT","GRANOLA","INSTANT","MUESLI","RICE","SPECIAL"),
    "CHAISE": ("LOUNGE",),
    "CHARD": ("SWISS",),
    "CHEESE": ("BABYBEL","BLACK","BLOCK","BLUE","BRIE","CHEDDAR","CHILI","CLASSIC","COTTAGE","CREAM","CROQUETTE","CUBE","FETA","FOOD","FRENCH","FRIES","FRY","GOAT","GORGONZOLA","GOUDA","GRANA","GREEK","HALLOUMI","ITALIAN","JACK","MEXICAN","MOZZ","ONION","PARMESAN","PIZZA","PORTION","RED","RICOTTA","SLI","SLICES","SMALL","SMOKED","SOFT","SPREAD","STICK","STYLE","SWISS","VEGAN","WEDGE","WHEEL"),
    "CHEESECAKE": ("BAILEYS","CAPPUCCINO","CARAMEL","CHERRY","CHOC","CHOCOLATE","LEMON","MIX","NEW","PLAIN","STRAWBERRY"),
    "CHERRY": ("ALMOND","CHOC","MARACHINO","WHOLE"),
    "CHESTNUT": ("PEELED",),
    "CHICKEN": ("AND","BONE","BREADED","BREAST","BURGER","CHUNK","CURRY","DICED","DRUMSTICK","FILET","FRIED","HALF","HOT","LEG","MAYONNAISE","MEAT","MIX","NUGGET","QUARTER","SKIN","STRIP","THIGH","WHOLE","WING","WINGS"),
    "CHICKPEA": ("BULK","CANNED","DRIED"),
    "CHICORY": ("FRESH",),
    "CHILI": ("CON","FRESH","GREEN","MIX","PAD","POWDER","RED"),
    "CHIP": ("BAG","BBQ","CHEESE","CHILI","CHUNK","CORN","CRISP","POTATO","ROLL","TORTILLA"),
    "CHIVE": ("FRESH",),
    "CHOC": ("CHIP","FONDANT","LOLLY","SAUCE"),
    "CHOCLATE": ("DARK","MILK","WHITE"),
    "CHOCOLATE": ("BAR","BASE","CARAMEL","CHIP","CREAM","CROISSANT","DARK","DROP","FUDGE","MILK","MINT","NUT","ORANGE","ROUALDE","SQUARE","STICK","WHITE"),
    "CHORIZO": ("SLICED",),
    "CHURRO": ("CHOCOLATE","FILLED"),
    "CHUTNEY": ("APPLE","FIG","MANGO","ONION","PEAR","TOMATO"),
    "CIDER": ("APPLE",),
    "CINNAMON": ("GROUND","STICK"),
    "CITRUS": ("PUNCH",),
    "CLEANER": ("BATHROOM","DRAIN","GEL","GRILL","LEMON","LIQUID","MULTI","OVEN","PAD","SPRAY","SUPER","TOILET","VIRABACT"),
    "CLOCK": ("TIME","WALL"),
    "CLOTH": ("ALL","BLUE","CLEANING","GLOVE","GREEN","NET","PAPER","YELLOW"),
    "CLOTHESPIN": ("WOOD",),
    "COCKTAIL": ("APTZR","SAUCE"),
    "COCOA": ("POWDER",),
    "COCONUT": ("CHOC","DRIED","MANGO","WHL"),
    "COD": ("BATTERED","BEER","BITE","BREADED","CUT","FIL","FILET","FILLET","FISH","LOIN","STEAK","TAIL"),
    "COFFEE": ("AZERA","BASE","BEANS","BLEND","COOKIE","GROUND","ICED","LITE","MACHINE","NUT","STICK","TEA","TIN","WALNUT"),
    "COLD": ("WATER",),
    "COLORING": ("FOOD",),
    "CONE": ("ICE","SUGAR","WAFER","WAFFLE"),
    "CONTAINER": ("BAGASSE","FOOD","SALAD","SANDWICH"),
    "COOKIE": ("BISCUIT","CARAMEL","CHIP","CHOC","CINNAMON","CREAM","CRUMB","FUDGE","JAM","MACAROON","MIX","OATMEAL","SANDWICH","SHORTBREAD","SPREAD","STICK"),
    "COOLER": ("WATER",),
    "CORN": ("BABY","COB","FLAKE","SWEET","WHL"),
    "COTTON": ("BALL",),
    "COUSCOUS": ("GRAIN","PEARL"),
    "COVER": ("TABLE",),
    "CRAB": ("CAKE","MEAT"),
    "CRACKER": ("RICE",),
    "CRANBERRY": ("FRESH",),
    "CRAWFISH": ("TAIL",),
    "CRAYFISH": ("TAIL",),
    "CREAM": ("AEROSOL","ALTERNATIVE","BISCUIT","CHEESE","CLEANER","CLOTTED","COCONUT","COFFEE","DOUBLE","FRAICHE","FRESH","LIQUID","PUFF","SET","WHIPPED","WHIPPING"),
    "CREME": ("BRULEE","CARAMEL","FRAICHE"),
    "CRISPS": ("HULO",),
    "CROISSANT": ("ALMOND","BUTTER","DOUGH","MINIATURE"),
    "CRUMBLE": ("APPLE",),
    "CRUMPET": ("PLAIN",),
    "CUCUMBER": ("FRESH",),
    "CUP": ("CLEAR","HALF","HOT","PAPER","PET","PLASTIC","WATER","WHITE"),
    "CURRANT": ("RED",),
    "CURRY": ("PASTE","POWDER"),
    "CUSTARD": ("CREAM","MIX"),
    "CUTLERY": ("KIT",),
    "DANISH": ("CINNAMON","PASTRY","PECAN"),
    "DATE": ("SLICE",),
    "DEGREASER": ("HEAVY",),
    "DESSERT": ("CARAMEL","CUP","FROZEN","MIX","MOUSSE","ORANGE","STRAWBERRY","TIRAMISU"),
    "DETERGENT": ("GLASS","LIQUID","MACHINE"),
    "DILL": ("HERB",),
    "DISH": ("PLASTIC",),
    "DISHWASHER": ("LOW",),
    "DISINFECTANT": ("PINE",),
    "DISPENSER": ("BOTTLE","FILM","PAPER","PUMP","TOWEL"),
    "DOG": ("TREAT",),
    "DOILY": ("PAPER",),
    "DOME": ("LID",),
    "DONUT": ("CHOC","CHOUXNUT","CINNAMON","DOUGH","JELLY","MINIATURE","WHITE"),
    "DOUGH": ("BALL","COOKIE","MIX"),
    "DOUGHNUT": ("MIX",),
    "DRESSING": ("CAESAR","FRENCH","JAPANESE","YOGURT"),
    "DRIED": ("PEEL",),
    "DRINK": ("APPLE","BLACKBERRY","BOT","CANNED","CHERRY","CHOCOLATE","COFFEE","ENERGY","FRUIT","GINGER","GREEN","ITALIAN","LEMON","LEMONADE","MANGO","MIX","ORANGE","PINEAPPLE","RASPBERRY","RED","SMOOTHIE","SPARKLING","STRAWBERRY","SWEET","TROPICAL","WHITE"),
    "DUCK": ("BREAST","FAT","GROUND","HALF","LEG","LIVER","MEAT","WHL","WHOLE"),
    "DUST": ("PAN",),
    "DUSTER": ("YELLOW",),
    "EGG": ("LIQUID","MAYONNAISE","ROLL","WHITE","YOLK"),
    "EMERY": ("BOARD",),
    "EXTRACT": ("VANILLA",),
    "FALAFEL": ("MOROCCAN",),
    "FAT": ("DUCK",),
    "FENNEL": ("FRESH","SEED"),
    "FIG": ("FRESH",),
    "FILLING": ("CHERRY","MIX","PIE","SANDWICH"),
    "FILM": ("CLING","FOR","PVC","ROLL","SHRINK"),
    "FILTER": ("COFFEE",),
    "FISH": ("BITE","BITES","BTRD","CAKE","FILET","FOOD","PIE","SMOKED","STICK","WHITE"),
    "FLAN": ("CASE",),
    "FLAP": ("JACK",),
    "FLAVOURING": ("ALMOND",),
    "FLOUR": ("CORN","MIX","RICE","SELF","SEMOLINA","TORTILLA","WHEAT","WHITE","WRAP"),
    "FLOWER": ("EDIBLE",),
    "FLOWERS": ("FRESH",),
    "FLU": ("MEDIUM",),
    "FOIL": ("FOOD","ROLL"),
    "FOOD": ("BABY","FOR","PET"),
    "FORK": ("WOOD","WOODEN"),
    "FRENCH": ("FRIES",),
    "FRESH": ("CRESS",),
    "FRESHENER": ("AIR",),
    "FRIES": ("HALLOUMI",),
    "FRITTER": ("CORN",),
    "FRUIT": ("BLUEBERRY","COCKTAIL","CRUMB","DRIED","FRESH","FROZEN","MIX","PASTILLES","PINEAPPLE","SCONE","SMOOTHIE","STICK"),
    "FUDGE": ("CHOCOLATE",),
    "GAME": ("MEAT",),
    "GARLIC": ("BULB","CHOPPED","CLOVE","FRESH","PEELED","POWDER","PUREE","SALT"),
    "GAS": ("CARBON",),
    "GELATIN": ("GEL",),
    "GINGER": ("BEER","FRESH","ROOT"),
    "GLACE": ("LOBSTER",),
    "GLASS": ("JUICE","PLASTIC","WATER"),
    "GLASSES": ("READING","SAFETY"),
    "GLAZE": ("BALSAMIC","BARBECUE","BASE","MIX"),
    "GLOVE": ("NITRILE","OVEN","RUBBER","VINYL"),
    "GRAPE": ("RED","WHITE"),
    "GRAPEFRUIT": ("FRESH","RUBY","SECTION"),
    "GRASS": ("GREEN",),
    "GRAVY": ("BASE","BEEF","CHICKEN"),
    "GREEN": ("FRESH","PEPPERCORNS"),
    "GROUND": ("PAPRIKA",),
    "GUACAMOLE": ("FRESH","SAUCE"),
    "GUINEA": ("WHL",),
    "GUM": ("BUBBLE","XANTHAN"),
    "HADDOCK": ("BATTERED","FILET","LOIN","SMOKED","STICK"),
    "HAGGIS": ("TRADITIONAL",),
    "HAIRNET": ("BLUE",),
    "HAKE": ("FILET",),
    "HALIBUT": ("FILET",),
    "HAM": ("BBQ","COOKED","GREEN","HALF","HOCK","HONEY","LEG","PARMA","PIZZA","SLICED","SMOKED","STEAK","WHOLE"),
    "HARNESS": ("HEAD",),
    "HASHBROWN": ("ROUND",),
    "HERB": ("BASIL","CHIVE","CRISP","FRESH","LEMON","MINT","MIX","PARSLEY","SAGE","SEED","TARRAGON"),
    "HOLDER": ("CUP",),
    "HONEY": ("CLEAR","COMB","FRESH","LIQUID"),
    "HONEYCOMB": ("WHL","WHOLE"),
    "HORSERADISH": ("FRESH",),
    "HOT": ("DOG",),
    "HUMMUS": ("ORIGINAL",),
    "ICE": ("CREAM","CUBE","DAIRY","FRUIT","LOLLY","MILK","ORANGE"),
    "ICING": ("BANANA","BUN","CARAMEL","CHOC","GLAZE","LEMON","STRAWBERRY","SUGAR","TOFFEE"),
    "IN": ("SYRUP",),
    "JAM": ("APRICOT","ASSORTED","BLACKCURRANT","CHERRY","FRUIT","RASPBERRY","SPONGE","STRAWBERRY"),
    "JELLY": ("ORANGE","QUINCE","RED","STRAWBERRY"),
    "JUICE": ("APPLE","BERRY","CRANBERRY","DRINK","LEMON","LIME","MANGO","ORANGE","PEAR","PINEAPPLE","TOMATO"),
    "KALE": ("FRESH",),
    "KETCHUP": ("PACKET","SQUEEZY","TABLE","TOMATO"),
    "KIWI": ("FRESH",),
    "KNIFE": ("BONE","STEAK"),
    "KOHLRABI": ("FRESH",),
    "LABEL": ("DAILY","DATE","DAY","MAILER","PAPER","ROLL","SAT","WED","WHITE"),
    "LAMB": ("BONE","BREAST","CUT","DICED","GROUND","KIDNEY","LEG","LIVER","LOIN","RACK","ROLL","SHANK","SHOULDER","STEAK","WHL","WHOLE"),
    "LARD": ("BLOCK",),
    "LASAGNA": ("BEEF","VEG"),
    "LAUNDRY": ("POWDER",),
    "LEAF": ("FRESH",),
    "LEAVES": ("FRESH",),
    "LEEK": ("BABY","FRESH"),
    "LEG": ("STEAK",),
    "LEMON": ("BLUEBERRY","CURD","FRESH","GLAZE","ROU"),
    "LEMONADE": ("BOTTLE","CONCENTRATE","FRESH","PINK"),
    "LENTIL": ("GREEN","PILAF"),
    "LETTUCE": ("FRESH","ICEBERG","LOLLO","RADICCHIO","RED"),
    "LID": ("BLACK","BOWL","CONTAINER","STOPCOCK","WHITE"),
    "LIME": ("LEMON","WEDGE"),
    "LIMEADE": ("CORDIAL",),
    "LINER": ("BIN",),
    "LIQUID": ("DISHWASHER",),
    "LIVER": ("CHICKEN","DUCK"),
    "LLAMA": ("ROAST",),
    "LNCPS": ("CHIP",),
    "LOBSTER": ("LIVE","SCAMPI"),
    "MACARONI": ("CHEESE",),
    "MACKEREL": ("FILET",),
    "MANDARIN": ("SEGMENT",),
    "MANGO": ("DICED","FRESH","PUREE"),
    "MARGARINE": ("BTR","TUB"),
    "MARINADE": ("GLAZE",),
    "MARMALADE": ("ONION","ORANGE","TUB"),
    "MARSHMALLOW": ("WHITE",),
    "MARZIPAN": ("PREMIUM",),
    "MATZO": ("BALL","EGG","MEAL"),
    "MAYONNAISE": ("CHIPOTLE","CLASSIC","CORONATION","CUP","GARLIC","LITE","MEXICAN","PACKET","SQUEEZE","VEGAN"),
    "MEAT": ("BALL","MIX"),
    "MEATBALL": ("VEGAN",),
    "MELON": ("GALIA","HONEYDEW","ORANGE"),
    "MERINGUE": ("NEST",),
    "MILK": ("ALMOND","BANANA","CARAMEL","CHOC","CHOCOLATE","COCONUT","COFFEE","CONDENSED","EVAPORATED","LIQUID","MINT","OAT","ORGANIC","SEMI","SKIM","SKIMMED","SOY","STRAWBERRY","VANILLA","WHL","WHOLE"),
    "MILKSHAKE": ("BASE",),
    "MINT": ("FRESH","LOLLY","SWEET"),
    "MIX": ("BATTER","GRAVY","MILK","MUFFIN","SMOOTHIE","SOUP","STUFFING"),
    "MONKFISH": ("PRTN","TAIL"),
    "MOP": ("BUCKET","HANDLE","HEAD"),
    "MOUSSE": ("CHOC",),
    "MUFFIN": ("BLUEBERRY","CASE","CHOC"),
    "MULLET": ("FILET",),
    "MUSHROOM": ("BUTTON","CUP","FRESH","OYSTER","PORTOBELLO","SHITAKE","SOUP","STEAK","WILD"),
    "MUSSEL": ("LIVE","MEAT"),
    "MUSTARD": ("BEEF","CHIP","DIJON","ENGLISH","FRENCH","GRAIN","GRAINY","HONEY","PACKET","POWDER","SEED","WHL","YELLOW"),
    "NAPKIN": ("1PLY","2PLY","3PLY","CREAM","LINEN","PAPER","SANITARY","WHITE"),
    "NECTARINE": ("FRESH",),
    "NOODLE": ("EGG","RICE","UDON"),
    "NUT": ("CASHEW","HAZELNUT","MIX","PEANUT","PECAN","PINE","PISTACHIO","PROTEIN","ROAST","WALNUT"),
    "OAT": ("FLAKES","REGULAR"),
    "OIL": ("ALMOND","BUTTER","COOKING","DRUM","GRAPE","OLIVE","SESAME","SUNFLOWER","TRUFFLE","VEGETABLE"),
    "OLIVE": ("BLACK","GREEK","GREEN","LEMON","MIX","PITTED","SPANISH","WHOLE"),
    "ONION": ("BALL","BALSAMIC","CHIP","CRISP","FRESH","LARGE","MEDIUM","MIX","PICKLE","PICKLED","POWDER","RED","RING","SEED","SLICED"),
    "ORANGE": ("FRESH","JUICE","LEMON","MANDARIN","SECTION"),
    "ORDER": ("FORM",),
    "PACKET": ("TOILET",),
    "PAD": ("CLEANING",),
    "PAN": ("GRILL",),
    "PANCAKE": ("BASE",),
    "PANCETTA": ("WHOLE",),
    "PANINI": ("PLAIN",),
    "PAPER": ("BAKING","PARCHMENT","PRODUCT","ROLL","SHEET","SINGLE"),
    "PARSNIP": ("FRESH",),
    "PARTRIDGE": ("WHOLE",),
    "PASSION": ("FRUIT",),
    "PASTA": ("BAULETTI","EGG","FUSILLI","GARGANELLI","GNOCCHI","LASAGNA","LINGUINE","LONG","MACARONI","MIX","ORZO","PENNE","RAVIOLI","SHELL","SPAGHETTI","SPINACH","TAGLIATELLE"),
    "PASTE": ("CHILE","VANILLA","WASABI"),
    "PASTRAMI": ("SLICED",),
    "PASTRY": ("BLOCK","CHOC","DOUGH","ECLAIR","MIX","RAISIN","SHELL"),
    "PASTY": ("BEEF","CHICKEN","CORNISH"),
    "PATE": ("ARDENNES","FRESH"),
    "PEA": ("GREEN","POD","PUREE","SNAP"),
    "PEACH": ("FRESH","HALF","PUREE","SLI","SLICED"),
    "PEANUT": ("BUTTER","CHILI","ROASTED","SALT","SALTED","WHOLE"),
    "PEAR": ("FRESH","HALF","PUREE"),
    "PEPPER": ("BLACK","CHILI","GREEN","HOT","MIXED","PACKET","RED","WHITE","YELLOW"),
    "PEPPERCORN": ("WHOLE",),
    "PEPPERS": ("JALAPENO",),
    "PERMIT": ("WHL",),
    "PHEASANT": ("BREAST",),
    "PICKLE": ("CHIP","DILL","GHERKIN","LARGE","SLI"),
    "PIE": ("APPLE","BAKING","BANOFFEE","BEEF","CHICKEN","FRESH","KEY","LEMON","MINI","MIX"),
    "PIG": ("WHOLE",),
    "PIGEON": ("WHOLE",),
    "PINEAPPLE": ("FRESH","RING"),
    "PIZZA": ("ALL","BASE","BOX","CHICKEN","DOUGH","MINI","PEPPERONI","TOMATO"),
    "PLAICE": ("BREADED","WHL"),
    "PLANTBASED": ("CHICKEN",),
    "PLASTER": ("PLASTIC",),
    "PLATE": ("GRILL","LUNCH","PAPER"),
    "PLUM": ("FRESH","HALF"),
    "POLISH": ("FURNITURE",),
    "POLLOCK": ("BATTERED","FILET"),
    "POMEGRANATE": ("FRESH",),
    "POPCORN": ("KERNEL",),
    "PORK": ("BACK","BBQ","BELLY","BONE","CHEEK","COLLAR","CUBE","EAR","FAT","FEET","FILET","GROUND","HAM","HEAD","HOCK","KIDNEY","LEEK","LEG","LIVER","LOIN","MEAT","PIE","PUREE","RIB","SHOULDER","SKIN","STEAK","STIR","WHOLE"),
    "POT": ("PIE",),
    "POTATO": ("BAKER","BAKING","CHIP","CROQUETTE","CUBE","DICE","DICED","FONDANT","FRESH","FRIES","HASHBROWN","MASH","PUFF","ROAST","ROUND","SKIN","SLI","SWEET","WEDGE","WHITE"),
    "POWDER": ("ARROWROOT","BAKING","COCONUT"),
    "PRAWN": ("SHRIMP","TEMPURA","WHOLE"),
    "PRESSE": ("ELDERFLOWER",),
    "PRETZEL": ("ROLL","SOFT"),
    "PRODUCE": ("MISC",),
    "PRODUCT": ("STORAGE",),
    "PRUNE": ("DRIED",),
    "PUDDING": ("BLACK","MIX"),
    "PUFF": ("PASTRY",),
    "PUMPKIN": ("FRESH","SEED"),
    "PUREE": ("BERRY","FRUIT","PEACH","PINEAPPLE"),
    "QUAIL": ("WHL",),
    "QUICHE": ("BASE","CHEESE","LORRAINE","MINI","SHELL","VEGETABLE"),
    "QUINOA": ("GRAIN",),
    "RABBIT": ("BACON","WHL"),
    "RADISH": ("FRESH",),
    "RAISIN": ("GOLDEN",),
    "RASPBERRY": ("FRESH","PUREE"),
    "RED": ("AMARANTH","GREEN","LENTIL","VEIN"),
    "RELISH": ("BURGER","ONION"),
    "RHUBARB": ("FRESH",),
    "RICE": ("ARBORIO","BASMATI","BROWN","CAKE","JASMINE","LONG","PUREE"),
    "RINSE": ("AID",),
    "ROLL": ("BREAD","BROWN","MINI","RASPBERRY","ROUND","RUSTIC","WHITE"),
    "ROSEMARY": ("FRESH","HERB"),
    "RUBBER": ("BAND",),
    "RUM": ("RAISIN",),
    "SAGE": ("FRESH",),
    "SALAD": ("BEAN","BOWL","CREAM","DRESSING","FROZEN","FRUIT","GARDEN","MIX","SEAWEED"),
    "SALAMI": ("CHORIZO","SLI"),
    "SALMON": ("FILET","PACIFIC","SKIN","SMOKED","WHL"),
    "SALSA": ("MEXICAN",),
    "SALT": ("CARAMEL","FINE","PACKET","ROCK","SEA","SMOKED","TABLE","TUB"),
    "SAMPLE": ("SET",),
    "SANDWICH": ("BACON","CHICKEN","FILLING","WEDGE"),
    "SANITIZER": ("HAND",),
    "SAUCE": ("APPLE","BASE","BBQ","BEAN","BOLOGNESE","BRANDY","BROWN","BUTTER","CARAMEL","CHEESE","CHILI","CHIMICHURRI","CHOCOLATE","CRANBERRY","CREAM","CURRY","FISH","GREEN","HABANERO","HORSERADISH","KETCHUP","LOBSTER","MAYONNAISE","MINT","MISO","MIX","MUSHROOM","OYSTER","PACKET","PEPPER","PEPPERCORN","PIZZA","PLUM","RED","SALAD","SALSA","SOY","SWEET","TARTAR","TERIYAKI","TOMATO","WHITE","WORCESTER"),
    "SAUERKRAUT": ("KUHNE",),
    "SAUSAGE": ("APPLE","CHORIZO","COCKTAIL","GARLIC","LINK","MEAT","PATTY","PORK","ROLL","STICK","VEGAN","VEGETARIAN"),
    "SCALLOP": ("IQF","SEA"),
    "SCAMPI": ("WHL",),
    "SCONE": ("APPLE","CHEESE","DOUGH","MIX","PLAIN"),
    "SEA": ("BURGER","URCHIN"),
    "SEABASS": ("FILET",),
    "SEAFOOD": ("BASKET","MIX"),
    "SEASONING": ("CAJUN","CHIP","HERB"),
    "SEAWEED": ("NORI",),
    "SEED": ("CHIA","LIN","POPPY","SESAME","SUNFLOWER","WHOLE"),
    "SET": ("COLLECTION",),
    "SHAKE": ("BANANA","BASE","CHOC","MIX","STRAWBERRY","VANILLA"),
    "SHARPENING": ("STEEL",),
    "SHEET": ("PAN",),
    "SHELL": ("TARTLET",),
    "SHELLOT": ("BANANA",),
    "SHORTBREAD": ("TRAYBAKE",),
    "SHORTCAKE": ("LEMON",),
    "SHRIMP": ("BREADED","ROLL"),
    "SKEWER": ("BAMBOO","WOOD"),
    "SLAW": ("DRY",),
    "SLCS": ("BEAN",),
    "SLUSH": ("BASE","STRAWBERRY"),
    "SMOOTHIE": ("POUCH",),
    "SNACK": ("BAR","CHIP","MIX"),
    "SOAP": ("HAND","LIQUID","PAD","POWDER"),
    "SODA": ("7-UP","CHERRY","COLA","CRISP","LEMON","LEMONADE","ORANGE","PEPSI","POP","REGULAR","SHANDY","SPRITE","STRAWBERRIES"),
    "SODIUM": ("ALGINATE","CHL"),
    "SOLE": ("WHOLE",),
    "SORBET": ("ACAI","CHAMPAGNE","COCONUT","FRUIT","GELATO","GRAPEFRUIT","LEMON","LIME","MANGO","ORANGE","PEACH","RASPBERRY","STRAWBERRY"),
    "SOUP": ("BROCCOLI","CHICKEN","LENTIL","MUSHROOM","TOMATO","VEGETABLE"),
    "SOUR": ("CREAM",),
    "SOYBEAN": ("FRESH",),
    "SPAGHETTI": ("RING",),
    "SPICE": ("BASIL","CAJUN","CLOVE","CUMIN","FIVE","GREEN","GROUND","HERB","ITALIAN","JUNIPER","MIX","NUTMEG","POWDER","RUB","SAFFRON","SEED","TARRAGON"),
    "SPINACH": ("BABY","FRESH"),
    "SPONGE": ("LARGE",),
    "SPOON": ("TEA",),
    "SPRAY": ("HEAD",),
    "SPREAD": ("BUTTER","CHOCOLATE","GARLIC","PORTIONS","SOFT"),
    "SPRING": ("ROLL",),
    "SPROUT": ("BEAN","MIX","SALAD"),
    "SQAUSH": ("APPLE",),
    "SQUASH": ("BUTTERNUT",),
    "SQUID": ("CAL","STRIP"),
    "STEAK": ("BEEF","BONE","CUT","FILET","MINUTE","PIE","RIBEYE","RND","RUMP","SIRLOIN","SLICED","STEW","TOMAHAWK"),
    "STEEL": ("WOOL",),
    "STOCK": ("BASE","BEEF","CHICKEN","FISH","MIX","RED","VEGETABLE"),
    "STOPCOCK": ("MALE","MET","ONE","PLASTIC"),
    "STRAW": ("PAPER",),
    "STRAWBERRY": ("BERRY","DAIRY","FRESH","IQF","LOLLY","PUREE","SPLIT","WHL"),
    "STUFFING": ("MIX",),
    "SUET": ("SHREDDED",),
    "SUGAR": ("BROWN","CANE","CASTER","CUBE","DARK","DONUT","GRANULATED","LIGHT","PACKET","STICK","SUBSTITUTE"),
    "SWEDE": ("FRESH",),
    "SWEET": ("CHILI",),
    "SWORDFISH": ("LOIN",),
    "SYRUP": ("AMARETTO","BANANA","BASE","BLACKBERRY","BLUE","BUTTERSCOTCH","CARAMEL","CHOCOLATE","CINNAMON","COCONUT","GINGER","GINGERBREAD","GOLDEN","GRENADINE","HAZELNUT","HONEY","KIWI","LEMON","LIGHT","MANGO","MAPLE","MINT","MIX","ORANGE","PASSION","PINEAPPLE","PUMPKIN","SALTED","SPECIAL","STRAWBERRY","VANILLA"),
    "TAHINI": ("PASTE",),
    "TAPIOCA": ("PEARLS",),
    "TART": ("ALMOND","APPLE","APRICOT","CARAMEL","CHERRY","CHOCOLATE","LEMON","PECAN","SHELL"),
    "TARTLET": ("APPLE",),
    "TEA": ("BAG","CHAI","CREAM","ENGLISH","GREEN","LEMON","LIQUID","MINT","PEACH","RASPBERRY","TOWEL"),
    "TEST": ("STRIP",),
    "THICKENER": ("FOOD",),
    "THYME": ("FRESH","HERB"),
    "TIN": ("FRUIT",),
    "TOAST": ("SESAME",),
    "TOFFEE": ("BUN","ICING"),
    "TOFU": ("SILKEN",),
    "TOILET": ("PAPER","ROLL"),
    "TOMATO": ("BABY","CHERRY","CHOPPED","DRIED","FRESH","PASTE","PLUM","PUREE","ROUND","SUNDRIED","VINE"),
    "TOPPING": ("SAUCE",),
    "TORTE": ("CHOCOLATE",),
    "TORTILLA": ("CORN",),
    "TOWEL": ("HAND","PAPER"),
    "TRAY": ("BAKE","CHIP","PAPER"),
    "TRAYBACK": ("BAKEWELL",),
    "TRAYBAKE": ("ALMOND","APPLE","APRICOT","BAKEWELL","FLAPJACK"),
    "TROUT": ("FILET","SKIN","SMOKED","WHL"),
    "TUNA": ("CHUNK","SALAD","STEAK"),
    "TURKEY": ("BREAST","CUTLET","DICED","MEAT","ROLL","THIGH","WHL"),
    "TURNIP": ("FRESH",),
    "URINAL": ("SCREEN",),
    "VAC": ("PACK",),
    "VEAL": ("BONE","CHEEK","CUTLET","JUS","LIVER","SWEET","TOP"),
    "VEGAN": ("MEAT",),
    "VEGETABLE": ("ASSORTED","BASE","BEEF","JELLY","MIX","NUGGET","PASTE","ROLL","SAMOSA","SAUSAGE","STEW"),
    "VENISON": ("DICED","GROUND","LEG","LOIN","SADDLE","STRIP","TRIMMING"),
    "VINEGAR": ("BALSAMIC","CIDER","DISTILLED","MALT","PACKET","RED","RICE","SHERRY","SUSHI","WHITE","WINE"),
    "WAFER": ("BISCUIT","CHOC","DISC","FAN","PAPER"),
    "WAFFLE": ("BOWL","CHOC","CINNAMON","MIX","PLAIN"),
    "WATER": ("CANNED","ICE","MELON","ORANGE","SODA","SPARKLING","SPRING","STILL"),
    "WATERCRESS": ("FRESH",),
    "WET": ("NAP",),
    "WHITE": ("BAIT",),
    "WHOLE": ("SHEEPHEAD",),
    "WINE": ("COOKING","PORT","RED","WHITE"),
    "WIPE": ("STERILE",),
    "WONTON": ("CHICKEN","SHRIMP"),
    "WOODEN": ("SPOON",),
    "WRAP": ("FILM","FOIL","PALLET"),
    "YEAST": ("DRY",),
    "YOGURT": ("ASSORTED","CHERRY","COCONUT","CREAM","FROZEN","FRUIT","GREEK","HONEY","LIME","MIX","NATURAL","PLAIN","VANILLA"),
}

FIRST_SECOND_WORD_LOV: set[str] = {
    f"{first} {second}"
    for first, seconds in _FIRST_SECOND_WORD_MAP.items()
    for second in seconds
}


def rule_lov_first_second_word(df: pd.DataFrame) -> list[dict]:
    """Rule L10 — 'First & Second Word' must be a valid approved WORD1 WORD2 pair."""
    rule_name = "Rule L10 — First & Second Word LOV"
    col = "First & Second Word"
    results = []
    if col not in df.columns:
        return results
    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        val = str(raw).strip().upper()
        if val not in FIRST_SECOND_WORD_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'First & Second Word' value '{str(raw).strip()}' is not an approved word pair.",
            ))
    return results


# =============================================================================
# Registry — all global rules in execution order
# =============================================================================

YES_NO_COLS = [
    "Dairy Free", "Gluten Free", "Halal", "Kosher", "Organic",
    "Vegan", "Vegetarian", "Biodegradable or Compostable",
    "Recyclable", "Hazardous Material", "Product Warranty",
    "Perishable Product/Date Tracked",
]
YES_NO_LOV = {"Yes", "No"}


def rule_lov_yes_no(df: pd.DataFrame) -> list[dict]:
    """Rule L8 — Boolean columns must contain 'Yes' or 'No'."""
    rule_name = "Rule L8 — Yes/No LOV"
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


def rule_product_warranty_code(df: pd.DataFrame) -> list[dict]:
    """Rule 11 — Product Warranty Code is conditional on Product Warranty.

    If 'Product Warranty' = Yes  → 'Product Warranty Code' must be filled.
    If 'Product Warranty' = No   → 'Product Warranty Code' must be empty.
    """
    rule_name = "Rule 11 — Product Warranty Code conditional"
    col_w  = "Product Warranty"
    col_wc = "Product Warranty Code"
    results = []
    if col_w not in df.columns or col_wc not in df.columns:
        return results
    for idx, row in df.iterrows():
        warranty  = str(row.get(col_w, "")).strip()
        wc_filled = not is_empty(row.get(col_wc))
        if warranty == "Yes" and not wc_filled:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Product Warranty' is Yes but 'Product Warranty Code' is empty.",
            ))
        elif warranty == "No" and wc_filled:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Product Warranty' is No but 'Product Warranty Code' is filled.",
            ))
    return results


def rule_perishable_food_only(df: pd.DataFrame) -> list[dict]:
    """Rule 12 — 'Perishable Product/Date Tracked' = Yes is only valid for food Attribute Group IDs.

    The set FOOD_ATTRIBUTE_GROUP_IDS must be populated with the confirmed IDs.
    Until populated the rule is skipped gracefully.
    """
    rule_name = "Rule 12 — Perishable only for food attribute groups"
    col_perishable = "Perishable Product/Date Tracked"
    results = []
    if col_perishable not in df.columns or COL_ATTRIBUTE_GROUP_ID not in df.columns:
        return results
    for idx, row in df.iterrows():
        if str(row.get(col_perishable, "")).strip() != "Yes":
            continue
        raw_id = row.get(COL_ATTRIBUTE_GROUP_ID)
        if is_empty(raw_id):
            continue
        attr_id = str(int(float(str(raw_id)))).zfill(8) if str(raw_id).replace(".", "").isdigit() else str(raw_id).strip()
        if attr_id not in FOOD_ATTRIBUTE_GROUP_IDS:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Perishable Product/Date Tracked' is Yes but Attribute Group ID '{attr_id}' is not a food attribute group.",
            ))
    return results


ALLERGEN_COLS = [
    "Almonds", "Barley", "Brazil Nuts", "Cashew Nuts",
    "Celery and products thereof", "Crustaceans and products thereof",
    "Eggs and products thereof", "Fish and products thereof",
    "Gluten at > 20 ppm", "Hazelnuts", "Kamut",
    "Lupin and products thereof", "Macadamia Nuts/Queensland Nuts",
    "Milk and products thereof", "Molluscs and products thereof",
    "Mustard and products thereof", "Nuts", "Oats",
    "Peanuts and products thereof", "Pecan Nuts", "Pistachio Nuts",
    "Rye", "Sesame seeds and products thereof", "Soybeans and products thereof",
    "Spelt", "Sulphur Dioxide > 10 ppm", "Walnuts", "Wheat",
]

ALLERGEN_STATUS_LOV = {"Contains", "May Contain", "Does Not Contain"}


def rule_lov_allergen_status(df: pd.DataFrame) -> list[dict]:
    """Rule L7 — Allergen columns must contain 'Contains', 'May Contain', or 'Does Not Contain'."""
    rule_name = "Rule L7 — Allergen Status LOV"
    results = []
    present = [c for c in ALLERGEN_COLS if c in df.columns]
    for idx, row in df.iterrows():
        for col in present:
            raw = row.get(col)
            if is_empty(raw):
                continue
            if str(raw).strip() not in ALLERGEN_STATUS_LOV:
                results.append(make_result(
                    sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                    rule=rule_name,
                    message=f"Row {excel_row(idx)} — '{col}' value '{str(raw).strip()}' is invalid. Allowed: Contains, May Contain, Does Not Contain.",
                ))
    return results


def rule_supc_unique(df: pd.DataFrame) -> list[dict]:
    """Rule U1 — SUPC must be unique within the file."""
    rule_name = "Rule U1 — SUPC uniqueness"
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


ALL_GLOBAL_RULES = [
    # A. Business Rules
    rule_supc_unique,                     # Rule U1
    rule_split_attributes_required,       # Rule 1
    rule_split_dimensions_within_case,    # Rule 2
    rule_shelf_life_order,                # Rule 4
    rule_no_nutrition_for_non_food,       # Rule 5
    rule_catch_weight_conditional,        # Rule 8
    rule_taric_code_conditional,          # Rule 9
    rule_mandatory_fields,                # Rule 10
    # B. Formatting Rules
    rule_gtin_outer_format,               # Rule 3
    rule_gtin_inner_format,               # Rule F1
    rule_attribute_group_id_format,       # Rule F2
    rule_taric_code_format,               # Rule F3
    rule_integer_fields,                  # Rule F4
    rule_numeric_fields,                  # Rule F5
    rule_country_of_origin_format,        # Rule F6
    rule_description_special_chars,       # Rule F7
    rule_search_name_format,              # Rule F8
    # C. LOV Rules
    rule_lov_attribute_group_id,          # Rule L0
    rule_lov_brand_key,                   # Rule L1
    rule_lov_status,                      # Rule L2
    rule_lov_seasonal,                    # Rule L3
    rule_lov_item_group,                  # Rule L4
    rule_lov_vat_group,                   # Rule L5
    rule_lov_temperature,                 # Rule L6
    rule_lov_allergen_status,             # Rule L7
    rule_lov_generic_gtin,               # Rule L9
    rule_lov_first_second_word,           # Rule L10
    rule_lov_yes_no,                      # Rule L8
    rule_product_warranty_code,           # Rule 11
    rule_perishable_food_only,            # Rule 12
]
