# NASA Space Apps Challenge 2026: Earth Systems Trend Detective
> **"Discover What Is Changing on Earth. Understand Where. Measure How Much."**

[![Node.js](https://img.shields.io/badge/Node.js-v24.x-green.svg)](https://nodejs.org/)
[![Express.js](https://img.shields.io/badge/Express-v4.x-lightgrey.svg)](https://expressjs.com/)
[![SciPy](https://img.shields.io/badge/SciPy-Statistical_Engine-blue.svg)](https://scipy.org/)
[![Three.js](https://img.shields.io/badge/Three.js-3D_Earth-black.svg)](https://threejs.org/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF_Dossiers-red.svg)](https://www.reportlab.com/)

---

## 1. Executive Summary & Challenge Alignment

This platform directly answers the four core mandates of the NASA Space Apps Challenge 2026, **"Be An Earth System Trend Detective!"**:

1. **Identified Earth-Science Variables:**
   - **Air Temperature at 2m (`T2M`)**: in °C (NASA POWER / MERRA-2)
   - **Precipitation Rate (`PRECTOTCORR`)**: in mm/day
   - **Relative Humidity at 2m (`RH2M`)**: in %
   - **Wind Speed at 10m (`WS10M`)**: in m/s
   - **Atmospheric Column Methane (`XCH4`)**: in ppb (Sentinel-5P / TROPOMI)
2. **Acquired Regional Observations:**
   - 255 spatial graph nodes across India on a 2.0° spherical grid (~222 km mesh)
   - Partitioned into 6 custom zones: Northwest (`NW`), Northeast (`NE`), Central-West (`CW`), Central-East (`CE`), Southwest (`SW`), and Southeast (`SE`)
3. **Decadal Time-Series Generated:**
   - 10-year continuous monthly time series (January 2015 to December 2024, 120 months)
   - 30,600 verified climate records with 100% completeness (0 missing values)
4. **Rate of Change & Statistical Significance Tested:**
   - **Parametric:** Ordinary Least Squares (OLS) regression slope, $R^2$, p-value, and Student's $t$ 95% confidence intervals
   - **Non-Parametric:** Theil-Sen median robust slope (immune to seasonal spikes and outliers)
   - **Hypothesis Testing:** Exact two-tailed Mann-Kendall rank trend test with tie correction at $\alpha = 0.05$
   - **Dynamic Plain-Language Interpretation:** Automatically synthesized scientific verdicts for public accessibility

---

## 2. System Architecture

The application strictly follows the mandated architecture:
- **Primary Backend:** **Node.js + Express** (`dashboard/backend/`)
  - RESTful APIs under `/api/`
  - In-memory sliding window rate limiting
  - In-memory computation cache (<1ms cache hits)
  - Mongoose MongoDB integration with automatic persistent JSON fallback
- **Scientific Computation Bridge:** Controlled Python subprocesses (`dashboard/backend/python/`)
  - `statistical_engine.py`: SciPy-powered OLS, Mann-Kendall, Sen's slope, seasonal decomposition
  - `dataset_processor.py`: Dynamic ingestion, schema validation, quality scoring, and baseline comparison for user datasets
  - `ml_inference.py`: CPU-based forward pass of 15 PyTorch checkpoints (`folds 1-3`, `seeds 7-123`)
  - `report_generator.py`: Publication-grade PDF dossier generation via ReportLab
- **Frontend Experience:** Modern Vanilla JavaScript, CSS3 Space Dark Theme, Bootstrap 5 (`dashboard/frontend/`)
  - **3D Earth Homepage:** Three.js procedural globe with atmospheric glow, starfield, telemetry HUD, and animated camera fly-to India
  - **Trend Detective Workspace:** Interactive Plotly charts with OLS fit, Sen's slope, 95% confidence band, 4-metric scorecard, and PDF export
  - **Dynamic Dataset Explorer:** Ingest custom CSV/NetCDF datasets, validate data completeness, map variables, calculate rate of change & compare against NASA POWER climatology
  - **Earth Explorer:** Leaflet.js dark map displaying 255 nodes, 8-NN graph topology, and local trend inspector
  - **Regional Comparison:** Cross-regional ranking table and comparative bar chart
  - **Climate Explorer:** 10-year monthly climatology and 4-season breakdown
  - **Sentinel-5P Methane Module:** 4-snapshot pilot observations, QA $\ge 0.50$ filtering, and Southeast India data gap analysis
  - **Experimental ML Insights:** Empirical model comparisons, negative $R^2$ disclosure, and live CPU inference sandbox
  - **AI Research Assistant:** Grounded Q&A assistant with strict scientific guardrails
  - **Research Dossiers:** Dynamic PDF report generator and history

---

## 3. Directory Layout

```
dashboard/
├── backend/
│   ├── .env.example
│   ├── package.json
│   ├── public/
│   │   └── reports/              # Generated PDF research dossiers
│   ├── python/
│   │   ├── statistical_engine.py # SciPy OLS, Mann-Kendall, Sen's slope
│   │   ├── ml_inference.py       # PyTorch CPU inference bridge
│   │   └── report_generator.py   # ReportLab PDF generator
│   └── src/
│       ├── app.js                # Express app & static routing
│       ├── server.js             # HTTP server entry point
│       ├── config/               # database.js, environment.js
│       ├── controllers/          # API controllers
│       ├── middleware/           # auth, error, rate-limiter, validator
│       ├── routes/               # Express REST routes
│       ├── services/             # dataService, statisticalService, etc.
│       └── utils/                # logger, responseFormatter, safePath
├── frontend/
│   ├── index.html                # 3D Earth homepage
│   ├── pages/                    # 8 functional application pages
│   ├── css/                      # Space Dark design system
│   └── js/                       # Modular client scripts
└── tests/
    ├── test_statistical_engine.py # 4/4 Python statistical tests
    └── test_api_endpoints.js     # 13/13 REST API acceptance tests
```

---

## 4. Quickstart Guide (Windows)

### Prerequisites
- Node.js v18+ (tested on Node.js v24.18)
- Python 3.10+ (with `pandas`, `numpy`, `scipy`, `reportlab`, `torch`)

### 1. Launch the Backend Server
```powershell
cd C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective\dashboard\backend
node src/server.js
```
The server will start on `http://localhost:5000`.

### 2. Open in Your Browser
Open:
```
http://localhost:5000
```
- Navigate to the **3D Earth Homepage** (`/`)
- Open the **Trend Detective Workspace** (`/pages/trend-detective.html`)
- Explore the **Earth Explorer Geospatial Mesh** (`/pages/earth-explorer.html`)
- Run queries with the **AI Research Assistant** (`/pages/ai-assistant.html`)
- Download a generated **Research Dossier (PDF)** (`/pages/reports.html`)

---

## 5. Verification & Acceptance Testing

Run the automated acceptance suite verifying all 70 core requirements across static assets, REST APIs, statistical engine, report generator, error handling, and dynamic data ingestion:
```powershell
node C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective\dashboard\tests\verify_integrations.js
```

Expected Output:
```
======================================================================
  INTEGRATION AUDIT SUMMARY:
  Total Checks:  70
  Passed:        70
  Failed:        0
======================================================================
```

### Dynamic Scientific Ingestion Endpoints (Section 8 Mandate)
- `POST /api/datasets/upload`: Ingest user CSV/NetCDF datasets up to 50MB
- `POST /api/datasets/validate`: Check completeness score, detected fields, temporal frequency, and bounds
- `GET /api/datasets`: Retrieve all registered datasets in repository
- `GET /api/datasets/:id`: Inspect dataset details and 25 preview records
- `GET /api/datasets/:id/metadata`: Query scientific metadata and column moments
- `DELETE /api/datasets/:id`: Safely purge dataset file and catalog entry
- `POST /api/datasets/:id/analyze`: Compute OLS slope, Theil-Sen rate, Mann-Kendall test, and 95% CI bands on custom user data
- `POST /api/datasets/:id/compare`: Correlate and calculate RMSE / bias vs NASA POWER 10-year climatology baselines

---

## 6. Scientific Integrity & Data Ethics Disclosures

1. **Continuous Climate vs. Pilot Satellite Methane:** NASA POWER climate data is a continuous 10-year monthly record (2015–2024, 30,600 observations). In contrast, Sentinel-5P atmospheric methane is an exploratory 4-snapshot pilot (May 2019, Feb 2021, Aug 2021, Nov 2023).
2. **Column Concentration vs. Surface Emissions:** Atmospheric column dry-air mole fraction ($X\text{CH}_4$ in ppb) reflects atmospheric transport and boundary layer advection, and is **never** presented as direct surface emission flux.
3. **Southeast India Data Gap:** In the pilot release, 0 valid soundings survived optical cloud filtering (QA $\ge 0.50$) over Southeast India. It is transparently presented as unavailable, never zero.
4. **Machine Learning Model Scope:** Neural network models are exploratory baselines exhibiting negative $R^2$ (-0.92) due to monsoon cloud filtering and spatial sparsity. They are clearly labeled as experimental and not approved for operational forecasting.
