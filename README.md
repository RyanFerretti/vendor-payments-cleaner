## Payments Converter

### Overview
This utility converts exported payment information files into a clean, normalized CSV suitable for downstream processing. It supports `.csv`, `.xls`, and `.xlsx` inputs and emits a new CSV without mutating the original file.

### What the script does
- **Strip currency formatting**: Removes dollar signs and thousands separators from all cell values across the file.
- **Discard top boilerplate rows**: Skips the first 3 rows (commonly export headers/notes) before processing.
- **Primary column logic**:
  - **Column K (`AT_dm_applyto8`)**:
    - Coerces to numeric for evaluation.
    - If non-zero: writes a negative value (as a minimal string, e.g., `-5` not `-5.00`).
    - If zero: stays as `0`.
  - **Column E (`InvNumber4`)**: If Column K is non-zero, replaces value with Column L (`CMNumber`).
  - **Column J (`ApplyThisPaymentAmount4`)**: If Column K is non-zero, sets to `0`.
- **Numeric normalization**: For known amount-like columns, trims trailing zeros and decimal points so integer-valued amounts render without `.00`. Ensures `-0` becomes `0`.
- **Non-destructive output**: Writes to a new file named `<input_base>_Cleaned.csv`. If that filename already exists, appends a numeric suffix: `_Cleaned_1.csv`, `_Cleaned_2.csv`, etc.

### Command-line usage
- Run on a single file and write output to the same directory:
```bash
uv run python main.py /path/to/input.csv
```
- Run on a directory of files and write outputs into an auto-created `cleaned/` folder under that directory:
```bash
uv run python main.py /path/to/folder
```
- Specify an explicit output directory:
```bash
uv run python main.py /path/to/input.csv -o /path/to/output
```

### Environment and installation
- Requires Python >= 3.10.
- Uses `uv` for environment and dependency management.
  - Project dependencies are defined in `pyproject.toml` (`pandas`, `openpyxl`, `xlrd`).
  - Install once per project directory:
```bash
uv sync
```

### Testing
- A pytest verifies the produced CSV matches the expected transformation:
```bash
uv run -m pytest -q
```

### Notes
- The script reads values as strings to keep formatting predictable, then applies targeted numeric normalization only where needed.
- If run against Excel files, `openpyxl` (for `.xlsx`) and `xlrd` (for legacy `.xls`) are used under the hood. CSVs are handled natively.
- Failures are reported per file; successful runs log the input and the generated output path.


