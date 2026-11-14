# API Documentation — Earth Systems Trend Detective

## Base URL
All API requests are relative to `http://localhost:5000/api`.

---

## 1. System Health
### `GET /api/health`
Returns system status, active database mode, and platform metadata.

**Response:**
```json
{
  "status": "online",
  "platform": "Earth Systems Trend Detective",
  "version": "1.0.0",
  "database": {
    "connected": true,
    "mode": "mongodb"
  }
}
```

---

## 2. Telemetry & Dashboard
### `GET /api/dashboard/stats`
Returns core KPIs derived directly from verified export metadata.
- `spatialNodesCount`: 255
- `observationRecordsCount`: 226
- `evaluationPredictionsCount`: 720
- `modelCheckpointsCount`: 15
- `observationPeriods`: ["2019-05", "2021-02", "2021-08", "2023-11"]

### `GET /api/dashboard/charts?period={period}&region={region}`
Provides pre-aggregated data for the 10 interactive Plotly dashboard visualizations.

---

## 3. Geospatial & Boundary Endpoints
### `GET /api/geo/nodes?period={period}`
Returns the 255 grid nodes with latitude, longitude, topology degree, and observation data for the requested snapshot period.

### `GET /api/geo/boundary`
Returns the GeoJSON FeatureCollection containing the boundary polygon of India (`india_adm0.geojson`).

---

## 4. Observations & Predictions
### `GET /api/methane/observations`
Supports query parameters:
- `period`: Filter by temporal snapshot (e.g. `2019-05`, `2021-08`, `ALL`)
- `region`: Filter by geographic zone (`North_West`, `Central_East`, etc.)
- `page`: Page index (default: 1)
- `limit`: Records per page (default: 1000)

### `POST /api/predictions/infer`
Runs live inference using the PyTorch `MethanePredictor`.
**Body:**
```json
{
  "features": [25.0, 1.0, 50.0, 3.0, 23.0, 83.0, 0.5, 0.866],
  "fold": 1,
  "seed": 42
}
```

---

## 5. Reports & Assistant
### `POST /api/reports/generate`
Generates research dossiers (`summary`, `regional`, `ml_evaluation`).

### `POST /api/assistant/chat`
Interacts with the grounded AI Research Assistant copilot.
