"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Geographic Service: Six-Region Partition & Spatial Lattice
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from ..config import SPHERICAL_NODES_PATH, INDIA_BOUNDARY_PATH, DASHBOARD_EXPORTS_DIR

class GeographicService:
    def __init__(self):
        self.nodes_df = None
        self.node_to_region = {}
        self.region_to_nodes = {}
        self.india_boundary_geojson = None
        self.spatial_nodes_geojson = None
        
        self.regions_metadata = [
            {"id": "All_India", "name": "All India", "criteria": "Full 255-node subcontinent lattice"},
            {"id": "North_West", "name": "Northwest", "criteria": "Lat ≥ 25.0°N, Lon < 82.0°E"},
            {"id": "North_East", "name": "Northeast", "criteria": "Lat ≥ 25.0°N, Lon ≥ 82.0°E"},
            {"id": "Central_West", "name": "Central-West", "criteria": "15.0°N ≤ Lat < 25.0°N, Lon < 82.0°E"},
            {"id": "Central_East", "name": "Central-East", "criteria": "15.0°N ≤ Lat < 25.0°N, Lon ≥ 82.0°E"},
            {"id": "South_West", "name": "Southwest", "criteria": "Lat < 15.0°N, Lon < 82.0°E"},
            {"id": "South_East", "name": "Southeast", "criteria": "Lat < 15.0°N, Lon ≥ 82.0°E (Pilot Data Gap)"}
        ]
        
        self._load_data()

    def _load_data(self):
        if SPHERICAL_NODES_PATH.exists():
            self.nodes_df = pd.read_csv(SPHERICAL_NODES_PATH)
            for _, row in self.nodes_df.iterrows():
                node_id = str(row["node_id"])
                lat = float(row["grid_latitude"])
                lon = float(row["grid_longitude"])
                reg = self.classify_region(lat, lon)
                
                self.node_to_region[node_id] = reg
                if reg not in self.region_to_nodes:
                    self.region_to_nodes[reg] = []
                self.region_to_nodes[reg].append(node_id)
        
        if INDIA_BOUNDARY_PATH.exists():
            with open(INDIA_BOUNDARY_PATH, "r", encoding="utf-8") as f:
                self.india_boundary_geojson = json.load(f)

        geo_nodes_path = DASHBOARD_EXPORTS_DIR / "spatial_nodes.geojson"
        if geo_nodes_path.exists():
            with open(geo_nodes_path, "r", encoding="utf-8") as f:
                self.spatial_nodes_geojson = json.load(f)

    @staticmethod
    def classify_region(lat: float, lon: float) -> str:
        """
        Six-zone partitioning according to reports/six_region_geometry_validation.json
        """
        if lat >= 25.0:
            return "North_West" if lon < 82.0 else "North_East"
        elif lat >= 15.0:
            return "Central_West" if lon < 82.0 else "Central_East"
        else:
            return "South_West" if lon < 82.0 else "South_East"

    def get_regions(self) -> List[Dict[str, Any]]:
        result = []
        for reg in self.regions_metadata:
            rid = reg["id"]
            if rid == "All_India":
                count = len(self.nodes_df) if self.nodes_df is not None else 255
            else:
                count = len(self.region_to_nodes.get(rid, []))
            result.append({
                **reg,
                "node_count": count
            })
        return result

    def get_nodes_in_region(self, region_id: str) -> List[str]:
        if region_id == "All_India" or not region_id:
            return list(self.node_to_region.keys())
        return self.region_to_nodes.get(region_id, [])

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        if self.nodes_df is None:
            return []
        nodes = []
        for _, row in self.nodes_df.iterrows():
            nid = str(row["node_id"])
            lat = float(row["grid_latitude"])
            lon = float(row["grid_longitude"])
            nodes.append({
                "node_id": nid,
                "latitude": lat,
                "longitude": lon,
                "region": self.node_to_region.get(nid, "Unknown"),
                "degree": int(row.get("degree", 8)),
                "connected_component": int(row.get("connected_component", 0))
            })
        return nodes

    def get_india_boundary_geojson(self) -> Optional[Dict[str, Any]]:
        return self.india_boundary_geojson

    def get_spatial_nodes_geojson(self) -> Optional[Dict[str, Any]]:
        return self.spatial_nodes_geojson

geo_service = GeographicService()
