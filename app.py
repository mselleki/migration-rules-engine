"""Streamlit UI for the Sysco Migration Rules Engine."""

import sys
import os

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from validator import validate, ValidationReport  # noqa: E402

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


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("Sysco Migration Rules Engine")
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


if __name__ == "__main__":
    main()
