# Technical Architecture — Earth Systems Trend Detective

## System Architecture Diagram

```
+--------------------------------------------------------------------------+
|                            USER INTERFACE LAYER                          |
|  - Vanilla HTML5 / Modern CSS3 / Dark NASA Theme (Inter & JetBrains Mono)|
|  - Leaflet.js Geospatial Mapping (Dark Matter, 255 Nodes, Polygons)      |
|  - Plotly.js Interactive Scientific Charting (10 Telemetry Charts)       |
|  - Responsive Mobile / Tablet / Desktop Navigation & Filter Toolbars    |
+------------------------------------+-------------------------------------+
                                     |
                                     | HTTP REST (JSON / GeoJSON)
                                     v
+--------------------------------------------------------------------------+
|                          BACKEND APPLICATION LAYER                       |
|  - Node.js (v24.18) & Express.js (Modular Controllers & Routes)          |
|  - In-Memory Caching & Dataset Service (Reads Verified Exports)          |
|  - JWT Authentication & Bcrypt Password Hashing                          |
|  - Multi-Provider Grounded AI Assistant (Gemini / OpenAI / Local Engine) |
+------------------+------------------------------------+------------------+
                   |                                    |
                   | Child Process / IPC                | Mongoose ORM / Fallback
                   v                                    v
+------------------------------------+  +----------------------------------+
|      SCIENTIFIC PYTHON ENGINE      |  |         PERSISTENCE LAYER        |
|  - Python 3.12 (.venv)             |  |  - MongoDB / Mongoose            |
|  - PyTorch MethanePredictor        |  |  - Local JSON Fallback Store     |
|  - 15 Model Checkpoints            |  |  - User Profiles, Saved Analyses |
|  - Feature Scaling & Target Denorm |  |  - Saved Reports & Chat History  |
+------------------------------------+  +----------------------------------+
```

## Architectural Principles
1. **Strict Data Grounding:** Analytical datasets are read from verified exports in `data/processed/dashboard_exports/`, eliminating runtime ETL overhead or large database ingestion.
2. **Dual-Mode Persistence:** MongoDB is leveraged when available, while a transparent file-backed fallback ensures uninterrupted operation during offline evaluations.
3. **Controlled Scientific Interface:** Live machine learning inference executes through verified PyTorch checkpoints under standardized feature pre-processing.
