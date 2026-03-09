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
ATTRIBUTE_GROUP_ID_LOV = {
    "01010100", "01010200", "01010300", "01010400", "01010500", "01010600", "01010700",
    "01020100", "01020200", "01020300", "01020400", "01020500", "01020600", "01020700",
    "01020800", "01020900", "01021000",
    "02010100",
    "02020100", "02020200", "02020300", "02020400", "02020500", "02020600", "02020700",
    "02020800",
    "02030100", "02030200", "02030300",
    "02040100",
    "02050100", "02050200", "02050300",
    "02060100", "02060200",
    "02070100", "02070200", "02070300",
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
    "04010200", "04010300", "04010400", "04010500",
    "04020100",
    "04030100",
    "04040100", "04040200", "04040300",
    "04050100",
    "04060100", "04060200", "04060300", "04060400", "04060500",
    "04070100", "04070200",
    "04080200", "04080300",
    "04090100", "04090200", "04090300",
    "05010100", "05010200", "05010300",
    "05020400", "05020500", "05020600", "05020700", "05020800", "05020900", "05021000",
    "05021100", "05021200", "05021300",
    "05030300",
    "05040100", "05040200", "05040300", "05040400", "05040500", "05040600", "05040700",
    "05040800", "05040900", "05041000", "05041100", "05041200", "05041300", "05041400",
    "05041500",
    "06010100", "06010200", "06010300",
    "06020100", "06020200", "06020300", "06020400", "06020500", "06020600", "06020700",
    "06030100",
    "06040100",
    "06050100",
    "06060100", "06060200", "06060300", "06060400", "06060500", "06060600", "06060700",
    "06060800", "06060900",
    "06070100",
    "06080100", "06080200", "06080300",
    "07010200",
    "07020100",
    "07030100", "07030200", "07030300", "07030400", "07030500", "07030600",
    "07040100", "07040200", "07040300",
    "07050100", "07050200",
    "08010100", "08010200", "08010300", "08010400",
    "08020100", "08020200", "08020300",
    "08030100", "08030200",
    "08040100", "08040200",
    "08050100",
    "08060100", "08060200",
    "08070100",
    "08080100", "08080200",
    "08090100", "08090200",
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
    "10010100", "10010200", "10010300", "10010400", "10010500", "10010600",
    "10020100", "10020200",
    "10030100", "10030200",
    "10040100", "10040200", "10040300", "10040400",
    "10050100", "10050200", "10050300",
    "10060100", "10060200", "10060300", "10060400",
    "10070100", "10070200", "10070300", "10070400",
    "10080100", "10080200", "10080300", "10080400", "10080500", "10080600",
    "10090100", "10090200", "10090300", "10090400",
    "10100100",
    "10110100", "10110200",
    "10120100", "10120200", "10120300",
    "10130100", "10130200", "10130300", "10130400",
    "10140100", "10140200", "10140300", "10140400", "10140500", "10140600",
    "10150100",
    "11010100", "11010300", "11010400", "11010500", "11010600", "11010700", "11010800",
    "11010900",
    "11021100", "11021200", "11021300", "11021400", "11021500", "11021600", "11021700",
    "11021800", "11021900", "11022000", "11022100", "11022200", "11022300", "11022400",
    "12010100",
    "12020100",
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
    "17010100", "17010200",
    "17020100",
    "17030100", "17030200", "17030300", "17030400", "17030500", "17030600", "17030700",
    "17030800", "17030900", "17031000", "17031100",
    "17040100",
    "17050100", "17050200", "17050300", "17050400", "17050500", "17050600",
    "17060100", "17060200",
    "18010100", "18010200", "18010300", "18010400", "18010500", "18010600",
    "18020100", "18020200", "18020300", "18020400", "18020500",
    "18030100", "18030200", "18030300",
    "18040100", "18040200", "18040300",
    "18050100", "18050200", "18050300", "18050400",
    "18060100", "18060200", "18060300",
    "18070100",
    "18080100", "18080200",
    "18090100", "18090200", "18090300", "18090400", "18090500", "18090600", "18090700",
    "18090800", "18090900", "18091000",
    "18100100", "18100200", "18100300", "18100400", "18100500", "18100600",
    "18110100", "18110200", "18110300", "18110400", "18110500", "18110600", "18110700",
    "18110800",
    "18120100", "18120200", "18120300", "18120400",
    "18130100", "18130200", "18130300", "18130400", "18130500", "18130600",
    "19010100", "19010200", "19010300", "19010400",
    "19020100", "19020200",
    "19030100",
    "19040100", "19040200", "19040300", "19040400", "19040500", "19040600", "19040700",
    "19040800", "19040900", "19041000", "19041100",
    "19050100", "19050200", "19050300", "19050400", "19050500", "19050600", "19050700",
    "19050800",
}

# ---------------------------------------------------------------------------
# Rule 5 — Food product Attribute Group IDs
# Products whose Attribute Group ID is NOT in this set are treated as non-food
# and must have all nutritional columns empty.
# TODO: confirm with business which IDs from ATTRIBUTE_GROUP_ID_LOV are food.
# ---------------------------------------------------------------------------
FOOD_ATTRIBUTE_GROUP_IDS: set[str] = set()  # placeholder — populate when confirmed

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
    "Recyclable",
    "Hazardous Material",
    "Product Warranty",
    "Perishable Product/Date Tracked",
    "Does Product Have A Taric Code?",
]

# ---------------------------------------------------------------------------
# LOV — Allergen columns (0 = Contains, 1 = May Contain, 2 = Does Not Contain)
# Source: allergen_Status LOV
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
# LOV — Unit of Measure (Stibo UOM codes)
# Source: UOM LOV — 44 codes confirmed
# ---------------------------------------------------------------------------
UOM_LOV = {
    "BL",     # Block
    "BOT",    # Bottle
    "BX",     # Box
    "BRI",    # Brick
    "BUC",    # Bucket
    "BNC",    # Bunch
    "BUN",    # Bundle
    "CAR",    # Carton
    "CS",     # Case
    "CL",     # Centilitre
    "CM",     # Centimetre
    "CRA",    # Crate
    "DL",     # Decilitre
    "DZ",     # Dozen
    "EA",     # Each
    "GM",     # Gram
    "GAL",    # Gallon
    "HG",     # Hectogram
    "IN",     # Inch
    "KG",     # Kilogram
    "L",      # Litre
    "LOAF",   # Loaf
    "M",      # Metre
    "MG",     # Miligram
    "ML",     # Mililitre
    "MM",     # Milimetre
    "OZ",     # Ounce
    "PK",     # Pack
    "PKT",    # Packet
    "PR",     # Pair
    "PALLET", # Pallet
    "PC",     # Piece
    "PT",     # Pint
    "PTN",    # Portion
    "LB",     # Pound
    "PUN",    # Punnet
    "SHT",    # Sheets
    "SMB",    # Small Block
    "TNK",    # Tank
    "TIN",    # Tin
    "TRY",    # Tray
    "UN",     # Unit
    "POT",    # Pot
    "LAY",    # Layer
}

UOM_COLS = [
    "Case UOM",
    "Split UOM",
]

# ---------------------------------------------------------------------------
# LOV — Item Group
# Source: item_group LOV
# ---------------------------------------------------------------------------
ITEM_GROUP_LOV = {
    "FG-DRY",
    "FG-COOLER",
    "FG-FREEZER",
    "RM-DRY",
    "RM-COOLER",
    "RM-FREEZER",
    "NON FOOD",
}

# ---------------------------------------------------------------------------
# LOV — Item Model Group Id
# Source: item_model_group LOV
# ---------------------------------------------------------------------------
ITEM_MODEL_GROUP_LOV = {
    "STK",  # Stocked Item
    "JIT",  # Just In Time
    "RM",   # Raw Materials
    "FG",   # Finished Goods
    "NFI",  # Non Food Item
}

# ---------------------------------------------------------------------------
# LOV — Sysco Finance Category
# Source: finance_cat LOV
# ---------------------------------------------------------------------------
FINANCE_CATEGORY_LOV = {
    "PCAT1",   # Medical/Hospitality
    "PCAT2",   # Dairy
    "PCAT3",   # Meat
    "PCAT4",   # Seafood
    "PCAT5",   # Poultry
    "PCAT6",   # Frozen
    "PCAT7",   # Canned & Dry
    "PCAT8",   # Paper/Disposables
    "PCAT9",   # Chemical/Janitorial
    "PCAT10",  # Supplier & Equipment
    "PCAT11",  # Produce
    "PCAT12",  # Beverage
}

# ---------------------------------------------------------------------------
# LOV — Biodegradable or Compostable
# Source: bio_degr LOV
# ---------------------------------------------------------------------------
BIO_DEGR_LOV = {
    "BIODEGRADABLE",
    "COMPOSTABLE",
    "NOT_APPLICABLE",
}

# ---------------------------------------------------------------------------
# LOV — Nutritional Unit
# Source: nutritional_unit LOV
# ---------------------------------------------------------------------------
NUTRITIONAL_UNIT_LOV = {
    "G",   # Per 100g
    "ML",  # Per 100ml
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
    Rule 4 — Shelf Life order.
    When all three values are present: Customer < Sysco < Manufacturer.
    """
    rule_name = "Rule 4 — Shelf Life order"
    results = []
    required = [COL_SHELF_CUSTOMER, COL_SHELF_SYSCO, COL_SHELF_MANUFACTURER]
    if any(c not in df.columns for c in required):
        return results

    for idx, row in df.iterrows():
        c_raw = row.get(COL_SHELF_CUSTOMER)
        s_raw = row.get(COL_SHELF_SYSCO)
        m_raw = row.get(COL_SHELF_MANUFACTURER)
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
    Note: FOOD_ATTRIBUTE_GROUP_IDS is currently empty — populate when confirmed.
    """
    rule_name = "Rule 5 — Nutritional data must be empty for non-food products"
    results = []
    if not FOOD_ATTRIBUTE_GROUP_IDS or COL_ATTRIBUTE_GROUP_ID not in df.columns:
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
    Source: UOM LOV (44 codes confirmed).
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
    Rule L4 — Item Group must be one of the allowed Stibo values.
    Source: item_group LOV.
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


def rule_lov_item_model_group(df: pd.DataFrame) -> list[dict]:
    """
    Rule L5 — Item Model Group Id must be a valid Stibo code.
    Source: item_model_group LOV.
    """
    rule_name = "Rule L5 — Item Model Group Id LOV"
    results = []
    col = "Item Model Group Id"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in ITEM_MODEL_GROUP_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Item Model Group Id' value '{raw}' is invalid. Allowed: {', '.join(sorted(ITEM_MODEL_GROUP_LOV))}.",
            ))
    return results


def rule_lov_finance_category(df: pd.DataFrame) -> list[dict]:
    """
    Rule L6 — Sysco Finance Category must be a valid PCAT code.
    Source: finance_cat LOV.
    """
    rule_name = "Rule L6 — Sysco Finance Category LOV"
    results = []
    col = "Sysco Finance Category"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in FINANCE_CATEGORY_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Sysco Finance Category' value '{raw}' is invalid. Allowed: {', '.join(sorted(FINANCE_CATEGORY_LOV))}.",
            ))
    return results


def rule_lov_biodegradable(df: pd.DataFrame) -> list[dict]:
    """
    Rule L7 — Biodegradable or Compostable must be BIODEGRADABLE, COMPOSTABLE or NOT_APPLICABLE.
    Source: bio_degr LOV.
    """
    rule_name = "Rule L7 — Biodegradable or Compostable LOV"
    results = []
    col = "Biodegradable or Compostable"
    if col not in df.columns:
        return results

    for idx, row in df.iterrows():
        raw = row.get(col)
        if is_empty(raw):
            continue
        if str(raw).strip() not in BIO_DEGR_LOV:
            results.append(make_result(
                sheet=SHEET, row=excel_row(idx), supc=get_supc(row),
                rule=rule_name,
                message=f"Row {excel_row(idx)} — 'Biodegradable or Compostable' value '{raw}' is invalid. Allowed: {', '.join(sorted(BIO_DEGR_LOV))}.",
            ))
    return results


def rule_lov_nutritional_unit(df: pd.DataFrame) -> list[dict]:
    """
    Rule L8 — Nutritional Unit must be 'G' (per 100g) or 'ML' (per 100ml).
    Source: nutritional_unit LOV.
    """
    rule_name = "Rule L8 — Nutritional Unit LOV"
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
                message=f"Row {excel_row(idx)} — 'Nutritional Unit' value '{raw}' is invalid. Allowed: G (per 100g), ML (per 100ml).",
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
    rule_mandatory_fields,                # Rule 10
    # B. Formatting Rules
    rule_gtin_outer_format,               # Rule 3
    rule_gtin_inner_format,               # Rule F1
    rule_attribute_group_id_format,       # Rule F2
    rule_taric_code_format,               # Rule F3
    rule_integer_fields,                  # Rule F4
    rule_numeric_fields,                  # Rule F5
    rule_country_of_origin_format,        # Rule F6
    # C. LOV Rules
    rule_lov_attribute_group_id,          # Rule L0
    rule_lov_yes_no,                      # Rule L1
    rule_lov_allergens,                   # Rule L2
    rule_lov_uom,                         # Rule L3
    rule_lov_item_group,                  # Rule L4
    rule_lov_item_model_group,            # Rule L5
    rule_lov_finance_category,            # Rule L6
    rule_lov_biodegradable,               # Rule L7
    rule_lov_nutritional_unit,            # Rule L8
]
