"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Observations & Data Coverage Route
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..services.data_service import data_service

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/observations")
def get_observations(
    variable: str = Query("T2M", description="Variable ID"),
    region: Optional[str] = Query("All_India", description="Region ID"),
    node_id: Optional[str] = Query(None, description="Node ID"),
    start_date: Optional[str] = Query("2015-01-01"),
    end_date: Optional[str] = Query("2024-12-01"),
    aggregation: Optional[str] = Query("monthly")
):
    try:
        series, meta = data_service.extract_time_series(
            variable=variable,
            region=region,
            node_id=node_id,
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation
        )
        return {
            "success": True,
            "count": len(series),
            "meta": meta,
            "data": series
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coverage")
def get_coverage():
    return {
        "success": True,
        "climate": {
            "dataset": "NASA POWER Surface Meteorology (2° Grid)",
            "spatial_nodes": 255,
            "months_per_node": 120,
            "total_records": 30600,
            "temporal_range": "2015-01-01 to 2024-12-01",
            "completeness_pct": 100.0,
            "missing_months": 0
        },
        "methane": {
            "dataset": "Copernicus Sentinel-5P TROPOMI Level-3 (QA >= 0.50)",
            "total_pixels_filtered": 73045,
            "node_month_records": 226,
            "unique_observed_nodes": 98,
            "unobserved_nodes": 157,
            "periods": ["2019-05", "2021-02", "2021-08", "2023-11"],
            "characterization": "Sparse pilot dataset, NOT a continuous national monthly series"
        }
    }
