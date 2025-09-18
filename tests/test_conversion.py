import os
import tempfile
import pandas as pd
from main import clean_file


def test_conversion_matches_expected():
    base_dir = "/Users/ryanferretti/Sandbox"
    input_path = os.path.join(base_dir, "original-file.csv")
    expected_path = os.path.join(base_dir, "correct-output-file.csv")

    with tempfile.TemporaryDirectory() as tmpdir:
        clean_file(input_path, tmpdir)

        # find the produced file (pattern: original-file_Cleaned*.csv)
        produced = None
        for name in os.listdir(tmpdir):
            if name.startswith("original-file_Cleaned") and name.endswith(".csv"):
                produced = os.path.join(tmpdir, name)
                break
        assert produced, "No cleaned file produced"

        exp = pd.read_csv(expected_path, dtype=str)
        act = pd.read_csv(produced, dtype=str)

        assert exp.shape == act.shape, f"shape mismatch: expected {exp.shape}, got {act.shape}"
        pd.testing.assert_frame_equal(exp, act, check_dtype=False)


