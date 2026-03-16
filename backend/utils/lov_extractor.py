"""
Extract LOV data from curated reference files only.

Sources:
  - reference/Attribute Group.xlsx   → Attribute Group ID
  - reference/Brands.xlsx            → Sysco Brand Code, Vendor Brand Code
  - reference/Buyer Group.xlsx       → Buyer Group
  - reference/Commodity code.xlsx    → Commodity Code / Taric
  - Hardcoded constants              → Status, Seasonal, Item Group, VAT, Temp,
                                       UOM, allergens, and Customer LOVs
"""

from __future__ import annotations
from typing import Optional
import pandas as pd


# ---------------------------------------------------------------------------
# File-based extractors
# ---------------------------------------------------------------------------

def extract_attribute_groups(path: str) -> pd.DataFrame:
    """
    Attribute Group.xlsx — Row 0: title, Row 1: headers, Row 2+: data
    Columns: Business Centre | Item Group | Attribute Group | STIBO ID
    """
    df = pd.read_excel(path, sheet_name=0, header=None)
    data = df.iloc[2:, [0, 1, 2, 3]].copy()
    data.columns = ["business_centre", "item_group", "attribute_group", "stibo_id"]
    data = data.dropna(subset=["stibo_id"])

    records = []
    for _, row in data.iterrows():
        raw = str(row["stibo_id"]).strip()
        key = str(int(float(raw))).zfill(8) if raw.replace(".", "").isdigit() else raw
        desc = " > ".join(
            str(row[c]).strip()
            for c in ["business_centre", "item_group", "attribute_group"]
            if not pd.isna(row[c]) and str(row[c]).strip()
        )
        records.append({"attribute": "Attribute Group ID", "key": key, "description": desc})

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


def extract_brands(path: str) -> pd.DataFrame:
    """
    Brands.xlsx — Row 0: title, Row 1: headers, Row 2+: data
    Cols 0-1: Sysco Brand Code | Sysco Brand
    Cols 3-4: Vendor Brand Code | Vendor Brand
    """
    df = pd.read_excel(path, sheet_name=0, header=None)
    records = []

    for _, row in df.iloc[2:].iterrows():
        code = row.iloc[0]
        name = row.iloc[1]
        if not pd.isna(code) and str(code).strip():
            records.append({
                "attribute": "Sysco Brand Code",
                "key": str(code).strip(),
                "description": "" if pd.isna(name) else str(name).strip(),
            })

    for _, row in df.iloc[2:].iterrows():
        code = row.iloc[3]
        name = row.iloc[4]
        if not pd.isna(code) and str(code).strip():
            records.append({
                "attribute": "Vendor Brand Code",
                "key": str(code).strip(),
                "description": "" if pd.isna(name) else str(name).strip(),
            })

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


def extract_buyer_groups(path: str) -> pd.DataFrame:
    """
    Buyer Group.xlsx — Row 0: title, Row 1: headers (LE | ID | Description), Row 2+: data
    """
    df = pd.read_excel(path, sheet_name=0, header=None)
    data = df.iloc[2:, [0, 1, 2]].copy()
    data.columns = ["le", "id", "description"]
    data = data.dropna(subset=["id"])

    records = []
    for _, row in data.iterrows():
        key = str(row["id"]).strip()
        le = "" if pd.isna(row["le"]) else str(row["le"]).strip()
        desc = "" if pd.isna(row["description"]) else str(row["description"]).strip()
        label = f"{le} — {desc}" if le else desc
        records.append({"attribute": "Buyer Group", "key": key, "description": label})

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


def extract_commodity_codes(path: str) -> pd.DataFrame:
    """
    Commodity code.xlsx — Row 0: title, Row 1: headers (Code | Name), Row 2+: data
    """
    df = pd.read_excel(path, sheet_name=0, header=None)
    data = df.iloc[2:, [0, 1]].copy()
    data.columns = ["code", "name"]
    data = data.dropna(subset=["code"])

    records = []
    for _, row in data.iterrows():
        raw = str(row["code"]).strip()
        key = str(int(float(raw))).zfill(8) if raw.replace(".", "").isdigit() else raw
        desc = "" if pd.isna(row["name"]) else str(row["name"]).strip()
        records.append({"attribute": "Commodity Code", "key": key, "description": desc})

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


# ---------------------------------------------------------------------------
# Hardcoded LOVs (provided explicitly by business)
# ---------------------------------------------------------------------------

def get_hardcoded_lovs() -> pd.DataFrame:
    rows = []

    def add(attribute, key, description=""):
        rows.append({"attribute": attribute, "key": key, "description": description})

    # Status
    for v in ["Active", "Delisted", "Archived"]:
        add("Status", v)

    # Seasonal
    for code, desc in [
        ("01", "Closed for Spring"), ("02", "Closed for Summer"),
        ("03", "Closed for Autumn"), ("04", "Closed for Winter"),
        ("05", "Closed for Summer, Spring"), ("06", "Closed for Autumn, Winter"),
        ("07", "Closed for Autumn, Winter, Spring"), ("99", "Non-Seasonal"),
    ]:
        add("Seasonal", code, desc)

    # Item Group
    for code, desc in [
        ("RM-DRY", "Raw Materials - Dry"), ("RM-COOLER", "Raw Materials - Cooler"),
        ("RM-FREEZER", "Raw Materials - Freezer"), ("FG-DRY", "Finished Goods - Dry"),
        ("FG-COOLER", "Finished Goods - Cooler"), ("FG-FREEZER", "Finished Goods - Freezer"),
        ("NON FOOD", "Non Food"),
    ]:
        add("Item Group", code, desc)

    # Item VAT (Purchasing + Selling share same values)
    for code, desc in [
        ("I-STD", "Standard – 20%"), ("I-ZERO", "Zero Rated – 0%"), ("I-RED", "Reduced – 5%"),
    ]:
        add("Item VAT", code, desc)

    # Temperature
    for code, desc in [
        ("TEMP18", "-18°C (0°F)"), ("TEMP0", "0°C (32°F)"),
        ("TEMP5", "5°C (41°F)"), ("TEMP8", "8°C (46.4°F)"),
    ]:
        add("Temperature", code, desc)

    # --- Customer LOVs ---

    # Intercompany / Trading Partner
    for code, desc in [
        ("GB01", "Sysco GB (old Brake Bros Ltd)"), ("GB57", "Medina Quay Meats Limited"),
        ("GB58", "Fresh Direct UK Ltd"), ("GB59", "Kent Frozen Foods"),
        ("GB80", "Sysco Foods NI Limited"), ("IE01", "Sysco Foods Ireland UC"),
        ("IE02", "Classic Drinks"), ("IE03", "Ready Chef"),
        ("IE90", "SMS Int'l Resources Ireland Unlimited"),
        ("HK91", "SMS GPC International Limited"),
        ("HK92", "SMS GPC International Resources Limited"),
        ("SE99", "Menigo Group"), ("SE01", "Menigo Food Service AB"),
        ("SE02", "Fruktservice i Helsingborg AB"), ("SE03", "Ekofisk"),
        ("SE04", "Servicestyckarna AB"), ("SE05", "Restaurangakademien"),
    ]:
        add("Intercompany/Trading Partner", code, desc)

    # Customer Group
    for code, desc in [
        ("BRAKES", "Brakes"), ("COUNTRY_CHOICE", "Country Choice"), ("BCE", "BCE"),
        ("KFF", "KFF"), ("FRESH_DIRECT", "Fresh Direct"), ("MEDINA", "Medina"),
        ("SYSCO_ROI", "Sysco ROI"), ("SYSCO_NI", "Sysco NI"),
        ("CLASSIC_DRINKS", "Classic Drinks"), ("READY_CHEF", "Ready Chef"),
        ("MENIGO", "Menigo"), ("SERVICESTYCKARNA", "Servicestyckarna"),
        ("FRUKTSERVICE", "Fruktservice"), ("EKOFISK", "Ekofisk"),
        ("SYSCO_FRANCE", "Sysco France"), ("LAG", "LAG"),
    ]:
        add("Customer Group", code, desc)

    # Division
    for code, desc in [
        ("TRS", "Territory Street Accounts"), ("TRP", "Territory Program"),
        ("LCC", "Local Contract Customer"), ("CMU", "Corporate Multi Unit"),
        ("OTH", "Bid & Other"), ("WHL", "Wholesale"), ("MIS", "Miscellaneous"),
    ]:
        add("Division", code, desc)

    # Method of Payment
    for code, desc in [
        ("C_DD_BASE", "Direct Debit Business Base Currency"),
        ("C_DD_OTHER", "Direct Debit Foreign Currency"),
        ("C_CASH", "Cash Payment"), ("C_CARD", "Debit/Credit Card Payment"),
        ("C_STRDCARD", "Purchase/Stored Card Payment"),
        ("C_BANK", "Direct Payment in Bank"), ("C_SWISH", "Swish Payment"),
        ("C_AUTOGIRO", "Autogiro Payment"), ("C_CHEQUE", "Cheque Payment"),
        ("C_CONTRA", "Cust/Vend Contra Account"),
        ("V_BACS_BAS", "BACS Business Base Currency"),
        ("V_BACS_OTH", "BACS Foreign Currency"), ("V_CASH", "Cash Payment"),
        ("V_CARD", "Credit Card Payment"), ("V_SWISH", "Swish Payment"),
        ("V_AUTOGIRO", "Autogiro Payment"), ("V_BANK", "Direct Payment in Bank"),
        ("V_CONTRA", "Cust/Vend Contra Account"),
        ("V_DD_BASE", "Direct Debit Business Base Currency"),
        ("V_DD_OTHER", "Direct Debit Foreign Currency"), ("V_CHEQUE", "Cheque Payment"),
    ]:
        add("Method of Payment", code, desc)

    # Mode of Delivery
    for code, desc in [
        ("3PL", "Outsourced Transportation and Warehousing"),
        ("AIR", "Goods Delivered by Air"), ("AMB_TRK", "Non-Temp Controlled Trucks"),
        ("ANY", "Default Any Vehicle Type"), ("BACK_HAUL", "Sysco Fleet Collects from Supplier"),
        ("BICYCLE", "Delivery by Bike"), ("BOAT", "Goods Shipped by Sea"),
        ("BULK_CRR", "Large Ships for Bulk Food"), ("COLD_STRG", "Temp-Controlled Logistics"),
        ("CONSOL", "Multiple Vendors/Customers, One Transport"),
        ("CONT_SHIP", "Goods Transport via Shipping Containers"),
        ("COURIER", "Small Parcel Deliveries via 3PL"),
        ("CROSS_DOCK", "Goods Moved Internally Before Final Receipt"),
        ("CUST_COLL", "Customers Pick Up at Warehouse"),
        ("DIRECT", "Items Shipped Directly from Supplier"),
        ("DRON_DLV", "Delivered via Drones"), ("FROZ_TRK", "Trucks with Freezers for Frozen Items"),
        ("INTERMOD", "Multiple Transport Modes"), ("PICKUP", "Collection from Designated Location"),
        ("PIPELINE", "Delivery via Pipelines"), ("REFR_TRK", "Temp-Controlled Truck for Perishables"),
        ("TRAIN", "Transport by Rail"), ("TRUCK", "Goods Delivered by Road"),
    ]:
        add("Mode of Delivery", code, desc)

    # Delivery Terms (Incoterms)
    for code, desc in [
        ("CFR", "Cost & Freight (C&F)"), ("CIF", "Cost, Insurance & Freight"),
        ("CIP", "Carriage & Insurance Paid"), ("CPT", "Carriage Paid To"),
        ("DAP", "Delivered At Place"), ("DDP", "Delivered Duty Paid"),
        ("DPU", "Delivered At Place Unloaded"), ("EXW", "Ex Works"),
        ("FAS", "Free Alongside Ship"), ("FCA", "Free Carrier"), ("FOB", "Free On Board"),
    ]:
        add("Delivery Terms", code, desc)

    return pd.DataFrame(rows, columns=["attribute", "key", "description"])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    ref = root / "reference"

    dfs = []

    for fname, extractor in [
        ("Attribute Group.xlsx", extract_attribute_groups),
        ("Brands.xlsx", extract_brands),
        ("Buyer Group.xlsx", extract_buyer_groups),
        ("Commodity code.xlsx", extract_commodity_codes),
    ]:
        p = ref / fname
        if p.exists():
            df = extractor(str(p))
            print(f"Loaded {len(df):>6} rows from {fname}")
            dfs.append(df)
        else:
            print(f"Warning: {fname} not found at {p}")

    hardcoded = get_hardcoded_lovs()
    print(f"Loaded {len(hardcoded):>6} rows from hardcoded LOVs")
    dfs.append(hardcoded)

    if not dfs:
        raise SystemExit("No reference files found — nothing to write.")

    flat_df = pd.concat(dfs, ignore_index=True)
    output_path = ref / "lovs_flat.csv"
    flat_df.to_csv(output_path, index=False)
    print(f"\nWrote {len(flat_df)} total LOV rows to {output_path}")
    print(f"Attributes: {sorted(flat_df['attribute'].unique())}")
