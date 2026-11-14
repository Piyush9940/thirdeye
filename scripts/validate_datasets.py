#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Dataset Validation Script
"""

from pathlib import Path
import json
import pandas as pd
import sys

def main():
    root = Path(__file__).resolve().parent.parent
    export_dir = root / "data" / "processed" / "dashboard_exports"

    print("==================================================================")
    print("  NASA EARTH SYSTEMS TREND DETECTIVE — DATASET VALIDATION AUDIT")
    print("==================================================================")
    print(f"Export Directory: {export_dir}")

    required_files = [
        "dashboard_metadata.json",
        "spatial_nodes.csv",
        "spatial_nodes.geojson",
        "methane_observations.csv",
        "mlp_predictions.csv",
        "fold_seed_metrics.csv",
        "fold_summary.csv"
    ]

    all_present = True
    for f in required_files:
        p = export_dir / f
        if p.exists() and p.stat().st_size > 0:
            print(f"  [PASS] {f} ({p.stat().st_size:,} bytes)")
        else:
            print(f"  [FAIL] {f} (Missing or empty)")
            all_present = False

    if not all_present:
        print("\nERROR: Required export files are missing or incomplete.")
        sys.exit(1)

    # Validate row dimensions
    nodes_df = pd.read_csv(export_dir / "spatial_nodes.csv")
    obs_df = pd.read_csv(export_dir / "methane_observations.csv")
    preds_df = pd.read_csv(export_dir / "mlp_predictions.csv")

    print("\n--- Verified Dataset Dimensions ---")
    print(f"Spatial Grid Nodes:        {len(nodes_df)} (Target: 255)")
    print(f"Methane Observations:      {len(obs_df)} (Target: 226)")
    print(f"MLP Evaluation Rows:       {len(preds_df)} (Target: 720)")

    assert len(nodes_df) == 255, "Nodes count mismatch"
    assert len(obs_df) == 226, "Observations count mismatch"
    assert len(preds_df) == 720, "Predictions count mismatch"

    print("\nALL DATASET AUDITS PASSED WITH 100% INTEGRITY.")

if __name__ == "__main__":
    main()
