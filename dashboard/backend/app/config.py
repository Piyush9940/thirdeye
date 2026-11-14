"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Backend Configuration & Dataset Path Registry
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective")
DASHBOARD_ROOT = PROJECT_ROOT / "dashboard"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Verified Dataset Absolute Paths (Read-Only)
NASA_POWER_GRID_PATH = DATA_PROCESSED / "nasa_power_grid_2deg.parquet"
NASA_POWER_MERGED_PATH = DATA_PROCESSED / "nasa_power_merged.parquet"
METHANE_PILOT_PATH = DATA_PROCESSED / "gnn_dataset" / "methane_climate_node_month_pilot.parquet"
SPHERICAL_NODES_PATH = DATA_PROCESSED / "gnn_dataset" / "spherical_graph_nodes.csv"
SPHERICAL_EDGES_PATH = DATA_PROCESSED / "gnn_dataset" / "spherical_graph_edges.csv"
INDIA_BOUNDARY_PATH = PROJECT_ROOT / "data" / "external" / "india_boundary" / "india_adm0.geojson"
DASHBOARD_EXPORTS_DIR = DATA_PROCESSED / "dashboard_exports"
MODEL_REFERENCE_DIR = PROJECT_ROOT / "models" / "production_reference"
PYTHON_VENV_PATH = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "*"
]

# Statistical Significance Settings
ALPHA_THRESHOLD = 0.05
MIN_OBSERVATIONS_FOR_TREND = 12

# Environment Variables for AI Providers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
MONGODB_URI = os.getenv("MONGODB_URI", "")
