# Migration Rules Engine — Validation Rules Reference

**Sheet covered:** Global Product Data
**Last updated:** 2026-03-09
**LOV source:** Stibo Master Data Dictionary MVP & Phase 1

---

## Categories

| Prefix | Category | Description |
|---|---|---|
| Rule 1–10 | Business Rules | Logical and conditional constraints |
| Rule F1–F6 | Formatting Rules | Data types, numeric formats, field lengths |
| Rule L0–L9 | LOV Rules | List-of-Values enforcement |

---

## A — Business Rules

### Rule 1 — Split attributes required when sold as split

**Trigger column:** `Legally packaged to be sold as a split?` = `Yes`

All of the following columns must be populated:

| Column |
|---|
| GTIN-Inner |
| Split Pack |
| Split Size |
| Split UOM |
| Split Net Weight |
| Split Tare Weight |
| Split Length |
| Split Width |
| Split Height |
| Splits Per Case |

**Error:** `Row {n} — Split product is missing required split attribute(s): {list}`

---

### Rule 2 — Split dimensions must not exceed Case dimensions

**Trigger column:** `Legally packaged to be sold as a split?` = `Yes`

Only checked when both values are present:

| Split dimension | ≤ | Case dimension |
|---|---|---|
| Split Length | ≤ | Case Length |
| Split Width | ≤ | Case Width |
| Split Height | ≤ | Case Height |
| Split Net Weight | ≤ | Case Net Weight |

**Error:** `Row {n} — {Split attribute} ({value}) exceeds {Case attribute} ({value})`

---

### Rule 4 — Shelf Life order (Global)

**Columns:** `Shelf Life Period in Days (Sysco)`, `Shelf Life Period In Days (Manufacturer)`

When both values are present:

```
Sysco  <  Manufacturer
```

> Note: `Shelf Life Period in Days (Customer)` is on the **Local Product Data** sheet and is validated there.

Values are cast to integer before comparison.

**Error:** `Row {n} — Shelf Life order invalid: Sysco ({s}) must be < Manufacturer ({m})`

---

### Rule 5 — No nutritional data for non-food products

**Trigger column:** `Attribute Group ID` not in `FOOD_ATTRIBUTE_GROUP_IDS`

The following Business Centres are **non-food** and must have all nutritional columns empty:
- `01xxxxxx` — Administrative
- `10xxxxxx` — Disposables
- `18xxxxxx` — Supplies & Equipment

All other Business Centres (02–09, 11–17, 19) are **food**.

The following columns must be empty for non-food products:

| Column |
|---|
| Energy Kcal |
| Energy KJ |
| Fat |
| Of which Saturates |
| Of which Mono-Unsaturates |
| Of which Polyunsaturates |
| Of which Trans Fats |
| Carbohydrate |
| Of which Sugars |
| Of which Polyols |
| Of which Starch |
| Fibre |
| Protein |
| Salt |
| Sodium |

**Error:** `Row {n} — Non-food product (Attribute Group ID: {id}) has nutritional data populated`

---

### Rule 8 — Catch Weight range required

**Trigger column:** `Catch Weight` = `Yes`

The following columns must be populated:
- `Case Catch Weight Range From`
- `Case Catch Weight Range To`

**Error:** `Row {n} — Catch Weight product is missing: {list}`

---

### Rule 9 — Taric Code required when flagged

**Trigger column:** `Does Product Have A Taric Code?` = `Yes`

`Taric Code/Commodity Code` must be populated.

**Error:** `Row {n} — 'Does Product Have A Taric Code?' is Yes but 'Taric Code/Commodity Code' is empty`

---

### Rule 10 — Mandatory fields

All of the following columns must be populated for every row:

| # | Column |
|---|---|
| 1 | SUPC |
| 2 | Attribute Group ID |
| 3 | Brand Key |
| 4 | Customer Branded |
| 5 | Sysco Finance Category |
| 6 | True Vendor Name |
| 7 | First & Second Word |
| 8 | Marketing Description |
| 9 | Warehouse Description |
| 10 | Invoice Description |
| 11 | Item Group |
| 12 | Item Model Group Id |
| 13 | Multi Language Packaging |
| 14 | EU Hub |
| 15 | Constellation |
| 16 | Case Pack |
| 17 | Case Size |
| 18 | Case UOM |
| 19 | Legally packaged to be sold as a split? |
| 20 | Case Net Weight |
| 21 | Case Length |
| 22 | Case Width |
| 23 | Case Height |
| 24 | Catch Weight |
| 25 | Cases per Layer (Standard Pallet) |
| 26 | Layers per Pallet (Standard Pallet) |
| 27 | Dairy Free |
| 28 | Gluten Free |
| 29 | Halal |
| 30 | Kosher |
| 31 | Organic |
| 32 | Vegan |
| 33 | Vegetarian |
| 34 | Biodegradable or Compostable |
| 35 | Recyclable |
| 36 | Hazardous Material |
| 37 | Product Warranty |
| 38 | Perishable Product/Date Tracked |
| 39 | Shelf Life Period In Days (Manufacturer) |
| 40 | Shelf Life Period in Days (Sysco) |
| 41 | Does Product Have A Taric Code? |
| 42 | Country Of Origin - Manufactured |
| 43 | Country Of Origin - Packed |
| 44 | Country Of Origin - Sold From |
| 45 | Country Of Origin - Raw Ingredients |

**Error:** `Row {n} — Missing mandatory field(s): {list}`

---

## B — Formatting Rules

### Rule 3 — GTIN-Outer format

**Column:** `GTIN-Outer`

- Must be numeric (digits only)
- Exact length: **8, 12, 13 or 14** digits
- Null/empty values are skipped
- If Excel stores the value as a float (e.g. `5038961000809.0`), it is converted to integer string before validation

**Error:** `Row {n} — GTIN-Outer '{value}' is invalid. Must be 8, 12, 13 or 14 digits.`

---

### Rule F1 — GTIN-Inner format

**Column:** `GTIN-Inner`

Same rules as GTIN-Outer. Only checked when populated.

**Error:** `Row {n} — GTIN-Inner '{value}' is invalid. Must be 8, 12, 13 or 14 digits.`

---

### Rule F2 — Attribute Group ID format

**Column:** `Attribute Group ID`

Must resolve to **exactly 8 digits** after zero-padding. Excel may drop the leading zero when storing as integer — the value is zero-padded before validation (e.g. `1010100` → `01010100`).

**Error:** `Row {n} — Attribute Group ID '{value}' must be exactly 8 digits.`

---

### Rule F3 — Taric Code format

**Column:** `Taric Code/Commodity Code`

Must be exactly **8 digits** when populated (e.g. `16041997`).

**Error:** `Row {n} — Taric Code '{value}' must be exactly 8 digits.`

---

### Rule F4 — Integer fields

The following columns must contain **whole numbers** (no decimal part) when populated:

| Column |
|---|
| SUPC |
| Case Pack |
| Split Pack |
| Splits Per Case |
| Cases per Layer (Standard Pallet) |
| Layers per Pallet (Standard Pallet) |
| Cases per Layer (Euro Pallet) |
| Layers per Pallet (Euro Pallet) |
| Shelf Life Period In Days (Manufacturer) |
| Shelf Life Period in Days (Sysco) |
| Shelf Life Period in Days (Customer) |

**Error:** `Row {n} — '{column}' must be a whole number, got '{value}'`

---

### Rule F5 — Numeric fields

The following columns must contain valid **numeric values** (float) when populated:

**Weights & Catch Weight**
- Case Net Weight, Case Tare Weight, Case True Net Weight (Drained/Glazed)
- Case Catch Weight Range From, Case Catch Weight Range To
- Split Net Weight, Split Tare Weight, Split True Net Weight (Drained/Glazed)

**Dimensions**
- Case Length, Case Width, Case Height
- Split Length, Split Width, Split Height

**Nutritional**
- Energy Kcal, Energy KJ, Fat, Of which Saturates, Of which Mono-Unsaturates, Of which Polyunsaturates, Of which Trans Fats, Carbohydrate, Of which Sugars, Of which Polyols, Of which Starch, Fibre, Protein, Salt, Sodium

**Error:** `Row {n} — '{column}' must be a number, got '{value}'`

---

### Rule F6 — Country of Origin format

**Columns:**
- `Country Of Origin - Manufactured`
- `Country Of Origin - Packed`
- `Country Of Origin - Sold From`
- `Country Of Origin - Raw Ingredients`

Must be a valid **ISO 3166-1 alpha-2** code: exactly 2 uppercase letters (e.g. `GB`, `FR`, `DE`, `BE`).

**Error:** `Row {n} — '{column}' value '{value}' must be a 2-letter ISO country code (e.g. GB, FR, DE).`

---

## C — LOV Rules

### Rule L0 — Attribute Group ID

**Column:** `Attribute Group ID`
**LOV source:** OSD Hierarchy (Stibo MDD)

Must be one of the 620+ confirmed OSD Hierarchy IDs. Value is zero-padded to 8 digits before checking.

> Update the `ATTRIBUTE_GROUP_ID_LOV` constant in `global_rules.py` if new IDs are added.

**Error:** `Row {n} — Attribute Group ID '{value}' is not a recognised OSD Hierarchy ID.`

---

### Rule L1 — Yes / No columns

The following columns only accept `Yes` or `No`:

| Column |
|---|
| Customer Branded |
| Multi Language Packaging |
| EU Hub |
| Constellation |
| Legally packaged to be sold as a split? |
| Catch Weight |
| Dairy Free |
| Gluten Free |
| Halal |
| Kosher |
| Organic |
| Vegan |
| Vegetarian |
| Recyclable |
| Hazardous Material |
| Product Warranty |
| Perishable Product/Date Tracked |
| Does Product Have A Taric Code? |

**Error:** `Row {n} — '{column}' value '{value}' is invalid. Allowed values: Yes, No.`

---

### Rule L2 — Allergen columns

**Allowed values:** `0`, `1`, `2`
**LOV source:** allergen_Status

| Value | Meaning |
|---|---|
| `0` | Contains |
| `1` | May Contain |
| `2` | Does Not Contain |

**Columns (28):**
Almonds, Barley, Brazil Nuts, Cashew Nuts, Celery and products thereof, Gluten at <gt/> 20 ppm, Crustaceans and products thereof, Eggs and products thereof, Fish and products thereof, Hazelnuts, Kamut, Lupin and products thereof, Macadamia Nuts/Queensland Nuts, Milk and products thereof, Molluscs and products thereof, Mustard and products thereof, Nuts, Oats, Peanuts and products thereof, Pecan Nuts, Pistachio Nuts, Rye, Sesame seeds and products thereof, Soybeans and products thereof, Spelt, Sulphur Dioxide <gt/> 10 ppm, Walnuts, Wheat

**Error:** `Row {n} — '{column}' value '{value}' is invalid. Allowed values: 0 (Contains), 1 (May Contain), 2 (Does Not Contain).`

---

### Rule L3 — Unit of Measure (UOM)

**Columns:** `Case UOM`, `Split UOM`
**LOV source:** UOM (44 confirmed codes)

| Code | Description | Code | Description |
|---|---|---|---|
| `BL` | Block | `MG` | Miligram |
| `BOT` | Bottle | `ML` | Mililitre |
| `BX` | Box | `MM` | Milimetre |
| `BRI` | Brick | `OZ` | Ounce |
| `BUC` | Bucket | `PK` | Pack |
| `BNC` | Bunch | `PKT` | Packet |
| `BUN` | Bundle | `PR` | Pair |
| `CAR` | Carton | `PALLET` | Pallet |
| `CS` | Case | `PC` | Piece |
| `CL` | Centilitre | `PT` | Pint |
| `CM` | Centimetre | `PTN` | Portion |
| `CRA` | Crate | `LB` | Pound |
| `DL` | Decilitre | `PUN` | Punnet |
| `DZ` | Dozen | `SHT` | Sheets |
| `EA` | Each | `SMB` | Small Block |
| `GM` | Gram | `TNK` | Tank |
| `GAL` | Gallon | `TIN` | Tin |
| `HG` | Hectogram | `TRY` | Tray |
| `IN` | Inch | `UN` | Unit |
| `KG` | Kilogram | `POT` | Pot |
| `L` | Litre | `LAY` | Layer |
| `LOAF` | Loaf | `M` | Metre |

> Update `UOM_LOV` in `global_rules.py` if new codes are confirmed.

**Error:** `Row {n} — '{column}' value '{value}' is not a recognised UOM code. Allowed: {list}.`

---

### Rule L4 — Item Group

**Column:** `Item Group`
**LOV source:** item_group

| Value | Description |
|---|---|
| `FG-DRY` | Finished Goods - Dry |
| `FG-COOLER` | Finished Goods - Cooler |
| `FG-FREEZER` | Finished Goods - Freezer |
| `RM-DRY` | Raw Materials - Dry |
| `RM-COOLER` | Raw Materials - Cooler |
| `RM-FREEZER` | Raw Materials - Freezer |
| `NON FOOD` | Non Food |

**Error:** `Row {n} — 'Item Group' value '{value}' is invalid. Allowed: {list}.`

---

### Rule L5 — Item Model Group Id

**Column:** `Item Model Group Id`
**LOV source:** item_model_group

| Value | Description |
|---|---|
| `STK` | Stocked Item |
| `JIT` | Just In Time |
| `RM` | Raw Materials |
| `FG` | Finished Goods |
| `NFI` | Non Food Item |

**Error:** `Row {n} — 'Item Model Group Id' value '{value}' is invalid. Allowed: FG, JIT, NFI, RM, STK.`

---

### Rule L6 — Sysco Finance Category

**Column:** `Sysco Finance Category`
**LOV source:** finance_cat

| Value | Description |
|---|---|
| `PCAT1` | Medical/Hospitality |
| `PCAT2` | Dairy |
| `PCAT3` | Meat |
| `PCAT4` | Seafood |
| `PCAT5` | Poultry |
| `PCAT6` | Frozen |
| `PCAT7` | Canned & Dry |
| `PCAT8` | Paper/Disposables |
| `PCAT9` | Chemical/Janitorial |
| `PCAT10` | Supplier & Equipment |
| `PCAT11` | Produce |
| `PCAT12` | Beverage |

**Error:** `Row {n} — 'Sysco Finance Category' value '{value}' is invalid. Allowed: {list}.`

---

### Rule L7 — Biodegradable or Compostable

**Column:** `Biodegradable or Compostable`
**LOV source:** bio_degr

| Value | Description |
|---|---|
| `BIODEGRADABLE` | Biodegradable |
| `COMPOSTABLE` | Compostable |
| `NOT_APPLICABLE` | Not Applicable |

**Error:** `Row {n} — 'Biodegradable or Compostable' value '{value}' is invalid. Allowed: BIODEGRADABLE, COMPOSTABLE, NOT_APPLICABLE.`

---

### Rule L8 — Nutritional Unit

**Column:** `Nutritional Unit`
**LOV source:** nutritional_unit

| Value | Description |
|---|---|
| `G` | Per 100g |
| `ML` | Per 100ml |

**Error:** `Row {n} — 'Nutritional Unit' value '{value}' is invalid. Allowed: G (per 100g), ML (per 100ml).`

---

### Rule L9 — Generic GTIN

**Column:** `Generic GTIN`
**LOV source:** GenericGTIN (9 confirmed values)

Only checked when the column is populated. Used when a generic/placeholder GTIN is assigned instead of a real GS1 barcode.

| Value | Description |
|---|---|
| `10000000000009` | Butchery |
| `20000000000009` | Inhouse/Catering |
| `30000000000009` | Equipment |
| `40000000000009` | Fishmongery |
| `50000000000009` | Non-GS1 Vendor |
| `60000000000009` | To Be Delisted |
| `70000000000009` | Produce |
| `80000000000009` | Hold GTIN |
| `99999999999999` | Generic placeholder |

**Error:** `Row {n} — 'Generic GTIN' value '{value}' is not a recognised generic GTIN. Allowed: {list}.`

---

## Summary

| Rule | Category | Key column(s) | Status |
|---|---|---|---|
| Rule 1 | Business | Legally packaged to be sold as a split? | ✅ Active |
| Rule 2 | Business | Split vs Case dimensions | ✅ Active |
| Rule 4 | Business | Shelf Life Sysco / Manufacturer | ✅ Active |
| Rule 5 | Business | Attribute Group ID + nutritional columns | ✅ Active |
| Rule 8 | Business | Catch Weight + Range From/To | ✅ Active |
| Rule 9 | Business | Does Product Have A Taric Code? + Taric Code | ✅ Active |
| Rule 10 | Business | 45 mandatory fields | ✅ Active |
| Rule 3 | Formatting | GTIN-Outer | ✅ Active |
| Rule F1 | Formatting | GTIN-Inner | ✅ Active |
| Rule F2 | Formatting | Attribute Group ID (8 digits, zero-padded) | ✅ Active |
| Rule F3 | Formatting | Taric Code/Commodity Code | ✅ Active |
| Rule F4 | Formatting | 11 integer columns | ✅ Active |
| Rule F5 | Formatting | Weights, dimensions, nutritional | ✅ Active |
| Rule F6 | Formatting | Country of Origin (4 columns) | ✅ Active |
| Rule L0 | LOV | Attribute Group ID (620+ OSD IDs) | ✅ Active |
| Rule L1 | LOV | 18 Yes/No columns | ✅ Active |
| Rule L2 | LOV | 28 allergen columns (0/1/2) | ✅ Active |
| Rule L3 | LOV | Case UOM, Split UOM (44 codes) | ✅ Active |
| Rule L4 | LOV | Item Group (7 values) | ✅ Active |
| Rule L5 | LOV | Item Model Group Id (5 values) | ✅ Active |
| Rule L6 | LOV | Sysco Finance Category (PCAT1–PCAT12) | ✅ Active |
| Rule L7 | LOV | Biodegradable or Compostable (3 values) | ✅ Active |
| Rule L8 | LOV | Nutritional Unit (G, ML) | ✅ Active |
| Rule L9 | LOV | Generic GTIN (9 values) | ✅ Active |
