# Sysco Migration Rules Engine

A Streamlit application that validates Sysco product migration Excel files against a set of configurable business rules.

## Project structure

```
migration-rules-engine/
├── app.py               # Streamlit UI
├── validator.py         # Orchestrates validation across both sheets
├── rules/
│   ├── __init__.py
│   ├── global_rules.py  # Rules for Global Product Data sheet
│   └── local_rules.py   # Rules for Local Product Data sheet
├── utils/
│   ├── __init__.py
│   └── helpers.py       # Shared utility functions
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Running the app

```bash
streamlit run app.py
```

## Input file format

The uploaded `.xlsx` file must contain two sheets:

| Sheet name | Description |
|---|---|
| Global Product Data | Product attributes validated by Rules 1–5 |
| Local Product Data | Local / market-specific data (rules can be added) |

## Implemented rules

| Rule | Sheet | Description |
|---|---|---|
| Rule 1 | Global | Split attributes are all populated when sold as a split |
| Rule 2 | Global | Split dimensions do not exceed Case dimensions |
| Rule 3 | Global | GTIN-Outer is numeric and 8, 12, 13 or 14 digits |
| Rule 4 | Global | Shelf life order: Customer < Sysco < Manufacturer |
| Rule 5 | Global | Non-food products have no nutritional data populated |

## Adding new rules

### Global rules

1. Open `rules/global_rules.py`.
2. Write a new function with the signature `def rule_xxx(df: pd.DataFrame) -> list[dict]`.
3. Use `make_result()` from `utils.helpers` to build each error object.
4. Append the function to `ALL_GLOBAL_RULES` at the bottom of the file.

### Local rules

Same process, but in `rules/local_rules.py` and `ALL_LOCAL_RULES`.

### Updating the food product Attribute Group ID list (Rule 5)

In `rules/global_rules.py`, find the constant `FOOD_ATTRIBUTE_GROUP_IDS` near the top of the file. Add or remove string IDs as needed.

## Validation output columns

| Column | Description |
|---|---|
| sheet | Sheet the error originates from |
| row | Excel row number (1-based, header = row 1) |
| supc | SUPC of the affected product |
| rule | Rule name |
| message | Human-readable error description |
