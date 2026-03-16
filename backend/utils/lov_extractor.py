"""Helpers to extract side-by-side LOV tables from an Excel workbook."""

from __future__ import annotations

from typing import Optional

import pandas as pd


def extract_attribute_groups(path: str) -> pd.DataFrame:
    """
    Parse the Attribute Group.xlsx reference file.

    Structure (0-indexed):
      Row 0 : title
      Row 1 : headers — Business Centre | Item Group | Attribute Group | STIBO ID
      Row 2+: data

    Output schema:
      attribute="Attribute Group ID" | key=STIBO ID (8-char zero-padded) | description="Business Centre > Item Group > Attribute Group"
    """
    df = pd.read_excel(path, sheet_name="Attributes Group", header=None)
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


def extract_lovs_from_excel(
    path: str,
    sheet_name: Optional[str | int] = 0,
    start_row_title: int = 0,
    header_row: int = 2,
    first_data_row: int = 3,
) -> pd.DataFrame:
    """
    Parse an Excel sheet where multiple LOV tables are laid out side by side.

    For each LOV block (at least 2 columns) it expects:
      - Row start_row_title : LOV title (optional)
      - Row header_row      : column headers
      - Rows >= first_data_row : data values until a blank row

    Output schema:
      attribute | key | description

    Assumptions:
      - Each LOV is two columns wide: [description_col, key_col]
      - LOV blocks are arranged horizontally: (col, col+1), (col+2, col+3), ...
    """
    # Raw read without headers to keep all rows as-is
    df = pd.read_excel(path, sheet_name=sheet_name, header=None)

    records: list[dict] = []
    n_rows, n_cols = df.shape
    col = 0

    while col < n_cols - 1:
        title_cell = df.iat[start_row_title, col]
        desc_header = df.iat[header_row, col]
        code_header = df.iat[header_row, col + 1]

        if pd.isna(desc_header) or pd.isna(code_header):
            col += 1
            continue

        desc_header_str = str(desc_header).strip()
        title_str = "" if pd.isna(title_cell) else str(title_cell).strip()

        # Attribute name: prefer the textual header, fall back to the LOV title
        if desc_header_str and desc_header_str.lower() not in {"value", "description"}:
            attribute_name = desc_header_str
        else:
            attribute_name = title_str or desc_header_str

        row = first_data_row
        while row < n_rows:
            desc_val = df.iat[row, col]
            code_val = df.iat[row, col + 1]

            if pd.isna(desc_val) and pd.isna(code_val):
                break

            if not pd.isna(code_val):
                records.append(
                    {
                        "attribute": attribute_name,
                        "key": str(code_val).strip(),
                        "description": None
                        if pd.isna(desc_val)
                        else str(desc_val).strip(),
                    }
                )

            row += 1

        col += 2

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


def extract_brands(path: str) -> pd.DataFrame:
    """
    Parse Brands.xlsx — one sheet, two side-by-side tables:
      Col 0-1 : Sysco (Own) Brand Code | Sysco (Own) Brand  → attribute="Sysco Brand Code"
      Col 3-4 : Vendor Brand Code      | Vendor Brand       → attribute="Vendor Brand Code"

    Row 0 : title, Row 1 : headers, Row 2+ : data.
    """
    df = pd.read_excel(path, sheet_name=0, header=None)

    records = []

    # Sysco brands (cols 0, 1)
    for _, row in df.iloc[2:].iterrows():
        code = row.iloc[0]
        name = row.iloc[1]
        if pd.isna(code) or str(code).strip() == "":
            continue
        records.append({
            "attribute": "Sysco Brand Code",
            "key": str(code).strip(),
            "description": "" if pd.isna(name) else str(name).strip(),
        })

    # Vendor brands (cols 3, 4)
    for _, row in df.iloc[2:].iterrows():
        code = row.iloc[3]
        name = row.iloc[4]
        if pd.isna(code) or str(code).strip() == "":
            continue
        records.append({
            "attribute": "Vendor Brand Code",
            "key": str(code).strip(),
            "description": "" if pd.isna(name) else str(name).strip(),
        })

    return pd.DataFrame(records, columns=["attribute", "key", "description"])


if __name__ == "__main__":
    # Example usage for manual runs:
    #   python -m utils.lov_extractor
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    ref = root / "reference"

    dfs = []

    lovs_path = ref / "LOVs.xlsx"
    if lovs_path.exists():
        dfs.append(extract_lovs_from_excel(str(lovs_path)))
        print(f"Loaded {len(dfs[-1])} rows from LOVs.xlsx")
    else:
        print(f"Warning: LOVs.xlsx not found at {lovs_path}")

    attr_path = ref / "Attribute Group.xlsx"
    if attr_path.exists():
        dfs.append(extract_attribute_groups(str(attr_path)))
        print(f"Loaded {len(dfs[-1])} rows from Attribute Group.xlsx")
    else:
        print(f"Warning: Attribute Group.xlsx not found at {attr_path}")

    brands_path = ref / "Brands.xlsx"
    if brands_path.exists():
        dfs.append(extract_brands(str(brands_path)))
        print(f"Loaded {len(dfs[-1])} rows from Brands.xlsx")
    else:
        print(f"Warning: Brands.xlsx not found at {brands_path}")

    if not dfs:
        raise SystemExit("No reference files found — nothing to write.")

    flat_df = pd.concat(dfs, ignore_index=True)
    output_path = ref / "lovs_flat.csv"
    flat_df.to_csv(output_path, index=False)
    print(f"Wrote {len(flat_df)} total LOV rows to {output_path}")

