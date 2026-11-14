# Preprocessing Methodology

1. **Pixel-Level QA Filtering:**
   All Sentinel-5P soundings with $\text{qa\_value} < 0.50$ are eliminated to remove thick clouds, snow/ice, and extreme solar zenith angles.
2. **Spatial Binning:**
   High-quality pixels within each 2° &times; 2° geographic cell are clustered and aggregated into robust statistics (median, mean, standard deviation).
3. **Temporal Collocation:**
   NASA POWER monthly surface meteorological parameters are collocated with observation cells and calendar timestamps.
4. **Graph Lattice Construction:**
   A spherical Haversine distance matrix connects adjacent nodes within distance thresholds to form spatial graph structures for GNN benchmarking.
