#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Model Evaluation Inspector
"""

from pathlib import Path
import pandas as pd
import json

def main():
    root = Path(__file__).resolve().parent.parent
    export_dir = root / "data" / "processed" / "dashboard_exports"

    print("==================================================================")
    print("  NASA EARTH SYSTEMS TREND DETECTIVE — MODEL EVALUATION AUDIT")
    print("==================================================================")

    summary_df = pd.read_csv(export_dir / "fold_summary.csv")
    print("\n--- Chronological Fold Summary ---")
    print(summary_df.to_string(index=False))

    seeds_df = pd.read_csv(export_dir / "fold_seed_metrics.csv")
    print("\n--- Seed-Level Evaluations (5 Seeds & 3 Folds) ---")
    print(seeds_df.head(10).to_string(index=False))

    print("\nModel Status: EXPERIMENTAL REFERENCE — NOT PRODUCTION APPROVED")

if __name__ == "__main__":
    main()
