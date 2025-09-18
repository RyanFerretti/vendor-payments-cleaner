import os
import argparse
from converter import convert_file_to_csv
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
 
def resolve_unique_csv_path(directory: str, base_name: str) -> str:
    """Return a unique CSV path in directory using pattern <base>_Cleaned.csv, adding a numeric suffix if needed."""
    candidate = os.path.join(directory, f"{base_name}_Cleaned.csv")
    if not os.path.exists(candidate):
        return candidate
    counter = 1
    while True:
        candidate = os.path.join(directory, f"{base_name}_Cleaned_{counter}.csv")
        if not os.path.exists(candidate):
            return candidate
        counter += 1

def clean_file(file_path, output_folder):
    try:
        output_file = convert_file_to_csv(file_path, output_folder)
        print(f"✔ Processed: {file_path} → {output_file}")
    except Exception as e:
        print(f"❌ Failed to process {file_path}: {e}")
 
def process_all_files(input_folder, output_folder):
    for file in os.listdir(input_folder):
        if file.endswith(('.xls', '.xlsx', '.csv')):
            clean_file(os.path.join(input_folder, file), output_folder)
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean payment files by removing currency formatting and applying column rules.")
    parser.add_argument("path", nargs="?", default=os.path.join(SCRIPT_DIR, "input"), help="Path to a file or directory of files (.csv/.xls/.xlsx). Defaults to ./input next to the script.")
    parser.add_argument("-o", "--output", default=None, help="Output directory. If not set: for a directory input, uses <input>/cleaned; for a single file, uses the file's directory.")

    args = parser.parse_args()

    input_path = os.path.abspath(args.path)

    if os.path.isdir(input_path):
        output_dir = os.path.abspath(args.output) if args.output else os.path.join(input_path, "cleaned")
        os.makedirs(output_dir, exist_ok=True)
        process_all_files(input_path, output_dir)
        print("✅ All files processed. Cleaned files are in:", output_dir)
    elif os.path.isfile(input_path):
        output_dir = os.path.abspath(args.output) if args.output else os.path.dirname(input_path)
        os.makedirs(output_dir, exist_ok=True)
        clean_file(input_path, output_dir)
        print("✅ File processed. Cleaned file is in:", output_dir)
    else:
        raise SystemExit(f"Input path not found: {input_path}")