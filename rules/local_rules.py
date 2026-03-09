"""Validation rules for the Local Product Data sheet.

Add new rule functions here following the same pattern as global_rules.py:
  - Accept a pandas DataFrame as the only argument.
  - Return a list of result dicts produced by utils.helpers.make_result().
  - Register each new rule in ALL_LOCAL_RULES at the bottom of this file.
"""

import pandas as pd
from utils.helpers import make_result, get_supc, excel_row  # noqa: F401

SHEET = "Local Product Data"


# ---------------------------------------------------------------------------
# Placeholder — no local rules are defined yet.
# Add rules below this comment and register them in ALL_LOCAL_RULES.
# ---------------------------------------------------------------------------

# Example skeleton:
#
# def rule_example(df: pd.DataFrame) -> list[dict]:
#     rule_name = "Rule L1 — Example local rule"
#     results = []
#     for idx, row in df.iterrows():
#         if <condition>:
#             results.append(
#                 make_result(
#                     sheet=SHEET,
#                     row=excel_row(idx),
#                     supc=get_supc(row),
#                     rule=rule_name,
#                     message=f"Row {excel_row(idx)} — ...",
#                 )
#             )
#     return results


# ---------------------------------------------------------------------------
# Registry — all local rules in execution order
# ---------------------------------------------------------------------------

ALL_LOCAL_RULES: list = []
