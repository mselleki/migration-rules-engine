# Sysco Migration Rules Engine

A React + FastAPI application that validates Sysco migration Excel files against business, formatting, and LOV rules across three domains: **Product**, **Vendor**, and **Customer**.

## Project structure

```
.
├── backend/
│   ├── main.py              # FastAPI app (REST API)
│   ├── requirements.txt
│   ├── validator.py         # Orchestration layer
│   ├── rules/
│   │   ├── global_rules.py  # 23 rules — Global Product Data sheet
│   │   ├── local_rules.py   # Rules — Local Product Data sheet (skeleton)
│   │   └── customer_rules.py# 6 rules — Customer domain (Invoice, LEA_Invoice, LEA_OS)
│   └── utils/
│       ├── helpers.py        # Shared utility functions
│       └── lov_extractor.py  # Reads LOVs.xlsx → lovs_flat.csv
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── pages/           # Dashboard, Validator, LovExplorer, Migrations
│   │   ├── components/      # ThemeProvider, ui/ (button, card, badge, tabs…)
│   │   ├── context/         # HistoryContext (shared run history)
│   │   └── lib/utils.js
│   ├── vite.config.js
│   └── package.json
├── input/
│   ├── Product/             # Migration files to validate (gitignored)
│   ├── Vendor/
│   └── Customer/
├── reference/               # LOVs.xlsx, Brands.xlsx, Attribute Group.xlsx (gitignored)
├── output/                  # Validation results CSV (gitignored)
├── VALIDATION_RULES.md      # Full rule reference
└── README.md
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`. API at `http://localhost:8000`.

## Domains

| Domain | Templates | Status |
|---|---|---|
| Product | Global Product Data, Local Product Data | Rules implemented |
| Customer | PT, Invoice, LEA_Invoice, OS, LEA_OS, EmployeeInvoice, EmployeeOS | Partial (6 rules) |
| Vendor | — | Planned |

## Validation rules summary

### Product — Global Product Data (`global_rules.py`)

| Rule | Category | Description |
|---|---|---|
| G1 | Business | Mandatory fields (45 columns) |
| G2 | Business | Split attributes required when sold as split |
| G3 | Business | Split dimensions ≤ Case dimensions |
| G4 | Business | Shelf Life: Sysco < Manufacturer |
| G5 | Business | No nutritional data for non-food products |
| G6 | Business | Catch Weight: Range From ≤ To |
| G7 | Business | Taric Code required when flagged |
| F1 | Formatting | GTIN-Outer: 8/12/13/14 digits |
| F2 | Formatting | GTIN-Inner: 8/12/13/14 digits |
| F3 | Formatting | Attribute Group ID: 8 digits (zero-padded) |
| F4 | Formatting | Taric Code: 8 digits |
| F5 | Formatting | 11 integer columns |
| F6 | Formatting | Numeric fields (weights, dimensions, nutritional) |
| F7 | Formatting | Country of Origin: ISO alpha-2 |
| F8 | Formatting | Description fields: allowed special characters |
| F9 | Formatting | Search Name: ≤20 chars, no spaces, allowed chars only |
| L0 | LOV | Attribute Group ID (620+ OSD IDs) |
| L1 | LOV | Brand Key (Sysco + Vendor brand codes) |
| L2 | LOV | Min/Max Temperature (TEMP18/TEMP0/TEMP5/TEMP8) |
| L3 | LOV | Item VAT Purchasing/Selling (I-STD/I-ZERO/I-RED) |
| L4 | LOV | Item Group (7 values) |
| L5 | LOV | Seasonal (codes 01–07, 99) |
| L6 | LOV | Status (Active/Delisted/Archived) |

### Customer (`customer_rules.py`)

| Rule | Sheet | Column |
|---|---|---|
| C1 | Invoice | Intercompany/Trading Partner |
| C2 | Invoice | Customer Group |
| C3 | LEA_Invoice | Division |
| C4 | LEA_Invoice | Method of Payment |
| C5 | LEA_OS | Mode of Delivery |
| C6 | LEA_OS | Delivery Terms (Incoterms) |

> See [VALIDATION_RULES.md](VALIDATION_RULES.md) for full rule details, error message formats, and LOV lists.

## Adding new rules

1. Open the relevant rules file (`global_rules.py`, `local_rules.py`, `customer_rules.py`).
2. Write a new function: `def rule_xxx(df: pd.DataFrame) -> list[dict]`.
3. Use `make_result()` from `utils.helpers` to build each error dict.
4. Append the function to the corresponding `ALL_*_RULES` list at the bottom of the file.

## Validation output columns

| Column | Description |
|---|---|
| sheet | Sheet the error originates from |
| row | Excel row number (1-based, header = row 1) |
| supc | SUPC / identifier of the affected record |
| rule | Rule name |
| message | Human-readable error description |
