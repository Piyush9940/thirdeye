"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Maps Route: Geospatial Lattice & GeoJSON Boundaries
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..services.geographic_service import geo_service

router = APIRouter(prefix="/api/maps", tags=["maps"])

@router.get("/nodes")
def get_map_nodes():
    nodes = geo_service.get_all_nodes()
    return {"success": True, "count": len(nodes), "data": nodes}

@router.get("/nodes/geojson")
def get_nodes_geojson():
    geojson = geo_service.get_spatial_nodes_geojson()
    if not geojson:
        raise HTTPException(status_code=404, detail="Nodes GeoJSON not available.")
    return JSONResponse(content=geojson)

@router.get("/boundary")
def get_india_boundary():
    geojson = geo_service.get_india_boundary_geojson()
    if not geojson:
        raise HTTPException(status_code=404, detail="India boundary GeoJSON not available.")
    return JSONResponse(content=geojson)
