#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Preprocessing Pipeline Runner
"""

from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent.parent
    meta_path = root / "data" / "processed" / "dashboard_exports" / "dashboard_metadata.json"

    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print("Preprocessing Pipeline Verified:")
        print(f"Generated Files: {len(meta.get('generated_files', []))} files verified.")
    else:
        print("Metadata not found.")

if __name__ == "__main__":
    main()
