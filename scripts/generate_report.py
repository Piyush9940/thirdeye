#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Research Report Generator
"""

from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent.parent
    export_dir = root / "data" / "processed" / "dashboard_exports"

    with open(export_dir / "dashboard_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    print("==================================================================")
    print("  NASA EARTH SYSTEMS TREND DETECTIVE — RESEARCH SUMMARY DOSSIER")
    print("==================================================================")
    print(f"Project:       {meta.get('project')}")
    print(f"Model Name:    {meta.get('model_name')}")
    print(f"Model Status:  {meta.get('model_status')}")
    print(f"Target:        {meta.get('target', {}).get('name')} ({meta.get('target', {}).get('unit')})")
    print("\n--- Scientific Warnings & Limitations ---")
    for w in meta.get("scientific_warnings", []):
        print(f"  • {w}")

if __name__ == "__main__":
    main()
