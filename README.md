# Sysco Migration Rules Engine

A Streamlit application that validates Sysco product migration Excel files against a comprehensive set of business, formatting, and LOV rules.

## Project structure

```
.
├── app.py               # Streamlit UI
├── validator.py         # Orchestrates validation across both files
├── rules/
│   ├── __init__.py
│   ├── global_rules.py  # 25 rules for Global Product Data
│   └── local_rules.py   # Rules for Local Product Data (skeleton)
├── utils/
│   ├── __init__.py
│   └── helpers.py       # Shared utility functions
├── input/               # Excel input files (Global & Local Product Data)
├── VALIDATION_RULES.md  # Full rule reference (English)
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv           # or: py -3 -m venv .venv  (Windows)
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
```

## Running the app

```bash
streamlit run app.py
```

## Input files

Upload two separate `.xlsx` files — one per sheet:

| File | Sheet | Description |
|---|---|---|
| Global Product Data | Global Product Data | Product master attributes |
| Local Product Data | Local Product Data | Market-specific data |

Both files are optional — you can validate either one independently.

## Implemented rules (Global Product Data)

### A — Business Rules

| Rule | Description |
|---|---|
| Rule 1 | Split attributes are all populated when sold as a split |
| Rule 2 | Split dimensions do not exceed Case dimensions |
| Rule 4 | Shelf Life order: Sysco < Manufacturer |
| Rule 5 | Non-food products have no nutritional data populated |
| Rule 8 | Catch Weight products have Range From/To populated and From ≤ To |
| Rule 9 | Taric Code populated when flagged |
| Rule 10 | 45 mandatory fields are populated |

### B — Formatting Rules

| Rule | Description |
|---|---|
| Rule 3 | GTIN-Outer: numeric, 8/12/13/14 digits |
| Rule F1 | GTIN-Inner: numeric, 8/12/13/14 digits (when populated) |
| Rule F2 | Attribute Group ID: exactly 8 digits (zero-padded) |
| Rule F3 | Taric Code/Commodity Code: exactly 8 digits (when populated) |
| Rule F4 | 11 integer columns must contain whole numbers |
| Rule F5 | Weight, dimension, and nutritional columns must be numeric |
| Rule F6 | Country of Origin: valid ISO 3166-1 alpha-2 code |
| Rule F7 | Description fields: allowed special characters only |
| Rule F8 | Search Name: alphanumeric only, no spaces, max 20 characters |

### C — LOV Rules

| Rule | Column | Allowed values |
|---|---|---|
| Rule L0 | Attribute Group ID | 620+ OSD Hierarchy IDs |
| Rule L1 | 18 Yes/No columns | Yes, No |
| Rule L2 | 28 allergen columns | 0 (Contains), 1 (May Contain), 2 (Does Not Contain) |
| Rule L3 | Case UOM, Split UOM | 44 Stibo UOM codes |
| Rule L4 | Item Group | FG-DRY, FG-COOLER, FG-FREEZER, RM-DRY, RM-COOLER, RM-FREEZER, NON FOOD |
| Rule L5 | Item Model Group Id | STK, JIT, RM, FG, NFI |
| Rule L6 | Sysco Finance Category | PCAT1–PCAT12 |
| Rule L7 | Biodegradable or Compostable | BIODEGRADABLE, COMPOSTABLE, NOT_APPLICABLE |
| Rule L8 | Nutritional Unit | G, ML |
| Rule L9 | Generic GTIN | 9 authorised placeholder values |

> See [VALIDATION_RULES.md](VALIDATION_RULES.md) for full rule details, error message formats, and LOV lists.

## Adding new rules

1. Open `rules/global_rules.py` (or `local_rules.py` for Local rules).
2. Write a new function: `def rule_xxx(df: pd.DataFrame) -> list[dict]`.
3. Use `make_result()` from `utils.helpers` to build each error dict.
4. Append the function to `ALL_GLOBAL_RULES` (or `ALL_LOCAL_RULES`) at the bottom of the file.

## Validation output columns

| Column | Description |
|---|---|
| sheet | Sheet the error originates from |
| row | Excel row number (1-based, header = row 1) |
| supc | SUPC of the affected product |
| rule | Rule name |
| message | Human-readable error description |
