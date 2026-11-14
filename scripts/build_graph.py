#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Spatial Graph Inspector
"""

from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent.parent
    geojson_file = root / "data" / "processed" / "dashboard_exports" / "spatial_nodes.geojson"

    if geojson_file.exists():
        with open(geojson_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        print(f"Spatial Graph GeoJSON contains {len(features)} node features.")
    else:
        print("Spatial nodes GeoJSON not found.")

if __name__ == "__main__":
    main()
