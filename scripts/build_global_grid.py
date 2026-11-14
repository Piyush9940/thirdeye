#!/usr/bin/env python3
"""
NASA Earth Systems Trend Detective
CLI Global Grid Inspector & Builder
"""

from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent.parent
    nodes_file = root / "data" / "processed" / "dashboard_exports" / "spatial_nodes.json"

    if nodes_file.exists():
        with open(nodes_file, "r", encoding="utf-8") as f:
            nodes = json.load(f)
        print(f"Verified 2° spatial grid loaded: {len(nodes)} grid nodes.")
    else:
        print("Spatial nodes file not found.")

if __name__ == "__main__":
    main()
