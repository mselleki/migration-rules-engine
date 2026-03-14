"""Streamlit UI for the Sysco Migration Rules Engine."""

import sys
import os
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from validator import validate, ValidationReport  # noqa: E402
from utils.lov_extractor import extract_lovs_from_excel

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Sysco Migration Rules Engine",
    page_icon="🔍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_summary(report: ValidationReport) -> None:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total rows validated", report.total_rows)
    col2.metric("Global Product Data rows", report.global_row_count)
    col3.metric("Local Product Data rows", report.local_row_count)

    if report.total_errors == 0:
        col4.metric("Validation errors", "✅ 0", delta="All rules passed", delta_color="off")
    else:
        col4.metric("Validation errors", f"❌ {report.total_errors}")

    if report.total_errors > 0:
        st.markdown("#### Errors per rule")
        rule_data = [
            {"Rule": rule, "Errors": count}
            for rule, count in sorted(report.errors_by_rule.items(), key=lambda x: -x[1])
        ]
        st.dataframe(pd.DataFrame(rule_data), use_container_width=True, hide_index=True)


def _render_warnings(warnings: list[str]) -> None:
    if not warnings:
        return
    st.markdown("#### Structural warnings")
    for w in warnings:
        st.warning(w)


def _render_errors_table(report: ValidationReport) -> None:
    df = report.errors_df
    if df.empty:
        st.success("No validation errors found.")
        return

    col_rule, col_sheet = st.columns(2)
    with col_rule:
        rule_options = ["All rules"] + sorted(df["rule"].unique().tolist())
        selected_rule = st.selectbox("Filter by rule", rule_options)
    with col_sheet:
        sheet_options = ["All sheets"] + sorted(df["sheet"].unique().tolist())
        selected_sheet = st.selectbox("Filter by sheet", sheet_options)

    filtered = df.copy()
    if selected_rule != "All rules":
        filtered = filtered[filtered["rule"] == selected_rule]
    if selected_sheet != "All sheets":
        filtered = filtered[filtered["sheet"] == selected_sheet]

    st.caption(f"Showing **{len(filtered)}** of **{len(df)}** errors")

    st.dataframe(
        filtered.rename(columns={
            "sheet": "Sheet",
            "row": "Excel Row",
            "supc": "SUPC",
            "rule": "Rule",
            "message": "Message",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Excel Row": st.column_config.NumberColumn(format="%d"),
        },
    )


def _render_validation_tab() -> None:
    st.markdown(
        "Upload the two migration files and click **Run Validation** to validate "
        "them against all business rules."
    )

    st.divider()

    col_global, col_local = st.columns(2)
    with col_global:
        global_file = st.file_uploader(
            "Global Product Data (.xlsx)",
            type=["xlsx"],
            key="global_file",
        )
    with col_local:
        local_file = st.file_uploader(
            "Local Product Data (.xlsx)",
            type=["xlsx"],
            key="local_file",
        )

    nothing_uploaded = global_file is None and local_file is None
    run_btn = st.button(
        "Run Validation",
        type="primary",
        disabled=nothing_uploaded,
    )

    if nothing_uploaded:
        st.info("Upload at least one file above to get started.")
        return

    if not run_btn:
        st.info("Click **Run Validation** to start.")
        return

    # --- Run validation ---
    with st.spinner("Validating…"):
        try:
            report = validate(
                global_file_bytes=global_file.read() if global_file else None,
                local_file_bytes=local_file.read() if local_file else None,
            )
        except Exception as exc:
            st.error(f"An unexpected error occurred while processing the file(s): {exc}")
            return

    st.divider()

    if report.warnings:
        _render_warnings(report.warnings)
        st.divider()

    st.markdown("## Validation Summary")
    _render_summary(report)

    st.divider()

    st.markdown("## Detailed Results")
    _render_errors_table(report)

    if report.total_errors > 0:
        st.divider()
        csv_bytes = report.errors_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download error report (CSV)",
            data=csv_bytes,
            file_name="validation_errors.csv",
            mime="text/csv",
        )


def _render_lov_explorer_tab() -> None:
    st.markdown("Browse and inspect all LOVs.")
    st.caption(
        "By default the app will load the flattened LOVs from `input/lovs_flat.csv` "
        "if available, or derive them from `LOVs.xlsx` in the project root. "
        "You can also upload a different LOV workbook below."
    )

    uploaded_lov_file = st.file_uploader(
        "Optional: upload a LOVs workbook (.xlsx)",
        type=["xlsx"],
        key="lovs_file",
    )

    df_flat: pd.DataFrame | None = None
    source_label = ""

    try:
        if uploaded_lov_file is not None:
            # For uploaded workbooks, derive LOVs on the fly using the same extractor logic.
            # We read to a temporary file-like DataFrame and reuse the extractor on disk file
            # by writing a temporary file would be overkill here, so we keep the simple view:
            raw_df = pd.read_excel(uploaded_lov_file, engine="openpyxl", header=None)
            if raw_df.empty:
                st.warning("The uploaded LOV workbook appears to be empty.")
                return
            # Minimal flattening: treat first two non-null columns as description/key pairs.
            # For richer behaviour, the user should regenerate `lovs_flat.csv` server-side.
            st.warning(
                "Uploaded workbook support is limited to the raw view for now. "
                "Regenerate `lovs_flat.csv` from `LOVs.xlsx` for a fully flattened view."
            )
            st.dataframe(raw_df, use_container_width=True)
            return

        # No upload: prefer the pre-flattened CSV if it exists
        project_root = Path(__file__).resolve().parent
        flat_path = project_root / "input" / "lovs_flat.csv"
        if flat_path.exists():
            df_flat = pd.read_csv(flat_path)
            source_label = f"`{flat_path}`"
        else:
            # Fallback: derive from LOVs.xlsx on the fly
            lovs_path = project_root / "LOVs.xlsx"

            if not lovs_path.exists():
                st.info(
                    "No `input/lovs_flat.csv` or `LOVs.xlsx` found. "
                    "Upload a workbook above or generate LOVs using `utils.lov_extractor`."
                )
                return

            df_flat = extract_lovs_from_excel(str(lovs_path))
            source_label = "`LOVs.xlsx` in project root"
    except Exception as exc:
        st.error(f"Failed to load LOVs: {exc}")
        return

    if df_flat is None or df_flat.empty:
        st.warning("No LOV rows were found.")
        return

    st.success(
        f"Loaded flattened LOVs from {source_label} — {len(df_flat)} rows, "
        f"{len(df_flat.columns)} columns."
    )

    lov_df = df_flat.copy()

    # High-level selector: attribute name
    attributes = sorted({str(v).strip() for v in lov_df["attribute"].dropna().unique()})
    selected_attr = st.selectbox(
        "Filter by attribute", options=["All attributes"] + attributes
    )
    if selected_attr != "All attributes":
        lov_df = lov_df[lov_df["attribute"].astype(str).str.strip() == selected_attr]

    # Text filter over key / description
    text_filter = st.text_input(
        "Optional text filter (matches in `key` or `description`)"
    ).strip()
    if text_filter:
        mask = (
            lov_df["key"].astype(str).str.contains(text_filter, case=False, na=False)
            | lov_df["description"]
            .astype(str)
            .str.contains(text_filter, case=False, na=False)
        )
        lov_df = lov_df[mask]

    st.markdown("### LOVs table")
    st.dataframe(lov_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.title("Sysco Migration Rules Engine")
    tabs = st.tabs(["Validation", "LOV Explorer"])

    with tabs[0]:
        _render_validation_tab()

    with tabs[1]:
        _render_lov_explorer_tab()


if __name__ == "__main__":
    main()
