"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Methane Analysis Route: Sentinel-5P TROPOMI Pilot Observations
"""

from fastapi import APIRouter
from ..services.data_service import data_service

router = APIRouter(prefix="/api/methane", tags=["methane"])

@router.get("/summary")
def get_methane_summary():
    summary = data_service.get_methane_summary()
    return {"success": True, "data": summary}

@router.get("/observations")
def get_methane_observations():
    if data_service.methane_df is None:
        return {"success": True, "count": 0, "data": []}
    
    records = []
    for _, row in data_service.methane_df.iterrows():
        records.append({
            "node_id": str(row["node_id"]),
            "year": int(row["year"]),
            "month": int(row["month"]),
            "period": f"{row['year']}-{str(row['month']).zfill(2)}",
            "methane_median_ppb": round(float(row["methane_median_ppb"]), 2),
            "methane_mean_ppb": round(float(row["methane_mean_ppb"]), 2),
            "pixel_count": int(row.get("methane_pixel_count", 0)),
            "region": row.get("region", "Unknown"),
            "T2M": round(float(row.get("T2M", 0.0)), 2),
            "PRECTOTCORR": round(float(row.get("PRECTOTCORR", 0.0)), 2),
            "RH2M": round(float(row.get("RH2M", 0.0)), 2),
            "WS10M": round(float(row.get("WS10M", 0.0)), 2)
        })

    return {"success": True, "count": len(records), "data": records}
