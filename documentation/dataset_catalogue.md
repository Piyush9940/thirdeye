# Dataset Catalogue & Data Provenance

## Primary Data Sources
1. **Satellite Atmospheric Methane ($X\text{CH}_4$):**
   - Mission: Copernicus Sentinel-5 Precursor (Sentinel-5P)
   - Instrument: TROPOspheric Monitoring Instrument (TROPOMI)
   - Product: Level-3 Offline Methane Total Column ($X\text{CH}_4$)
   - Quality Threshold: $\text{qa\_value} \ge 0.50$

2. **Surface Meteorological Reanalysis:**
   - Source: NASA POWER (Prediction of Worldwide Energy Resources)
   - Parameters:
     - `T2M`: Temperature at 2m (°C / Kelvin)
     - `PRECTOTCORR`: Corrected Precipitation (mm/day)
     - `RH2M`: Relative Humidity at 2m (%)
     - `WS10M`: Wind Speed at 10m (m/s)

3. **Geospatial Reference:**
   - Boundary: India Administrative Level 0 Polygon (`india_adm0.geojson`)
   - Spatial Grid: 2° &times; 2° regular lattice (255 nodes)
