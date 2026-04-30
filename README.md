## Payments Converter

### Overview
This utility converts exported payment / credit-memo files into a normalized CSV suitable for downstream processing. It supports `.csv`, `.xls`, and `.xlsx` inputs and emits a new CSV without mutating the original file. A single input file may contain rows for multiple customers — all are processed.

The hosted Streamlit app is configured via Streamlit Community Cloud — see the **Releasing / deployment** section below.

### Input shape
The expected RAW format has 13 columns and a 4-line header block:

```
row 1: Textbox1, Textbox2 labels
row 2: report title + branch info
row 3: blank
row 4: column header
row 5+: data rows
```

Columns (positional, 0-indexed):

| Idx | Name | Description |
|---|---|---|
| 0 | CompanyName2 | Customer name |
| 1 | dm_amount | Payment amount |
| 2 | dm_number | Payment / debit memo number |
| 3 | InvDate4 | Invoice date |
| 4 | InvNumber4 | Invoice number |
| 5 | InvLocation | Location |
| 6 | InvOriginalAmount4 | Invoice original amount |
| 7 | BalanceDue4 | Balance due on the invoice |
| 8 | Textbox108 | Always blank — passes through |
| 9 | ApplyThisPaymentAmount4 | Amount of the payment applied to the invoice |
| 10 | AT_dm_applyto8 | Amount of a credit memo being applied (`0` if none) |
| 11 | CMNumber | Credit memo number (equals `dm_number` when no CM is applied) |
| 12 | Textbox15 | Same as `dm_amount` — passes through |

### Row classification
Every data row is one of two types, determined by `AT_dm_applyto8` (col 10):

- **Invoice row** — `AT_dm_applyto8 == 0`. A straight payment applied to an invoice. `CMNumber` equals `dm_number`.
- **Credit memo row** — `AT_dm_applyto8 > 0`. A credit memo is being applied against an invoice. `CMNumber` holds the credit memo number.

### Transformation rules

1. **Currency formatting** — strip `$` and `,` from every cell up front.
2. **Header / metadata rows (rows 1–3)** — pad with trailing commas so each is 13 columns wide. If already 13 columns, leave as-is. Row 4 (the column header) passes through unchanged.
3. **Invoice rows pass through unchanged** — any row where `AT_dm_applyto8 == 0` is written to the output exactly as it appeared in the input.
4. **Credit memo rows are transformed** — only two columns change:
   - `InvNumber4` ← `CMNumber` (the credit memo number)
   - `InvOriginalAmount4` ← `-(AT_dm_applyto8)` (the negative of the credit memo amount)

   All other columns carry through unchanged. _(Open question: `InvDate4` on CM rows should be the credit memo's own date, but the raw input does not include CM dates. The script currently leaves the invoice date in place as a placeholder and flags it with a `TODO`. Source of the CM date — lookup file? DB query? API? — must be confirmed with the stakeholder.)_
5. **Synthesize a missing invoice row** — when a `(CompanyName2, InvNumber4)` group consists entirely of credit memo rows (no invoice row), the script inserts a synthetic invoice row immediately before that group's CM rows. The synthetic row is built from one of the CM rows for that invoice, with these overrides:
   - `InvNumber4` — keep the original invoice number (do **not** replace with `CMNumber`)
   - `InvOriginalAmount4` — keep the original positive amount
   - `AT_dm_applyto8` — set to `0`
   - `CMNumber` — set to `dm_number`
   - `ApplyThisPaymentAmount4` — set to `BalanceDue4`
6. **Numeric normalization** — for amount-like columns (`dm_amount`, `InvOriginalAmount4`, `BalanceDue4`, `ApplyThisPaymentAmount4`, `AT_dm_applyto8`, `Textbox15`), trims trailing zeros / decimal points and collapses `-0` to `0`.
7. **Row ordering** — preserves the original row order, with the only exception being inserted synthetic rows (rule 5).

### Output
- Written to `<input_base>_Cleaned.csv` next to the input (or under `cleaned/` for directory inputs). On filename collision, appends a numeric suffix: `_Cleaned_1.csv`, `_Cleaned_2.csv`, …
- The 4-line preamble is preserved at the top of the output.

### Command-line usage
- Single file → output goes next to the input:
```bash
uv run python main.py /path/to/input.csv
```
- Directory → output goes to an auto-created `cleaned/` folder:
```bash
uv run python main.py /path/to/folder
```
- Explicit output directory:
```bash
uv run python main.py /path/to/input.csv -o /path/to/output
```
- Streamlit UI (local):
```bash
uv run streamlit run app.py
```

### Environment and installation
- Requires Python >= 3.10.
- Managed with `uv`. Dependencies are pinned in `pyproject.toml` / `uv.lock`.
```bash
uv sync
```

### Testing
- Golden-file test against a sample input/output pair. The fixture CSVs are not committed (they contain customer-shaped data); place `sample_raw.csv` and `sample_expected.csv` in `tests/fixtures/` to run the test, otherwise it will skip.
```bash
uv run -m pytest -q
```

### Releasing / deployment
The Streamlit app is hosted on **Streamlit Community Cloud** and auto-deploys from this GitHub repo (`RyanFerretti/vendor-payments-cleaner`). There is no separate build pipeline.

To ship a change:

1. Commit and push to `master`.
   ```bash
   git push origin master
   ```
2. Streamlit Cloud detects the push, reinstalls dependencies from `pyproject.toml`, and redeploys the app within ~1–2 minutes.
3. Verify the live app — a hard refresh may be needed to clear cached assets.

Manage / restart / view logs / change branch / set secrets at https://share.streamlit.io/ (sign in with the GitHub account that owns the repo).

If a deploy fails, check the Cloud logs first — the most common causes are dependency resolution errors (mismatch between `pyproject.toml` and the runtime's Python version) or missing imports in `app.py`.
