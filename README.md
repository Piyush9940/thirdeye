# Earth Systems Trend Detective
## Explore Earth. Understand Methane. Discover Environmental Patterns.
### NASA Space Apps Challenge — Earth Observation & Environmental Intelligence Platform

[![NASA Space Apps](https://img.shields.io/badge/NASA-Space%20Apps%20Challenge-0B3D91?style=for-the-badge&logo=nasa)](https://www.spaceappschallenge.org/)
[![Status](https://img.shields.io/badge/Model%20Release-Experimental%20Reference-orange?style=for-the-badge)]()
[![Data Stream](https://img.shields.io/badge/Sentinel--5P-TROPOMI%20Level--3-blue?style=for-the-badge)]()
[![Climate](https://img.shields.io/badge/NASA%20POWER-Surface%20Meteorology-green?style=for-the-badge)]()

---

## 1. Project Overview & Core Vision

**Earth Systems Trend Detective** transforms spaceborne satellite soundings, surface reanalysis meteorology, spatial graph topology, and open environmental science into an accessible, interactive exploration platform that helps ordinary people, students, teachers, and researchers understand atmospheric methane ($X\text{CH}_4$) variations across India.

### The Problem
Atmospheric methane ($\text{CH}_4$) is responsible for approximately 30% of modern global warming. It possesses over 80 times the heat-trapping power of carbon dioxide over a 20-year timescale. Monitoring its spatial patterns and regional distribution is critical for planetary health, yet raw satellite soundings often remain trapped in specialized formats inaccessible to the public.

### Mandatory Scientific Integrity Standards
1. **Atmospheric Concentration $\ne$ Surface Emissions:** Satellite-derived column abundance ($X\text{CH}_4$ in ppb) measures total vertical column mixing. It does **not** identify ground emission flux, pinpoint industrial leaks, or prove local illegal discharges without inverse Lagrangian dispersion modeling.
2. **Missing Observations $\ne$ Zero Concentration:** Satellite data gaps caused by dense monsoon cloud masking and quality thresholding ($\text{QA} < 0.50$) are explicitly retained as unobserved/missing, never plotted as zero.
3. **Model Status:** The machine learning reference model is strictly **"Experimental Reference Model — Not Production Approved"**. Negative $R^2$ scores and systematic negative bias reflect real temporal distribution shifts and data sparsity, presented with full scientific transparency.

---

## 2. Signature Experience: Immersive 3D Earth & Scroll Journey

The homepage features a cinematic Three.js 3D Earth synchronized with GSAP ScrollTrigger, taking visitors on a 6-scene journey from outer space to India's environmental landscape:

- **Scene 1 — Opening in Space:** Deep-space background, rotating 3D Earth, atmospheric glow, cloud layer, city lights, stars, mission branding, and scroll invitation.
- **Scene 2 — Global Exploration:** Camera approaches the globe, revealing continents, subtle latitude/longitude grid, satellite orbit paths, and planetary atmospheric systems.
- **Scene 3 — Understanding Methane:** Educational visualization introducing $\text{CH}_4$ molecules, the greenhouse effect, and the distinction between atmospheric concentration and surface emissions.
- **Scene 4 — Rotate Toward India:** Earth rotates until India (Centroid: 22°N, 79°E) faces the camera, highlighted by a radiant environmental target marker.
- **Scene 5 — Cinematic Zoom into India:** Continuous transition zooming into the subcontinent, revealing the 255 spatial lattice nodes and the six study regions (Northwest, Northeast, Central-West, Central-East, Southwest, Southeast). Southeast is highlighted as having unavailable observations in the pilot dataset (not zero).
- **Scene 6 — Enter the Environmental Dashboard:** 3D Earth smoothly transitions into the background, unveiling the live Project Overview Dashboard and interactive Leaflet map.

---

## 3. Verified Project Statistics

| Metric | Ground Truth Value | Scientific Explanation |
|---|---:|---|
| **Quality-filtered Methane Pixels** | **73,045** | Sub-pixel satellite soundings retained after applying QA threshold $\ge 0.50$. |
| **Spatial Grid Nodes** | **255** | 2° regular spherical lattice discretizing India [7°N–37°N, 69°E–97°E]. |
| **Methane Node-Month Records** | **226** | Spatially aggregated observations collocated with meteorology. |
| **Unique Observed Nodes** | **98** | Number of unique grid nodes with at least one valid observation. |
| **Available Observation Months** | **4 Snapshots** | May 2019, February 2021, August 2021, November 2023. |

*Note: This is a sparse pilot research dataset across four discrete temporal snapshots, not a continuous national monthly record.*

---

## 4. Platform Pages & Exploration Modules

- **Home (`index.html`):** The signature 3D Earth exploration homepage with GSAP ScrollTrigger camera choreography and 8-stage public storytelling.
- **Explore Earth / India Map (`earth-explorer.html`):** Interactive Leaflet dark-matter map with India administrative boundary, 255 grid nodes, color-coded soundings (Viridis palette), dashed unobserved rings, and node inspector.
- **Why Methane? (`why-methane.html`):** Plain-language educational guide explaining the greenhouse effect, 80x warming potential, short atmospheric lifetime (~12 years), Sentinel-5P TROPOMI satellite explainer, and the concentration vs. emissions distinction.
- **India Explorer Dashboard (`dashboard.html`):** 10 interactive Plotly.js charts displaying concentration KDE distributions, regional box plots, temporal observation counts, climate distributions, parity scatter, error residuals, and coverage missingness.
- **Our Findings (`findings.html`):** "What We Discovered" — honest analysis of satellite coverage inequality, monsoon cloud masking (August 2021 gap), and climate context without unsupported claims.
- **Environmental Impact (`impact.html`):** 5 pillars of potential relevance: research, climate awareness, education, environmental monitoring, and future research roadmap.
- **Scientific Methodology (`methodology.html`):** 9-step visual process from satellite acquisition to interactive dissemination with expandable mathematical details.
- **Data & Research Downloads (`data-research.html`):** Direct CSV, JSON, and GeoJSON downloads with strict categorization: [Measured Satellite Observations], [Climate Context], [Experimental Model Estimates], and [Evaluation Metrics].
- **About the Project (`about.html`):** Mission, NASA Space Apps Challenge background, 4 scientific commitments, and data attribution.
- **AI Research Assistant (`research-assistant.html`):** Grounded Q&A assistant explaining charts, terms, methodology, and scientific caveats.
- **Advanced Research & ML Lab (`advanced-research.html`):** Secondary technical section detailing GCN vs. MLP benchmarks, 3-fold chronological evaluation, 5-seed stability, negative $R^2$ diagnostics, and interactive live CPU predictor test bench.

---

## 5. Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Bootstrap 5, Three.js (r128), GSAP & GSAP ScrollTrigger (v3.12+), Leaflet.js, Plotly.js, FontAwesome.
- **Backend:** Node.js (v24.18.0), Express.js (v4.22), RESTful APIs, JWT authentication, Bcrypt password hashing.
- **Database:** MongoDB & Mongoose with zero-config in-memory / JSON fallback adapter (`data/users_store.json`).
- **Scientific Engine:** Python 3.12 (.venv), PyTorch on CPU, NumPy, Pandas, Scikit-learn, GeoPandas.
- **AI Integration:** Multi-provider architecture supporting Google Gemini, OpenAI, and a grounded local scientific retrieval engine.

---

## 6. Machine Learning Benchmarks (Optional Research Lab)

Chronological validation results across 3 folds and 5 random seeds:

| Model Architecture | Features Used | Equal-Fold Mean MAE | Equal-Fold Mean RMSE | Equal-Fold Mean R² | Equal-Fold Mean Bias |
|---|---|---:|---:|---:|---:|
| **Month-only Diagnostic** | Month Sine & Cosine | **49.04 ppb** | **52.68 ppb** | -10.49 | -46.49 ppb |
| **Original MLP Reference** | 8 Features (Climate + Geo + Calendar) | **53.79 ppb** | **56.87 ppb** | -13.35 | -50.85 ppb |
| **Distance-Weighted GCN** | 8 Features + Adjacency Graph | **58.48 ppb** | **60.76 ppb** | -11.49 | -58.01 ppb |
| **Global Training Mean** | Constant Historical Mean | 62.72 ppb | 65.07 ppb | -11.90 | -62.43 ppb |
| **Climate-only Ablation** | T2M, Precip, RH, Wind, Lat, Lon | 59.09 ppb | 63.26 ppb | -13.09 | -58.66 ppb |
| **Unweighted GCN** | 8 Features + Binary Adjacency | 70.93 ppb | 75.87 ppb | -23.94 | -64.82 ppb |

*Scientific Finding: Graph Neural Networks did not outperform the multi-layer perceptron on this sparse pilot dataset. Negative R² confirms that models are experimental reference artifacts, not operational forecasting tools.*

---

## 7. Getting Started & Installation

### Prerequisites
- Node.js >= 18.0.0
- Python >= 3.10 with PyTorch in `.venv` (configured in workspace)

### Installation
```bash
# Navigate to project directory
cd earth-systems-trend-detective

# Install backend dependencies
npm install
```

### Running the Application
```bash
# Start the Express server
npm start
```
Launch your browser and navigate to: **`http://localhost:5000`**

### Running the Automated Test Suite
```bash
# Inside earth-systems-trend-detective
npm test
```
Validates data integrity, observation filtering, 10-chart data structures, AI assistant integrity rules, and all 8 in-process REST API routes.
