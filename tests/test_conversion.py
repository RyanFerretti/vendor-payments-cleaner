import csv
import os
import tempfile
from pathlib import Path

import pytest

from main import clean_file


FIXTURES = Path(__file__).resolve().parent / "fixtures"
RAW = FIXTURES / "sample_raw.csv"
EXPECTED = FIXTURES / "sample_expected.csv"


def _read_rows(path: Path) -> list[list[str]]:
    with path.open("r", newline="") as f:
        return list(csv.reader(f))


@pytest.mark.skipif(
    not (RAW.exists() and EXPECTED.exists()),
    reason="Fixture CSVs are not committed (contain customer-shaped data); place sample_raw.csv and sample_expected.csv in tests/fixtures/ to run.",
)
def test_conversion_matches_expected():
    with tempfile.TemporaryDirectory() as tmpdir:
        clean_file(str(RAW), tmpdir)

        produced = None
        for name in os.listdir(tmpdir):
            if name.startswith("sample_raw_Cleaned") and name.endswith(".csv"):
                produced = Path(tmpdir) / name
                break
        assert produced, "No cleaned file produced"

        expected_rows = _read_rows(EXPECTED)
        produced_rows = _read_rows(produced)

        assert len(expected_rows) == len(produced_rows), (
            f"row count mismatch: expected {len(expected_rows)}, got {len(produced_rows)}"
        )
        for i, (exp, act) in enumerate(zip(expected_rows, produced_rows)):
            assert exp == act, (
                f"row {i + 1} mismatch:\n  expected: {exp}\n  got:      {act}"
            )
