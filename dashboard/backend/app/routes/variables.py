"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Variables Route
"""

from fastapi import APIRouter, HTTPException
from ..services.data_service import data_service

router = APIRouter(prefix="/api/variables", tags=["variables"])

@router.get("")
def get_variables():
    return {"success": True, "count": len(data_service.get_variables()), "data": data_service.get_variables()}

@router.get("/{var_id}")
def get_variable(var_id: str):
    info = data_service.get_variable_info(var_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Variable '{var_id}' not found.")
    return {"success": True, "data": info}
