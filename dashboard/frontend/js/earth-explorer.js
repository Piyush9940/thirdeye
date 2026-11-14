/**
 * NASA Earth Systems Trend Detective — Earth Explorer Map
 * Leaflet.js Dark Matter Geospatial Mesh & Spatial Inspector
 */

class EarthExplorer {
  constructor(containerId = 'leaflet-map') {
    this.containerId = containerId;
    this.map = null;
    this.nodesLayer = null;
    this.edgesLayer = null;
    this.boundaryLayer = null;
    this.nodes = [];
    this.edges = [];

    this.init();
  }

  async init() {
    this.setupMap();
    await this.loadData();
    this.renderBoundary();
    this.renderEdges();
    this.renderNodes();
    this.setupControls();
  }

  setupMap() {
    // Center map over India: 22°N, 82°E, zoom 5
    this.map = L.map(this.containerId, {
      center: [22.0, 82.0],
      zoom: 5,
      minZoom: 4,
      maxZoom: 9,
      zoomControl: true
    });

    // Dark CartoDB basemap tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> & NASA POWER',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(this.map);
  }

  async loadData() {
    try {
      const [nodes, edges, boundary] = await Promise.all([
        window.api.getMapNodes(),
        window.api.getMapEdges(),
        window.api.getBoundary()
      ]);

      this.nodes = nodes || [];
      this.edges = edges || [];
      this.boundary = boundary || null;
    } catch (err) {
      console.error('[EarthExplorer] Failed to load spatial data:', err);
      window.showToast('Could not load spatial mesh', 'error');
    }
  }

  renderBoundary() {
    if (!this.boundary) return;

    this.boundaryLayer = L.geoJSON(this.boundary, {
      style: {
        color: '#00f2fe',
        weight: 1.5,
        opacity: 0.6,
        fillColor: '#00f2fe',
        fillOpacity: 0.03
      }
    }).addTo(this.map);
  }

  renderEdges() {
    if (!this.edges.length || !this.nodes.length) return;

    const nodeMap = new Map();
    this.nodes.forEach(n => nodeMap.set(n.node_id, n));

    const edgeLines = [];
    this.edges.forEach(e => {
      const src = nodeMap.get(e.source);
      const tgt = nodeMap.get(e.target);
      if (src && tgt) {
        edgeLines.push([
          [src.lat, src.lon],
          [tgt.lat, tgt.lon]
        ]);
      }
    });

    this.edgesLayer = L.polyline(edgeLines, {
      color: 'rgba(0, 242, 254, 0.12)',
      weight: 1,
      dashArray: '2, 4'
    }).addTo(this.map);
  }

  renderNodes(filteredNodes = null) {
    if (this.nodesLayer) {
      this.map.removeLayer(this.nodesLayer);
    }

    const targetNodes = filteredNodes || this.nodes;
    const markers = [];

    targetNodes.forEach(node => {
      const circle = L.circleMarker([node.lat, node.lon], {
        radius: 6,
        fillColor: '#00f2fe',
        color: '#ffffff',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.7
      });

      circle.bindTooltip(`
        <div style="font-family: Inter, sans-serif; font-size: 0.8rem; line-height: 1.4;">
          <b>Node: ${node.node_id}</b> (${node.region})<br>
          Lat: ${node.lat.toFixed(2)}°N | Lon: ${node.lon.toFixed(2)}°E<br>
          Degree: ${node.degree} edges
        </div>
      `, { className: 'custom-tooltip', sticky: true });

      circle.on('click', () => this.inspectNode(node));

      markers.push(circle);
    });

    this.nodesLayer = L.featureGroup(markers).addTo(this.map);
  }

  inspectNode(node) {
    const drawer = document.getElementById('node-inspector');
    if (!drawer) return;

    drawer.style.display = 'block';
    document.getElementById('insp-node-id').textContent = node.node_id;
    document.getElementById('insp-coords').textContent = `${node.lat.toFixed(2)}°N, ${node.lon.toFixed(2)}°E`;
    document.getElementById('insp-region').textContent = `${node.region}`;
    document.getElementById('insp-degree').textContent = `${node.degree} neighbors`;

    // Trigger local trend fetch for this single node
    this.loadNodeTrend(node.node_id);
  }

  async loadNodeTrend(nodeId) {
    const statusEl = document.getElementById('insp-status');
    if (statusEl) statusEl.textContent = 'Calculating localized trend...';

    try {
      const data = await window.api.getTrend({
        variable: 'T2M',
        node_id: nodeId
      });

      if (statusEl) {
        const rate = data.sen_slope?.slope_per_year;
        const sign = rate > 0 ? '+' : '';
        statusEl.innerHTML = `
          <b>Rate:</b> ${sign}${rate?.toFixed(4)} °C/yr<br>
          <b>Mann-Kendall p:</b> ${data.mann_kendall?.p_value?.toFixed(4)} (${data.mann_kendall?.is_significant ? 'Significant' : 'No Trend'})
        `;
      }
    } catch (e) {
      if (statusEl) statusEl.textContent = 'Could not load local trend.';
    }
  }

  setupControls() {
    const regFilter = document.getElementById('map-region-filter');
    if (regFilter) {
      regFilter.addEventListener('change', (e) => {
        const reg = e.target.value;
        if (reg === 'ALL') {
          this.renderNodes(this.nodes);
        } else {
          this.renderNodes(this.nodes.filter(n => n.region === reg));
        }
      });
    }

    const toggleEdges = document.getElementById('toggle-edges');
    if (toggleEdges) {
      toggleEdges.addEventListener('change', (e) => {
        if (e.target.checked) this.map.addLayer(this.edgesLayer);
        else this.map.removeLayer(this.edgesLayer);
      });
    }
  }
}

window.EarthExplorer = EarthExplorer;
