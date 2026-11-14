# Spatial Graph Construction & Topological Methodology

## 1. Spherical Graph Lattice
The Indian landmass is mapped into 255 discrete nodes positioned on a regular 2° by 2° spherical grid. 
Adjacency between nodes $i$ and $j$ is derived from their great-circle distance $d(i, j)$ using the spherical Haversine formula:
$$d(i, j) = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_i)\cos(\phi_j)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
where $R \approx 6371\text{ km}$ is Earth's mean radius, $\phi$ is latitude, and $\lambda$ is longitude.

## 2. Distance-Weighted Adjacency
For the distance-weighted Graph Convolutional Network (GCN), edges were weighted using a Gaussian kernel:
$$W_{ij} = \exp\left(-\frac{d(i, j)^2}{2\sigma^2}\right) \quad \text{for } d(i, j) \le d_{\text{max}}$$

## 3. Findings from Graph Experiments
- While the spatial graph accurately captures 8-neighborhood spatial proximity, empirical evaluation across chronological folds showed that Graph Neural Networks (GCN) did not outperform the baseline MLP on this sparse temporal pilot.
- The high temporal gap between observation snapshots (e.g., 2019 to 2021) made static spatial smoothing suboptimal compared to seasonal calendar representation.
