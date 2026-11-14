"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Data Service: Parquet Loader & Time-Series Extraction Engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from ..config import NASA_POWER_GRID_PATH, METHANE_PILOT_PATH, DASHBOARD_EXPORTS_DIR
from .geographic_service import geo_service

class DataService:
    def __init__(self):
        self.climate_df: Optional[pd.DataFrame] = None
        self.methane_df: Optional[pd.DataFrame] = None
        self.variables_catalog = {
            "T2M": {
                "id": "T2M",
                "name": "Temperature at 2 Metres",
                "unit": "°C",
                "description": "Monthly average air temperature at 2 metres above the surface from NASA POWER.",
                "source": "NASA POWER Surface Meteorology (GMAO MERRA-2 assimilation)",
                "temporal_coverage": "2015-01 to 2024-12 (10 Years continuous, 120 months)",
                "spatial_coverage": "India regular 2° spherical lattice (255 nodes)",
                "observation_count": 30600,
                "annual_unit": "°C / year"
            },
            "PRECTOTCORR": {
                "id": "PRECTOTCORR",
                "name": "Corrected Precipitation",
                "unit": "mm/day",
                "description": "Mean daily precipitation rate corrected for bias from NASA POWER.",
                "source": "NASA POWER Surface Meteorology",
                "temporal_coverage": "2015-01 to 2024-12 (10 Years continuous, 120 months)",
                "spatial_coverage": "India regular 2° spherical lattice (255 nodes)",
                "observation_count": 30600,
                "annual_unit": "(mm/day) / year"
            },
            "RH2M": {
                "id": "RH2M",
                "name": "Relative Humidity at 2 Metres",
                "unit": "%",
                "description": "Ratio of actual water vapor pressure to saturation vapor pressure at 2 metres.",
                "source": "NASA POWER Surface Meteorology",
                "temporal_coverage": "2015-01 to 2024-12 (10 Years continuous, 120 months)",
                "spatial_coverage": "India regular 2° spherical lattice (255 nodes)",
                "observation_count": 30600,
                "annual_unit": "% / year"
            },
            "WS10M": {
                "id": "WS10M",
                "name": "Wind Speed at 10 Metres",
                "unit": "m/s",
                "description": "Horizontal wind speed at 10 metres above displacement height.",
                "source": "NASA POWER Surface Meteorology",
                "temporal_coverage": "2015-01 to 2024-12 (10 Years continuous, 120 months)",
                "spatial_coverage": "India regular 2° spherical lattice (255 nodes)",
                "observation_count": 30600,
                "annual_unit": "(m/s) / year"
            },
            "CH4": {
                "id": "CH4",
                "name": "Atmospheric Column Methane (XCH₄)",
                "unit": "ppb",
                "description": "Total column-averaged dry air mole fraction of atmospheric methane from Copernicus Sentinel-5P TROPOMI.",
                "source": "Copernicus Sentinel-5P TROPOMI Level-3 (QA ≥ 0.50)",
                "temporal_coverage": "4 Discrete Pilot Snapshots: May 2019, Feb 2021, Aug 2021, Nov 2023",
                "spatial_coverage": "98 Observed Grid Nodes across India (157 unobserved / cloud-filtered)",
                "observation_count": 226,
                "annual_unit": "ppb"
            }
        }
        self._load_datasets()

    def _load_datasets(self):
        if NASA_POWER_GRID_PATH.exists():
            print(f"[DataService] Loading NASA POWER Climate Grid from {NASA_POWER_GRID_PATH}...")
            self.climate_df = pd.read_parquet(NASA_POWER_GRID_PATH)
            # Ensure time column is datetime
            self.climate_df["time"] = pd.to_datetime(self.climate_df["time"])
            self.climate_df["year"] = self.climate_df["time"].dt.year
            self.climate_df["month"] = self.climate_df["time"].dt.month
            self.climate_df["date_str"] = self.climate_df["time"].dt.strftime("%Y-%m-%d")
            
            # Augment region column
            self.climate_df["region"] = self.climate_df["node_id"].map(geo_service.node_to_region)
            print(f"[DataService] Climate Grid loaded: {len(self.climate_df)} rows, 255 nodes, 120 months.")

        if METHANE_PILOT_PATH.exists():
            print(f"[DataService] Loading Methane Pilot from {METHANE_PILOT_PATH}...")
            self.methane_df = pd.read_parquet(METHANE_PILOT_PATH)
            self.methane_df["region"] = self.methane_df["node_id"].map(geo_service.node_to_region)
            print(f"[DataService] Methane Pilot loaded: {len(self.methane_df)} records.")

    def get_variables(self) -> List[Dict[str, Any]]:
        return list(self.variables_catalog.values())

    def get_variable_info(self, var_id: str) -> Optional[Dict[str, Any]]:
        return self.variables_catalog.get(var_id.upper())

    def extract_time_series(
        self,
        variable: str,
        region: str = "All_India",
        node_id: Optional[str] = None,
        start_date: str = "2015-01-01",
        end_date: str = "2024-12-01",
        aggregation: str = "monthly",
        remove_seasonality: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extracts observations and aggregates by month or year for selected region/node.
        Returns: (time_series_points, metadata)
        """
        var_upper = variable.upper()
        if var_upper not in self.variables_catalog:
            raise ValueError(f"Unsupported variable '{variable}'. Supported: {list(self.variables_catalog.keys())}")

        if var_upper == "CH4":
            return self._extract_methane_series(region, node_id)

        if self.climate_df is None:
            raise RuntimeError("Climate dataset not loaded.")

        df = self.climate_df

        # Filter by Node or Region
        if node_id:
            df = df[df["node_id"] == node_id]
        elif region and region != "All_India":
            df = df[df["region"] == region]

        # Filter by Date
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df["time"] >= start_dt) & (df["time"] <= end_dt)]

        if df.empty:
            return [], {"sample_size": 0, "missing_count": 0}

        # Spatial Aggregation across selected nodes
        # Area weighting using cos(latitude)
        df = df.copy()
        df["weight"] = np.cos(np.radians(df["grid_latitude"]))
        df["weighted_val"] = df[var_upper] * df["weight"]

        if aggregation == "annual":
            grouped = df.groupby(["year"]).apply(
                lambda g: g["weighted_val"].sum() / g["weight"].sum()
            ).reset_index(name="value")
            grouped["date"] = grouped["year"].astype(str) + "-01-01"
        else:
            # Monthly aggregation
            grouped = df.groupby(["time"]).apply(
                lambda g: g["weighted_val"].sum() / g["weight"].sum()
            ).reset_index(name="value")
            grouped["date"] = grouped["time"].dt.strftime("%Y-%m-%d")

        grouped = grouped.sort_values("date")

        # Optional seasonal adjustment (subtract monthly climatology)
        if remove_seasonality and aggregation == "monthly":
            grouped["month"] = pd.to_datetime(grouped["date"]).dt.month
            monthly_clim = grouped.groupby("month")["value"].transform("mean")
            overall_mean = grouped["value"].mean()
            grouped["value"] = grouped["value"] - monthly_clim + overall_mean

        time_series = [
            {"date": row["date"], "value": float(round(row["value"], 4))}
            for _, row in grouped.iterrows()
        ]

        meta = {
            "sample_size": len(time_series),
            "missing_count": 0,
            "variable": var_upper,
            "region": region,
            "node_id": node_id,
            "aggregation": aggregation,
            "seasonality_removed": remove_seasonality
        }

        return time_series, meta

    def _extract_methane_series(
        self,
        region: str = "All_India",
        node_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Methane is a 4-snapshot pilot dataset, returned with explicit documentation.
        """
        if self.methane_df is None:
            raise RuntimeError("Methane pilot dataset not loaded.")

        df = self.methane_df.copy()
        if node_id:
            df = df[df["node_id"] == node_id]
        elif region and region != "All_India":
            df = df[df["region"] == region]

        if df.empty:
            return [], {"sample_size": 0, "missing_count": 0, "is_methane_gap": True}

        # Map to date string
        df["date"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
        grouped = df.groupby("date")["methane_median_ppb"].mean().reset_index()
        grouped = grouped.sort_values("date")

        time_series = [
            {"date": row["date"], "value": float(round(row["methane_median_ppb"], 2))}
            for _, row in grouped.iterrows()
        ]

        meta = {
            "sample_size": len(time_series),
            "missing_count": 0,
            "variable": "CH4",
            "region": region,
            "node_id": node_id,
            "is_pilot_sparse": True
        }

        return time_series, meta

    def get_methane_summary(self) -> Dict[str, Any]:
        if self.methane_df is None:
            return {}

        periods = [
            {"period": "2019-05", "name": "May 2019 (Pre-monsoon)", "nodes_observed": int((self.methane_df["year"] == 2019).sum())},
            {"period": "2021-02", "name": "February 2021 (Winter)", "nodes_observed": int(((self.methane_df["year"] == 2021) & (self.methane_df["month"] == 2)).sum())},
            {"period": "2021-08", "name": "August 2021 (Monsoon Gap)", "nodes_observed": int(((self.methane_df["year"] == 2021) & (self.methane_df["month"] == 8)).sum())},
            {"period": "2023-11", "name": "November 2023 (Post-monsoon)", "nodes_observed": int(((self.methane_df["year"] == 2023) & (self.methane_df["month"] == 11)).sum())}
        ]

        regions_breakdown = []
        for reg in geo_service.get_regions():
            rid = reg["id"]
            if rid == "All_India":
                count = len(self.methane_df)
                mean_val = float(self.methane_df["methane_median_ppb"].mean())
            else:
                m_sub = self.methane_df[self.methane_df["region"] == rid]
                count = len(m_sub)
                mean_val = float(m_sub["methane_median_ppb"].mean()) if count > 0 else None

            regions_breakdown.append({
                "region_id": rid,
                "region_name": reg["name"],
                "records_count": count,
                "mean_methane_ppb": round(mean_val, 2) if mean_val is not None else None,
                "status": "UNAVAILABLE" if count == 0 else "OBSERVED"
            })

        return {
            "total_pixels_filtered": 73045,
            "total_node_month_records": len(self.methane_df),
            "unique_observed_nodes": int(self.methane_df["node_id"].nunique()),
            "total_spatial_nodes": 255,
            "periods": periods,
            "regional_coverage": regions_breakdown,
            "scientific_warning": (
                "Sentinel-5P TROPOMI observations are a 4-month pilot dataset. "
                "Atmospheric column concentration (ppb) is not surface emission flux (kg/hr). "
                "Data gaps represent missing/cloud-filtered soundings, never zero concentration."
            )
        }

data_service = DataService()
