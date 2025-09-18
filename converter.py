import os
import re
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


def convert_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Remove currency formatting
    df = df.applymap(lambda x: str(x).replace('$', '').replace(',', '') if isinstance(x, str) else x)

    # Column references
    col_k = 'AT_dm_applyto8'
    col_e = 'InvNumber4'
    col_j = 'ApplyThisPaymentAmount4'
    col_l = 'CMNumber'

    # K as numeric
    k_numeric = pd.to_numeric(df[col_k], errors='coerce').fillna(0)

    # K != 0 logic
    mask_nonzero = k_numeric != 0
    neg_vals = -k_numeric[mask_nonzero].abs()
    df.loc[mask_nonzero, col_k] = neg_vals.apply(
        lambda v: str(int(v)) if float(v).is_integer() else str(v).rstrip('0').rstrip('.')
    )
    df.loc[mask_nonzero, col_e] = df.loc[mask_nonzero, col_l]
    df.loc[mask_nonzero, col_j] = "0"

    # K == 0 logic
    mask_zero = k_numeric == 0
    df.loc[mask_zero, col_k] = "0"

    # Normalize numeric-like columns
    amount_columns = [
        "dm_amount",
        "InvOriginalAmount4",
        "BalanceDue4",
        "ApplyThisPaymentAmount4",
        "AT_dm_applyto8",
        "Textbox15",
    ]
    for c in amount_columns:
        if c in df.columns:
            df[c] = df[c].map(normalize_numeric_string)

    return df


def convert_file_to_csv(input_path: str, output_dir: str) -> str:
    # Load, skipping first 3 rows, read as strings
    df = (
        pd.read_excel(input_path, skiprows=3, dtype=str)
        if input_path.endswith((".xls", ".xlsx"))
        else pd.read_csv(input_path, skiprows=3, dtype=str)
    )
    df = convert_dataframe(df)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_file = resolve_unique_csv_path(output_dir, base_name)
    df.to_csv(output_file, index=False)
    return output_file


