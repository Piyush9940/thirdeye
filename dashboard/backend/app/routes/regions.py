"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Regions Route
"""

from fastapi import APIRouter
from ..services.geographic_service import geo_service

router = APIRouter(prefix="/api/regions", tags=["regions"])

@router.get("")
def get_regions():
    regions = geo_service.get_regions()
    return {"success": True, "count": len(regions), "data": regions}
