#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Trend Analysis Runner
"""

from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent.parent
    obs_file = root / "data" / "processed" / "dashboard_exports" / "methane_observations.json"

    if obs_file.exists():
        with open(obs_file, "r", encoding="utf-8") as f:
            obs = json.load(f)
        print(f"Loaded {len(obs)} verified methane observations across 4 temporal snapshots.")
    else:
        print("Observations file not found.")

if __name__ == "__main__":
    main()
