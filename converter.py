import os
import re
from io import StringIO
from typing import List

import pandas as pd


def resolve_unique_csv_path(directory: str, base_name: str) -> str:
    candidate = os.path.join(directory, f"{base_name}_Cleaned.csv")
    if not os.path.exists(candidate):
        return candidate
    counter = 1
    while True:
        candidate = os.path.join(directory, f"{base_name}_Cleaned_{counter}.csv")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def normalize_numeric_string(val: str) -> str:
    if val is None:
        return val
    s = str(val)
    if s == "":
        return s
    num_re = re.compile(r"^-?\d+(?:\.\d+)?$")
    if not num_re.match(s):
        return s
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", "+0"):
        s = "0"
    return s


def _pad_preamble_row(line: str) -> str:
    """Pad rows 1-3 of the preamble with trailing commas so they have 13 columns."""
    stripped = line.rstrip("\r\n")
    eol = line[len(stripped):] or "\n"
    n_commas = stripped.count(",")
    if n_commas < 12:
        stripped += "," * (12 - n_commas)
    return stripped + eol


def convert_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Strip currency symbols and thousands separators from every cell.
    df = df.map(lambda x: str(x).replace('$', '').replace(',', '') if isinstance(x, str) else x)

    col_company = 'CompanyName2'
    col_dm_number = 'dm_number'
    col_inv_date = 'InvDate4'  # noqa: F841 — referenced by the TODO below
    col_inv_number = 'InvNumber4'
    col_inv_orig = 'InvOriginalAmount4'
    col_balance_due = 'BalanceDue4'
    col_apply_amt = 'ApplyThisPaymentAmount4'
    col_at = 'AT_dm_applyto8'
    col_cm_number = 'CMNumber'

    k_numeric = pd.to_numeric(df[col_at], errors='coerce').fillna(0)

    # Pre-pass: identify (customer, invoice) groups that have NO invoice row
    # (i.e., every row in the group is a credit memo). Those need a synthetic
    # invoice row inserted.
    has_invoice_row = (
        df.assign(_is_inv=(k_numeric == 0))
        .groupby([col_company, col_inv_number])['_is_inv']
        .any()
    )

    output_rows: List[pd.Series] = []
    synthesized: set = set()

    for i, row in df.iterrows():
        k = k_numeric.iloc[i]
        if k == 0:
            # Invoice row — pass through unchanged.
            output_rows.append(row.copy())
            continue

        # Credit memo row.
        group_key = (row[col_company], row[col_inv_number])
        if not has_invoice_row.get(group_key, False) and group_key not in synthesized:
            # Synthesize the missing invoice row, derived from this CM row.
            # Keep InvNumber4 and InvOriginalAmount4 from the source CM row;
            # override AT_dm_applyto8, CMNumber, and ApplyThisPaymentAmount4.
            synth = row.copy()
            synth[col_at] = '0'
            synth[col_cm_number] = row[col_dm_number]
            synth[col_apply_amt] = row[col_balance_due]
            output_rows.append(synth)
            synthesized.add(group_key)

        # Transform the CM row.
        new_row = row.copy()
        new_row[col_inv_number] = row[col_cm_number]
        at_val = row[col_at]
        new_row[col_inv_orig] = f"-{at_val}" if at_val and at_val != '0' else at_val
        # TODO: InvDate4 on credit memo rows should be the credit memo's own
        # date, not the invoice date. The raw input does not include CM dates;
        # the source (lookup file / DB query / API) needs to be confirmed with
        # the stakeholder. Until then, the invoice date is left in place as a
        # placeholder.
        output_rows.append(new_row)

    result = pd.DataFrame(output_rows, columns=df.columns).reset_index(drop=True)

    amount_columns = [
        "dm_amount",
        "InvOriginalAmount4",
        "BalanceDue4",
        "ApplyThisPaymentAmount4",
        "AT_dm_applyto8",
        "Textbox15",
    ]
    for c in amount_columns:
        if c in result.columns:
            result[c] = result[c].map(normalize_numeric_string)

    return result


def convert_csv_text(input_text: str) -> str:
    """Transform CSV text → CSV text, preserving the 3 preamble rows + header."""
    lines = input_text.splitlines(keepends=True)
    if len(lines) < 4:
        # Shouldn't happen for real input, but fall through to a data-only path.
        df = pd.read_csv(StringIO(input_text), skiprows=3, dtype=str)
        df = convert_dataframe(df)
        out = StringIO()
        df.to_csv(out, index=False)
        return out.getvalue()

    preamble = [_pad_preamble_row(l) for l in lines[:3]] + [lines[3]]
    df = pd.read_csv(StringIO(input_text), skiprows=3, dtype=str)
    df = convert_dataframe(df)

    out = StringIO()
    for line in preamble:
        out.write(line)
    df.to_csv(out, index=False, header=False)
    return out.getvalue()


def convert_file_to_csv(input_path: str, output_dir: str) -> str:
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_file = resolve_unique_csv_path(output_dir, base_name)

    if input_path.endswith((".xls", ".xlsx")):
        # Excel inputs don't carry a literal preamble in the same way; fall
        # back to data-only conversion.
        df = pd.read_excel(input_path, skiprows=3, dtype=str)
        df = convert_dataframe(df)
        df.to_csv(output_file, index=False)
    else:
        with open(input_path, "r", newline="", encoding="utf-8") as f:
            text = f.read()
        cleaned_text = convert_csv_text(text)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            f.write(cleaned_text)

    return output_file
