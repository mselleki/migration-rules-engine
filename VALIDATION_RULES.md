# Migration Rules Engine — Validation Rules Reference

**Sheet couverte :** Global Product Data
**Dernière mise à jour :** 2026-03-09
**Source LOVs :** Stibo Master Data Dictionary MVP & Phase 1

---

## Catégories

| Préfixe | Catégorie | Description |
|---|---|---|
| Rule 1–10 | Business Rules | Contraintes logiques et conditionnelles |
| Rule F1–F6 | Formatting Rules | Types de données, formats numériques |
| Rule L0–L8 | LOV Rules | Listes de valeurs autorisées |

---

## A — Business Rules

### Rule 1 — Split attributes requis si vendu en split

**Colonne déclencheur :** `Legally packaged to be sold as a split?` = `Yes`

Les colonnes suivantes doivent toutes être renseignées :

| Colonne |
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

**Erreur :** `Row {n} — Split product is missing required split attribute(s): {liste}`

---

### Rule 2 — Dimensions split ≤ dimensions case

**Colonne déclencheur :** `Legally packaged to be sold as a split?` = `Yes`

Les dimensions du split ne doivent pas dépasser celles du case (vérifié uniquement si les deux valeurs sont présentes) :

| Dimension split | ≤ | Dimension case |
|---|---|---|
| Split Length | ≤ | Case Length |
| Split Width | ≤ | Case Width |
| Split Height | ≤ | Case Height |
| Split Net Weight | ≤ | Case Net Weight |

**Erreur :** `Row {n} — {Split attribute} ({valeur}) exceeds {Case attribute} ({valeur})`

---

### Rule 4 — Ordre des Shelf Life

**Colonnes :** `Shelf Life Period in Days (Customer)`, `Shelf Life Period in Days (Sysco)`, `Shelf Life Period In Days (Manufacturer)`

Quand les trois valeurs sont présentes :

```
Customer  <  Sysco  <  Manufacturer
```

Les valeurs sont castées en entier avant comparaison.

**Erreur :** `Row {n} — Shelf Life order invalid: Customer ({c}) must be < Sysco ({s}) must be < Manufacturer ({m})`

---

### Rule 5 — Pas de données nutritionnelles pour les non-alimentaires

**Colonne déclencheur :** `Attribute Group ID` n'appartient pas à `FOOD_ATTRIBUTE_GROUP_IDS`

> ⚠️ **Règle désactivée** — `FOOD_ATTRIBUTE_GROUP_IDS` est vide en attente de confirmation par le business sur quels IDs OSD correspondent aux produits alimentaires.

Les colonnes suivantes doivent être vides pour les produits non-alimentaires :

| Colonne |
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

**Erreur :** `Row {n} — Non-food product (Attribute Group ID: {id}) has nutritional data populated`

---

### Rule 8 — Catch Weight range obligatoire

**Colonne déclencheur :** `Catch Weight` = `Yes`

Les colonnes suivantes doivent être renseignées :

- `Case Catch Weight Range From`
- `Case Catch Weight Range To`

**Erreur :** `Row {n} — Catch Weight product is missing: {liste}`

---

### Rule 9 — Taric Code obligatoire si flagué

**Colonne déclencheur :** `Does Product Have A Taric Code?` = `Yes`

La colonne `Taric Code/Commodity Code` doit être renseignée.

**Erreur :** `Row {n} — 'Does Product Have A Taric Code?' is Yes but 'Taric Code/Commodity Code' is empty`

---

### Rule 10 — Champs obligatoires

Les colonnes suivantes doivent être renseignées pour chaque ligne :

| # | Colonne |
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

**Erreur :** `Row {n} — Missing mandatory field(s): {liste}`

---

## B — Formatting Rules

### Rule 3 — Format GTIN-Outer

**Colonne :** `GTIN-Outer`

- Doit être numérique (chiffres uniquement)
- Longueur exacte : **8, 12, 13 ou 14** chiffres
- Les valeurs null/vides sont ignorées
- Si Excel stocke la valeur en float (ex: `5038961000809.0`), la conversion en entier est appliquée avant vérification

**Erreur :** `Row {n} — GTIN-Outer '{valeur}' is invalid. Must be 8, 12, 13 or 14 digits.`

---

### Rule F1 — Format GTIN-Inner

**Colonne :** `GTIN-Inner`

Mêmes règles que GTIN-Outer. Vérifié uniquement si la valeur est présente.

**Erreur :** `Row {n} — GTIN-Inner '{valeur}' is invalid. Must be 8, 12, 13 or 14 digits.`

---

### Rule F2 — Format Attribute Group ID

**Colonne :** `Attribute Group ID`

Doit résoudre à **exactement 8 chiffres** après normalisation (zero-padding). Excel peut supprimer le zéro de tête en stockant la valeur comme entier — la valeur est zero-paddée avant vérification (ex: `1010100` → `01010100`).

**Erreur :** `Row {n} — Attribute Group ID '{valeur}' must be exactly 8 digits.`

---

### Rule F3 — Format Taric Code

**Colonne :** `Taric Code/Commodity Code`

Doit être composé de **exactement 8 chiffres** quand renseigné (ex: `16041997`).

**Erreur :** `Row {n} — Taric Code '{valeur}' must be exactly 8 digits.`

---

### Rule F4 — Champs entiers (Integer)

Les colonnes suivantes doivent contenir des **nombres entiers** (sans décimales) :

| Colonne |
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

**Erreur :** `Row {n} — '{colonne}' must be a whole number, got '{valeur}'`

---

### Rule F5 — Champs numériques

Les colonnes suivantes doivent contenir des **valeurs numériques** valides (float) quand renseignées :

**Poids & Catch Weight**
- Case Net Weight, Case Tare Weight, Case True Net Weight (Drained/Glazed)
- Case Catch Weight Range From, Case Catch Weight Range To
- Split Net Weight, Split Tare Weight, Split True Net Weight (Drained/Glazed)

**Dimensions**
- Case Length, Case Width, Case Height
- Split Length, Split Width, Split Height

**Nutritionnel**
- Energy Kcal, Energy KJ, Fat, Of which Saturates, Of which Mono-Unsaturates, Of which Polyunsaturates, Of which Trans Fats, Carbohydrate, Of which Sugars, Of which Polyols, Of which Starch, Fibre, Protein, Salt, Sodium

**Erreur :** `Row {n} — '{colonne}' must be a number, got '{valeur}'`

---

### Rule F6 — Format Country of Origin

**Colonnes :**
- `Country Of Origin - Manufactured`
- `Country Of Origin - Packed`
- `Country Of Origin - Sold From`
- `Country Of Origin - Raw Ingredients`

Doit être un **code ISO 3166-1 alpha-2** : exactement 2 lettres majuscules (ex: `GB`, `FR`, `DE`, `BE`).

**Erreur :** `Row {n} — '{colonne}' value '{valeur}' must be a 2-letter ISO country code (e.g. GB, FR, DE).`

---

## C — LOV Rules

### Rule L0 — Attribute Group ID

**Colonne :** `Attribute Group ID`
**Source LOV :** OSD Hierarchy (Stibo MDD)

La valeur doit appartenir à la liste des IDs OSD Hierarchy confirmés (620+ valeurs).
La valeur est zero-paddée à 8 chiffres avant vérification.

> Mettre à jour la constante `ATTRIBUTE_GROUP_ID_LOV` dans `global_rules.py` si de nouveaux IDs sont ajoutés.

**Erreur :** `Row {n} — Attribute Group ID '{valeur}' is not a recognised OSD Hierarchy ID.`

---

### Rule L1 — Colonnes Yes / No

Les colonnes suivantes n'acceptent que les valeurs `Yes` ou `No` :

| Colonne |
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

**Erreur :** `Row {n} — '{colonne}' value '{valeur}' is invalid. Allowed values: Yes, No.`

---

### Rule L2 — Colonnes Allergènes

**Valeurs autorisées :** `0`, `1`, `2`
**Source LOV :** allergen_Status

| Valeur | Signification |
|---|---|
| `0` | Contains |
| `1` | May Contain |
| `2` | Does Not Contain |

**Colonnes concernées (28) :**
Almonds, Barley, Brazil Nuts, Cashew Nuts, Celery and products thereof, Gluten at <gt/> 20 ppm, Crustaceans and products thereof, Eggs and products thereof, Fish and products thereof, Hazelnuts, Kamut, Lupin and products thereof, Macadamia Nuts/Queensland Nuts, Milk and products thereof, Molluscs and products thereof, Mustard and products thereof, Nuts, Oats, Peanuts and products thereof, Pecan Nuts, Pistachio Nuts, Rye, Sesame seeds and products thereof, Soybeans and products thereof, Spelt, Sulphur Dioxide <gt/> 10 ppm, Walnuts, Wheat

**Erreur :** `Row {n} — '{colonne}' value '{valeur}' is invalid. Allowed values: 0 (Contains), 1 (May Contain), 2 (Does Not Contain).`

---

### Rule L3 — Unit of Measure (UOM)

**Colonnes :** `Case UOM`, `Split UOM`
**Source LOV :** UOM (44 codes confirmés)

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

> Étendre la constante `UOM_LOV` dans `global_rules.py` si de nouveaux codes sont confirmés.

**Erreur :** `Row {n} — '{colonne}' value '{valeur}' is not a recognised UOM code. Allowed: {liste}.`

---

### Rule L4 — Item Group

**Colonne :** `Item Group`
**Source LOV :** item_group

| Valeur | Description |
|---|---|
| `FG-DRY` | Finished Goods - Dry |
| `FG-COOLER` | Finished Goods - Cooler |
| `FG-FREEZER` | Finished Goods - Freezer |
| `RM-DRY` | Raw Materials - Dry |
| `RM-COOLER` | Raw Materials - Cooler |
| `RM-FREEZER` | Raw Materials - Freezer |
| `NON FOOD` | Non Food |

**Erreur :** `Row {n} — 'Item Group' value '{valeur}' is invalid. Allowed: {liste}.`

---

### Rule L5 — Item Model Group Id

**Colonne :** `Item Model Group Id`
**Source LOV :** item_model_group

| Valeur | Description |
|---|---|
| `STK` | Stocked Item |
| `JIT` | Just In Time |
| `RM` | Raw Materials |
| `FG` | Finished Goods |
| `NFI` | Non Food Item |

**Erreur :** `Row {n} — 'Item Model Group Id' value '{valeur}' is invalid. Allowed: FG, JIT, NFI, RM, STK.`

---

### Rule L6 — Sysco Finance Category

**Colonne :** `Sysco Finance Category`
**Source LOV :** finance_cat

| Valeur | Description |
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

**Erreur :** `Row {n} — 'Sysco Finance Category' value '{valeur}' is invalid. Allowed: {liste}.`

---

### Rule L7 — Biodegradable or Compostable

**Colonne :** `Biodegradable or Compostable`
**Source LOV :** bio_degr

| Valeur | Description |
|---|---|
| `BIODEGRADABLE` | Biodegradable |
| `COMPOSTABLE` | Compostable |
| `NOT_APPLICABLE` | Not Applicable |

**Erreur :** `Row {n} — 'Biodegradable or Compostable' value '{valeur}' is invalid. Allowed: BIODEGRADABLE, COMPOSTABLE, NOT_APPLICABLE.`

---

### Rule L8 — Nutritional Unit

**Colonne :** `Nutritional Unit`
**Source LOV :** nutritional_unit

| Valeur | Description |
|---|---|
| `G` | Per 100g |
| `ML` | Per 100ml |

**Erreur :** `Row {n} — 'Nutritional Unit' value '{valeur}' is invalid. Allowed: G (per 100g), ML (per 100ml).`

---

## Récapitulatif

| Règle | Catégorie | Colonnes clés | Statut |
|---|---|---|---|
| Rule 1 | Business | Legally packaged to be sold as a split? | ✅ Active |
| Rule 2 | Business | Split vs Case dimensions | ✅ Active |
| Rule 4 | Business | Shelf Life Customer / Sysco / Manufacturer | ✅ Active |
| Rule 5 | Business | Attribute Group ID + colonnes nutritionnelles | ⚠️ Désactivée (FOOD IDs à confirmer) |
| Rule 8 | Business | Catch Weight + Range From/To | ✅ Active |
| Rule 9 | Business | Does Product Have A Taric Code? + Taric Code | ✅ Active |
| Rule 10 | Business | 45 champs obligatoires | ✅ Active |
| Rule 3 | Formatting | GTIN-Outer | ✅ Active |
| Rule F1 | Formatting | GTIN-Inner | ✅ Active |
| Rule F2 | Formatting | Attribute Group ID (8 chiffres, zero-padded) | ✅ Active |
| Rule F3 | Formatting | Taric Code/Commodity Code | ✅ Active |
| Rule F4 | Formatting | 11 colonnes entières | ✅ Active |
| Rule F5 | Formatting | Poids, dimensions, nutritionnel | ✅ Active |
| Rule F6 | Formatting | Country of Origin (4 colonnes) | ✅ Active |
| Rule L0 | LOV | Attribute Group ID (620+ IDs OSD) | ✅ Active |
| Rule L1 | LOV | 18 colonnes Yes/No | ✅ Active |
| Rule L2 | LOV | 28 colonnes allergènes (0/1/2) | ✅ Active |
| Rule L3 | LOV | Case UOM, Split UOM (44 codes) | ✅ Active |
| Rule L4 | LOV | Item Group (7 valeurs) | ✅ Active |
| Rule L5 | LOV | Item Model Group Id (5 valeurs) | ✅ Active |
| Rule L6 | LOV | Sysco Finance Category (PCAT1–PCAT12) | ✅ Active |
| Rule L7 | LOV | Biodegradable or Compostable (3 valeurs) | ✅ Active |
| Rule L8 | LOV | Nutritional Unit (G, ML) | ✅ Active |
