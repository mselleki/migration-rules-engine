# Migration Rules Engine — Validation Rules Reference

**Domains covered:** Product (Global + Local), Customer
**Last updated:** 2026-03-16
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

When both values are present:

```
Case Catch Weight Range From  ≤  Case Catch Weight Range To
```

**Error (missing):** `Row {n} — Catch Weight product is missing: {list}`

**Error (range):** `Row {n} — Catch Weight Range From ({value}) must be ≤ Range To ({value})`

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

### Rule F7 — Description fields special characters

**Columns:** `Description Text`, `Marketing Description`, `Warehouse Description`, `Invoice Description`, `First & Second Word`

Description fields must only contain alphanumeric characters, spaces, and the following allowed special characters:

| Allowed |
|---|
| `%` `&` `(` `)` `*` `+` `-` `.` `/` `™` `®` `Ø` |

The following characters are **not allowed**:

| Not allowed |
|---|
| `,` `!` `"` `#` `$` `'` `:` `;` `<` `=` `>` `?` `@` `[` `\` `]` `^` `_` `` ` `` `{` `\|` `}` `~` |

> Update `DESCRIPTION_COLS` in `global_rules.py` to add or remove columns. Update `DESCRIPTION_ALLOWED_RE` to add or remove allowed characters.

**Error:** `Row {n} — '{column}' contains disallowed character(s): {chars}`

---

### Rule F8 — Search Name format

**Column:** `Search Name`

- Maximum **20 characters**
- No spaces
- Allowed characters: `a-z A-Z 0-9` plus accented letters (see below) and the approved special characters
- **Approved special characters:** `% & ( ) * + - . / ™ ® Ø`
- **Forbidden special characters:** `, ! " # $ ' : ; < = > ? @ [ \ ] ^ _ ` { | } ~`
- **Allowed accented letters:** á Á à À â Â ä Ä å Å æ Æ Ç ç é É è È ê Ê ë Ë í Í ì Ì î Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö ú Ú ù Ù û Û ü Ü ß ÿ Ý

> The same approved/forbidden special character lists apply to all attribute fields across all domains.

**Error:** `Row {n} — 'Search Name' is invalid: {reason(s)}`

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

### Rule L-Brand — Brand Key

**Column:** `Brand Key`
**LOV source:** `reference/Brands.xlsx`

Must be a valid **Sysco (Own) Brand Code** (96 values, e.g. `BRAKES`, `EKOFISK`, `MIGI`) **or** a valid **Vendor Brand Code** (10 335 values, e.g. `EU441`, `EU661`).

**Error:** `Row {n} — 'Brand Key' value '{value}' is not a recognised Sysco or Vendor brand code.`

---

### Rule L-Temp — Min / Max Temperature

**Columns:** `Min Temperature`, `Max Temperature`
**LOV source:** temp

| Code | Description |
|---|---|
| `TEMP18` | -18°C (0°F) |
| `TEMP0` | 0°C (32°F) |
| `TEMP5` | 5°C (41°F) |
| `TEMP8` | 8°C (46.4°F) |

**Error:** `Row {n} — '{column}' value '{value}' is invalid. Allowed: TEMP18, TEMP0, TEMP5, TEMP8.`

---

### Rule L-VAT — Item VAT Purchasing / Selling

**Columns:** `Item VAT - Purchasing`, `Item VAT - Selling`
**LOV source:** vat_group

| Code | Description |
|---|---|
| `I-STD` | Standard – 20% |
| `I-ZERO` | Zero Rated – 0% |
| `I-RED` | Reduced – 5% |

**Error:** `Row {n} — '{column}' value '{value}' is invalid. Allowed: I-STD, I-ZERO, I-RED.`

---

### Rule L-Seasonal — Seasonal

**Column:** `Seasonal`
**LOV source:** Seasonal

| Code | Description |
|---|---|
| `01` | Closed for Spring |
| `02` | Closed for Summer |
| `03` | Closed for Autumn |
| `04` | Closed for Winter |
| `05` | Closed for Summer, Spring |
| `06` | Closed for Autumn, Winter |
| `07` | Closed for Autumn, Winter, Spring |
| `99` | Non-Seasonal |

**Error:** `Row {n} — 'Seasonal' value '{value}' is invalid. Allowed: 01–07, 99.`

---

### Rule L-Status — Status

**Column:** `Status`
**LOV source:** Status

| Value |
|---|
| `Active` |
| `Delisted` |
| `Archived` |

**Error:** `Row {n} — 'Status' value '{value}' is invalid. Allowed: Active, Delisted, Archived.`

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

---

## D — Customer Rules (`customer_rules.py`)

Customer files contain **7 templates** (sheets): `PT`, `Invoice`, `LEA_Invoice`, `OS`, `LEA_OS`, `EmployeeInvoice`, `EmployeeOS`.

### Rule C1 — Intercompany / Trading Partner

**Sheet:** Invoice
**Column:** `Intercompany/Trading Partner`

| Code | Entity |
|---|---|
| `GB01` | Sysco GB (old Brake Bros Ltd) |
| `GB57` | Medina Quay Meats Limited |
| `GB58` | Fresh Direct UK Ltd |
| `GB59` | Kent Frozen Foods |
| `GB80` | Sysco Foods NI Limited |
| `IE01` | Sysco Foods Ireland UC |
| `IE02` | Classic Drinks |
| `IE03` | Ready Chef |
| `IE90` | SMS Int'l Resources Ireland Unlimited |
| `HK91` | SMS GPC International Limited |
| `HK92` | SMS GPC International Resources Limited |
| `SE99` | Menigo Group |
| `SE01` | Menigo Food Service AB |
| `SE02` | Fruktservice i Helsingborg AB |
| `SE03` | Ekofisk |
| `SE04` | Servicestyckarna AB |
| `SE05` | Restaurangakademien |

**Error:** `Row {n} — 'Intercompany/Trading Partner' value '{value}' is not a recognised entity code.`

---

### Rule C2 — Customer Group

**Sheet:** Invoice
**Column:** `Customer Group`

| Code |
|---|
| `BRAKES` · `COUNTRY_CHOICE` · `BCE` · `KFF` · `FRESH_DIRECT` · `MEDINA` · `SYSCO_ROI` · `SYSCO_NI` · `CLASSIC_DRINKS` · `READY_CHEF` · `MENIGO` · `SERVICESTYCKARNA` · `FRUKTSERVICE` · `EKOFISK` · `SYSCO_FRANCE` · `LAG` |

**Error:** `Row {n} — 'Customer Group' value '{value}' is not a recognised customer group code.`

---

### Rule C3 — Division

**Sheet:** LEA_Invoice
**Column:** `Division`

| Code | Description |
|---|---|
| `TRS` | Territory Street Accounts |
| `TRP` | Territory Program |
| `LCC` | Local Contract Customer |
| `CMU` | Corporate Multi Unit |
| `OTH` | Bid & Other |
| `WHL` | Wholesale |
| `MIS` | Miscellaneous |

**Error:** `Row {n} — 'Division' value '{value}' is invalid. Allowed: TRS, TRP, LCC, CMU, OTH, WHL, MIS.`

---

### Rule C4 — Method of Payment

**Sheet:** LEA_Invoice
**Column:** `Method of Payment`

| Code | Description |
|---|---|
| `C_DD_BASE` | Direct Debit Business Base Currency |
| `C_DD_OTHER` | Direct Debit Foreign Currency |
| `C_CASH` | Cash Payment |
| `C_CARD` | Debit/Credit Card Payment |
| `C_STRDCARD` | Purchase/Stored Card Payment |
| `C_BANK` | Direct Payment in Bank |
| `C_SWISH` | Swish Payment |
| `C_AUTOGIRO` | Autogiro Payment |
| `C_CHEQUE` | Cheque Payment |
| `C_CONTRA` | Cust/Vend Contra Account |
| `V_BACS_BAS` | BACS Business Base Currency |
| `V_BACS_OTH` | BACS Foreign Currency |
| `V_CASH` | Cash Payment |
| `V_CARD` | Credit Card Payment |
| `V_SWISH` | Swish Payment |
| `V_AUTOGIRO` | Autogiro Payment |
| `V_BANK` | Direct Payment in Bank |
| `V_CONTRA` | Cust/Vend Contra Account |
| `V_DD_BASE` | Direct Debit Business Base Currency |
| `V_DD_OTHER` | Direct Debit Foreign Currency |
| `V_CHEQUE` | Cheque Payment |

**Error:** `Row {n} — 'Method of Payment' value '{value}' is not a recognised payment method code.`

---

### Rule C5 — Mode of Delivery

**Sheet:** LEA_OS
**Column:** `Mode of Delivery`

| Code | Description |
|---|---|
| `3PL` | Outsourced transportation and warehousing |
| `AIR` | Goods delivered by air |
| `AMB_TRK` | Non-temp controlled trucks |
| `ANY` | Default any vehicle type |
| `BACK_HAUL` | Sysco fleet collects from supplier |
| `BICYCLE` | Delivery by bike |
| `BOAT` | Goods shipped by sea |
| `BULK_CRR` | Large ships for bulk food |
| `COLD_STRG` | Temp-controlled logistics |
| `CONSOL` | Multiple vendors/customers, one transport |
| `CONT_SHIP` | Goods transport via shipping containers |
| `COURIER` | Small parcel deliveries via 3PL |
| `CROSS_DOCK` | Goods moved internally before final receipt |
| `CUST_COLL` | Customers pick up at warehouse |
| `DIRECT` | Items shipped directly from supplier |
| `DRON_DLV` | Delivered via drones |
| `FROZ_TRK` | Trucks with freezers for frozen items |
| `INTERMOD` | Multiple transport modes |
| `PICKUP` | Collection from a designated location |
| `PIPELINE` | Delivery via pipelines |
| `REFR_TRK` | Temp-controlled truck for perishables |
| `TRAIN` | Transport by rail |
| `TRUCK` | Goods delivered by road |

**Error:** `Row {n} — 'Mode of Delivery' value '{value}' is not a recognised delivery mode code.`

---

### Rule C6 — Delivery Terms (Incoterms)

**Sheet:** LEA_OS
**Column:** `Delivery Terms`

| Code | Description |
|---|---|
| `CFR` | Cost & Freight (C&F) |
| `CIF` | Cost, Insurance & Freight |
| `CIP` | Carriage & Insurance Paid |
| `CPT` | Carriage Paid To |
| `DAP` | Delivered At Place |
| `DDP` | Delivered Duty Paid |
| `DPU` | Delivered At Place Unloaded |
| `EXW` | Ex Works |
| `FAS` | Free Alongside Ship |
| `FCA` | Free Carrier |
| `FOB` | Free On Board |

**Error:** `Row {n} — 'Delivery Terms' value '{value}' is not a recognised Incoterms code.`

---

## Summary

### Product — Global Product Data

| Rule | Category | Key column(s) | Status |
|---|---|---|---|
| Rule 1 | Business | Split attributes required | ✅ Active |
| Rule 2 | Business | Split vs Case dimensions | ✅ Active |
| Rule 4 | Business | Shelf Life Sysco < Manufacturer | ✅ Active |
| Rule 5 | Business | Non-food: no nutritional data | ✅ Active |
| Rule 8 | Business | Catch Weight Range From ≤ To | ✅ Active |
| Rule 9 | Business | Taric Code required when flagged | ✅ Active |
| Rule 10 | Business | 45 mandatory fields | ✅ Active |
| Rule 3 | Formatting | GTIN-Outer (8/12/13/14 digits) | ✅ Active |
| Rule F1 | Formatting | GTIN-Inner | ✅ Active |
| Rule F2 | Formatting | Attribute Group ID (8 digits, zero-padded) | ✅ Active |
| Rule F3 | Formatting | Taric Code (8 digits) | ✅ Active |
| Rule F4 | Formatting | 11 integer columns | ✅ Active |
| Rule F5 | Formatting | Weights, dimensions, nutritional | ✅ Active |
| Rule F6 | Formatting | Country of Origin (ISO alpha-2) | ✅ Active |
| Rule F7 | Formatting | Description special characters | ✅ Active |
| Rule F8 | Formatting | Search Name (≤20 chars, no spaces, allowed chars) | ✅ Active |
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
| Rule L-Brand | LOV | Brand Key (96 Sysco + 10 335 Vendor codes) | ✅ Active |
| Rule L-Temp | LOV | Min/Max Temperature (4 codes) | ✅ Active |
| Rule L-VAT | LOV | Item VAT Purchasing/Selling (I-STD/I-ZERO/I-RED) | ✅ Active |
| Rule L-Seasonal | LOV | Seasonal (codes 01–07, 99) | ✅ Active |
| Rule L-Status | LOV | Status (Active/Delisted/Archived) | ✅ Active |

### Product — Local Product Data

| Rule | Category | Key column(s) | Status |
|---|---|---|---|
| LCL-U0 | Uniqueness | SUPC unique | ✅ Active |
| LCL-U1 | Uniqueness | STEP ID unique | ✅ Active |
| LCL-F1 | Formatting | Special characters (Local Product Description, Ecom Description) | ✅ Active |
| LCL-L1 | LOV | Legal Entity (13 entity names) | ✅ Active |
| LCL-L2 | LOV | Status (Active / Delisted / Archived) | ✅ Active |
| LCL-L3 | LOV | Yes/No (Proprietary Product?, Split Product) | ✅ Active |
| LCL-L4 | LOV | Min/Max Temperature (TEMP18 / TEMP0 / TEMP5 / TEMP8) | ✅ Active |
| LCL-L5 | LOV | Item VAT Purchasing/Selling (I-STD / I-ZERO / I-RED) | ✅ Active |
| LCL-L6 | LOV | Item Buyer Group (from reference/Buyer Group.xlsx) | ✅ Active |
| LCL-L7 | LOV | Storage Area (F / C / D) | ✅ Active |
| LCL-L8 | LOV | Product Source Type (STOCKED / JUST_IN_TIME / LEAD_TIME / MAKE_TO_ORDER) | ✅ Active |
| LCL-L9 | LOV | Ecom Hierarchy Level 2 ID (200+ codes) | ✅ Active |

### Customer

| Rule | Sheet | Column | Status |
|---|---|---|---|
| C1 | Invoice | Intercompany/Trading Partner (17 entity codes) | ✅ Active |
| C2 | Invoice | Customer Group (16 codes) | ✅ Active |
| C3 | LEA_Invoice | Division (7 codes) | ✅ Active |
| C4 | LEA_Invoice | Method of Payment (21 codes) | ✅ Active |
| C5 | LEA_OS | Mode of Delivery (23 codes) | ✅ Active |
| C6 | LEA_OS | Delivery Terms / Incoterms (11 codes) | ✅ Active |

### Vendor

| Rule | Sheet | Key column(s) | Status |
|---|---|---|---|
| V-U1 | Invoice | StepID unique | ✅ Active |
| V-B1 | Invoice | Mandatory address fields (Address Line 1, Town/City, Zip/Postal Code) | ✅ Active |
| V-B2 | Invoice | Company Registration Number (mandatory + unique) | ✅ Active |
| V-L1 | Invoice | Intercompany/Trading Partner (17 entity codes) | ✅ Active |
| V-L9 | Invoice | Trade/Indirect Vendor (Trade / Indirect) | ✅ Active |
| V-L11 | Invoice | Country (ISO 3166-1 alpha-2) | ✅ Active |
| V-F1 | Invoice | Search Name (≤20 chars, no spaces, allowed chars) | ✅ Active |
| V-U2 | LEA_Invoice | SUVC Invoice unique | ✅ Active |
| V-L8 | LEA_Invoice | Legal Entity (13 entity names) | ✅ Active |
| V-L2 | LEA_Invoice | Method of Payment (21 codes) | ✅ Active |
| V-L3 | LEA_Invoice | VAT Group (I-STD / I-ZERO / I-RED) | ✅ Active |
| V-L4 | LEA_Invoice | Status (Active / Delisted / Archived) | ✅ Active |
| V-L13 | LEA_Invoice | Cost Centre (25 codes) | ✅ Active |
| V-U3 | OS | SUVC Ordering/Shipping unique | ✅ Active |
| V-L12 | OS | Country (ISO 3166-1 alpha-2) | ✅ Active |
| V-F2 | OS | Search Name (≤20 chars, no spaces, allowed chars) | ✅ Active |
| V-U4 | LEA_OS | SUVC Ordering/Shipping unique | ✅ Active |
| V-L10 | LEA_OS | Legal Entity (13 entity names) | ✅ Active |
| V-L5 | LEA_OS | Delivery Terms / Incoterms (11 codes) | ✅ Active |
| V-L6 | LEA_OS | Mode of Delivery (23 codes) | ✅ Active |
| V-L7 | LEA_OS | Status (Active / Delisted / Archived) | ✅ Active |
| V-L14 | LEA_OS | Buyer Group (from reference/Buyer Group.xlsx) | ✅ Active |
| V-L15 | LEA_OS | Warehouse Code (IW001 / MK001 / EK001) | ✅ Active |
