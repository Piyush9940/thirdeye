"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
FastAPI Main Application & Static Asset Server
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import CORS_ORIGINS, DASHBOARD_ROOT
from .routes import trends, variables, regions, observations, maps, methane, models_research, reports, assistant

app = FastAPI(
    title="Earth Systems Trend Detective",
    description="Statistical Environmental Trend Investigation Platform for NASA Space Apps Challenge 2026",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Scientific REST API Routers
app.include_router(trends.router)
app.include_router(variables.router)
app.include_router(regions.router)
app.include_router(observations.router)
app.include_router(maps.router)
app.include_router(methane.router)
app.include_router(models_research.router)
app.include_router(reports.router)
app.include_router(assistant.router)

# Health Check Endpoint
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Earth Systems Trend Detective API",
        "challenge": "NASA Space Apps Challenge 2026",
        "engine": "FastAPI + NumPy + SciPy Statistical Engine"
    }

# Mount Frontend Static Assets
frontend_dir = DASHBOARD_ROOT / "frontend"

if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{page_name}.html")
    def serve_html_page(page_name: str):
        candidate = frontend_dir / f"{page_name}.html"
        if candidate.exists():
            return FileResponse(str(candidate))
        candidate_pages = frontend_dir / "pages" / f"{page_name}.html"
        if candidate_pages.exists():
            return FileResponse(str(candidate_pages))
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/")
    def serve_index():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Welcome to Earth Systems Trend Detective API. Visit /docs for OpenAPI documentation."}
