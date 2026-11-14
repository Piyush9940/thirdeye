const fs = require('fs');
const path = require('path');
const env = require('../config/environment');
const logger = require('../utils/logger');

class DataService {
  constructor() {
    this.nodesCache = null;
    this.edgesCache = null;
    this.boundaryCache = null;
    this.exportsCache = {};
  }

  getMetadata() {
    return {
      project: "Earth Systems Trend Detective",
      tagline: "Discover What Is Changing on Earth. Understand Where. Measure How Much.",
      challenge: "NASA Space Apps Challenge 2026",
      version: "1.0.0",
      geographic_coverage: {
        country: "India",
        latitude_range: [7.0, 39.0],
        longitude_range: [69.0, 97.0],
        spatial_mesh: "2.0-degree spherical grid (~222 km)",
        total_nodes: 255,
        connected_components: 1,
        average_degree: 4.19
      },
      temporal_coverage: {
        primary_climate: {
          source: "NASA POWER MERRA-2 Assimilation",
          start_date: "2015-01",
          end_date: "2024-12",
          total_months: 120,
          total_observations: 30600,
          completeness: "100.0% (Zero missing monthly values across 255 nodes)"
        },
        methane_pilot: {
          source: "Sentinel-5P / TROPOMI (Offline & Reprocessed)",
          snapshots: ["2019-05", "2021-02", "2021-08", "2023-11"],
          total_node_months: 226,
          unique_observed_nodes: 98,
          qa_threshold: ">= 0.50 (Filtered)",
          monsoon_limitation: "August 2021 contains only 11 soundings due to deep monsoon convective cloud cover."
        }
      },
      variables: {
        T2M: {
          code: "T2M",
          name: "Air Temperature at 2m",
          units: "°C",
          description: "Monthly mean near-surface air temperature at 2 meters from NASA POWER assimilation.",
          range_observed: [-21.7, 38.6],
          mean_observed: 24.1
        },
        PRECTOTCORR: {
          code: "PRECTOTCORR",
          name: "Precipitation Rate",
          units: "mm/day",
          description: "Bias-corrected monthly total precipitation rate from NASA POWER.",
          range_observed: [0.0, 34.2],
          mean_observed: 3.2
        },
        RH2M: {
          code: "RH2M",
          name: "Relative Humidity at 2m",
          units: "%",
          description: "Monthly mean relative humidity at 2 meters above ground from NASA POWER.",
          range_observed: [12.4, 98.7],
          mean_observed: 62.4
        },
        WS10M: {
          code: "WS10M",
          name: "Wind Speed at 10m",
          units: "m/s",
          description: "Monthly mean wind speed at 10 meters above ground from NASA POWER.",
          range_observed: [0.8, 12.3],
          mean_observed: 3.4
        },
        CH4: {
          code: "CH4",
          name: "Column Methane (XCH4)",
          units: "ppb",
          description: "Tropospheric dry-air column-averaged methane from Sentinel-5P TROPOMI (4 pilot snapshots).",
          range_observed: [1750.2, 1995.8],
          mean_observed: 1861.16,
          limitation_notice: "Exploratory pilot observations. Not 10-year continuous. Concentration does not equal surface emissions flux."
        }
      },
      regions: [
        { code: "ALL", name: "All India (National Grid)", nodes_count: 255, description: "Composite nationwide domain" },
        { code: "NW", name: "Northwest India", nodes_count: 56, description: "Lat >= 25°N, Lon < 82°E (Indo-Gangetic West, Thar, Himalayas)" },
        { code: "NE", name: "Northeast India", nodes_count: 64, description: "Lat >= 25°N, Lon >= 82°E (Assam, Brahmaputra valley, Eastern Himalayas)" },
        { code: "CW", name: "Central-West India", nodes_count: 35, description: "15°N <= Lat < 25°N, Lon < 82°E (Maharashtra, Gujarat, Malwa Plateau)" },
        { code: "CE", name: "Central-East India", nodes_count: 40, description: "15°N <= Lat < 25°N, Lon >= 82°E (Chhota Nagpur, Odisha, Chhattisgarh)" },
        { code: "SW", name: "Southwest India", nodes_count: 28, description: "Lat < 15°N, Lon < 82°E (Western Ghats, Karnataka, Kerala)" },
        { code: "SE", name: "Southeast India", nodes_count: 32, description: "Lat < 15°N, Lon >= 82°E (Coromandel Coast, Tamil Nadu, Andhra Coast)" }
      ]
    };
  }

  getSpatialNodes() {
    if (this.nodesCache) return this.nodesCache;

    try {
      if (fs.existsSync(env.PATHS.NODES_CSV)) {
        const raw = fs.readFileSync(env.PATHS.NODES_CSV, 'utf-8');
        const lines = raw.trim().split('\n');
        const header = lines[0].split(',').map(h => h.trim());
        const nodes = [];

        for (let i = 1; i < lines.length; i++) {
          const parts = lines[i].split(',').map(p => p.trim());
          if (parts.length >= 3) {
            const lat = parseFloat(parts[1]);
            const lon = parseFloat(parts[2]);
            const id = parts[0];
            const idx = parseInt(parts[3] || (i - 1), 10);
            
            // Assign custom region code
            let reg = 'NW';
            if (lon >= 82.0 && lat >= 25.0) reg = 'NE';
            else if (lon < 82.0 && lat >= 25.0) reg = 'NW';
            else if (lon < 82.0 && lat >= 15.0) reg = 'CW';
            else if (lon >= 82.0 && lat >= 15.0) reg = 'CE';
            else if (lon < 82.0 && lat < 15.0) reg = 'SW';
            else if (lon >= 82.0 && lat < 15.0) reg = 'SE';

            nodes.push({
              node_id: id,
              node_index: idx,
              lat,
              lon,
              region: reg,
              degree: parseInt(parts[4] || '8', 10),
              connected_component: parseInt(parts[5] || '0', 10)
            });
          }
        }
        this.nodesCache = nodes;
        return nodes;
      }
    } catch (err) {
      logger.error(`[DataService] Error parsing nodes CSV: ${err.message}`);
    }

    return [];
  }

  getSpatialEdges() {
    if (this.edgesCache) return this.edgesCache;

    try {
      if (fs.existsSync(env.PATHS.EDGES_CSV)) {
        const raw = fs.readFileSync(env.PATHS.EDGES_CSV, 'utf-8');
        const lines = raw.trim().split('\n');
        const edges = [];
        for (let i = 1; i < lines.length; i++) {
          const parts = lines[i].split(',').map(p => p.trim());
          if (parts.length >= 6) {
            edges.push({
              source_index: parseInt(parts[0], 10),
              target_index: parseInt(parts[1], 10),
              source: parts[2],
              target: parts[3],
              distance_km: parseFloat(parts[4]),
              weight: parseFloat(parts[5])
            });
          } else if (parts.length >= 2) {
            edges.push({
              source: parts[0],
              target: parts[1],
              weight: parts[2] ? parseFloat(parts[2]) : 1.0
            });
          }
        }
        this.edgesCache = edges;
        return edges;
      }
    } catch (err) {
      logger.error(`[DataService] Error parsing edges CSV: ${err.message}`);
    }
    return [];
  }

  getBoundaryGeoJSON() {
    if (this.boundaryCache) return this.boundaryCache;

    try {
      if (fs.existsSync(env.PATHS.INDIA_GEOJSON)) {
        const raw = fs.readFileSync(env.PATHS.INDIA_GEOJSON, 'utf-8');
        this.boundaryCache = JSON.parse(raw);
        return this.boundaryCache;
      }
    } catch (err) {
      logger.error(`[DataService] Error parsing boundary GeoJSON: ${err.message}`);
    }
    return null;
  }

  /**
   * Central Scientific Dataset Registry
   * Records metadata, schema, variables, coverage, provenance, and validation status
   */
  getDatasetRegistry() {
    return [
      {
        dataset_id: "ds_nasa_power_grid_2deg",
        name: "NASA POWER 2.0-Degree Decadal Climate Grid",
        source: "NASA POWER (Prediction of Worldwide Energy Resources) / MERRA-2 Assimilation",
        file_path: env.PATHS.NASA_POWER_GRID_2DEG,
        format: "Parquet",
        coordinate_reference_system: "WGS 84 (EPSG:4326)",
        variables: [
          { code: "T2M", name: "Air Temperature at 2m", unit: "°C" },
          { code: "PRECTOTCORR", name: "Precipitation Rate", unit: "mm/day" },
          { code: "RH2M", name: "Relative Humidity at 2m", unit: "%" },
          { code: "WS10M", name: "Wind Speed at 10m", unit: "m/s" }
        ],
        temporal_coverage: {
          start_date: "2015-01-01",
          end_date: "2024-12-01",
          total_months: 120,
          frequency: "Monthly"
        },
        spatial_coverage: {
          domain: "India Subcontinent",
          spatial_mesh: "2.0° spherical grid (~222 km)",
          total_nodes: 255,
          latitude_range: [7.0, 39.0],
          longitude_range: [69.0, 97.0]
        },
        record_count: 30600,
        missing_values_count: 0,
        completeness_pct: 100.0,
        quality_status: "VERIFIED",
        data_provenance: "Assimilated satellite & reanalysis meteorology from NASA Langley Research Center MERRA-2.",
        last_validation_status: "PASSED (100% complete, 30,600 node-months)"
      },
      {
        dataset_id: "ds_nasa_power_merged",
        name: "NASA POWER High-Resolution Historical Climate Mesh",
        source: "NASA POWER / MERRA-2",
        file_path: env.PATHS.NASA_POWER_MERGED,
        format: "Parquet",
        coordinate_reference_system: "WGS 84 (EPSG:4326)",
        variables: [
          { code: "T2M", name: "Air Temperature at 2m", unit: "°C" },
          { code: "PRECTOTCORR", name: "Precipitation Rate", unit: "mm/day" },
          { code: "RH2M", name: "Relative Humidity at 2m", unit: "%" },
          { code: "WS10M", name: "Wind Speed at 10m", unit: "m/s" }
        ],
        temporal_coverage: {
          start_date: "2015-01-01",
          end_date: "2024-12-01",
          total_months: 120,
          frequency: "Monthly"
        },
        spatial_coverage: {
          domain: "India Subcontinent Grid",
          latitude_range: [7.0, 39.0],
          longitude_range: [69.0, 97.0]
        },
        record_count: 374400,
        missing_values_count: 0,
        completeness_pct: 100.0,
        quality_status: "VERIFIED",
        data_provenance: "Full-domain climate records covering all grid interpolations.",
        last_validation_status: "PASSED"
      },
      {
        dataset_id: "ds_sentinel5p_methane_pilot",
        name: "Sentinel-5P/TROPOMI Column Methane (XCH4) Pilot Observations",
        source: "Copernicus Sentinel-5 Precursor / TROPOMI Level-2 Offline & Reprocessed",
        file_path: env.PATHS.METHANE_PILOT_PARQUET,
        format: "Parquet",
        coordinate_reference_system: "WGS 84 (EPSG:4326)",
        variables: [
          { code: "XCH4", name: "Atmospheric Column Methane", unit: "ppb" },
          { code: "median_precision_ppb", name: "Observation Precision", unit: "ppb" },
          { code: "methane_pixel_count", name: "Filtered Sounding Pixels", unit: "count" }
        ],
        temporal_coverage: {
          snapshots: ["2019-05", "2021-02", "2021-08", "2023-11"],
          total_periods: 4,
          frequency: "Discontinuous Snapshot Pilot"
        },
        spatial_coverage: {
          domain: "India Spatial Graph",
          observed_nodes: 98,
          total_grid_nodes: 255,
          unobserved_nodes_count: 157
        },
        record_count: 226,
        missing_values_count: 0,
        quality_filtering: "qa_value >= 0.50 optical cloud threshold",
        quality_status: "PILOT_EXPLORATORY",
        data_provenance: "Derived from 73,045 QA-filtered Level-2 satellite pixels across 7 granules matched to spatial graph nodes.",
        scientific_limitations: "4 uneven snapshots cannot establish decadal trend. Southeast India has 0 valid soundings in pilot. Concentration != surface emissions flux.",
        last_validation_status: "PASSED"
      },
      {
        dataset_id: "ds_spherical_graph_topology",
        name: "India 255-Node Spherical Nearest-Neighbor Spatial Graph",
        source: "Spherical Graph Construction Pipeline",
        file_path: env.PATHS.NODES_CSV,
        format: "CSV (Nodes) & CSV (Edges)",
        coordinate_reference_system: "Spherical Great-Circle Topology",
        components: {
          nodes_file: env.PATHS.NODES_CSV,
          edges_file: env.PATHS.EDGES_CSV,
          edges_bidi_file: env.PATHS.EDGES_BIDI_CSV
        },
        topology: {
          nodes: 255,
          undirected_edges: 1068,
          directed_edges: 2136,
          connected_components: 1,
          graph_type: "8-Nearest-Neighbor Spatial Mesh",
          edge_weights: "Inverse great-circle distance (1 / d)"
        },
        quality_status: "VERIFIED",
        last_validation_status: "PASSED (Single connected component, 1,068 valid undirected edges)"
      }
    ];
  }

  getMethaneObservations() {
    if (this.exportsCache['methane_observations']) {
      return this.exportsCache['methane_observations'];
    }

    const jsonPath = path.resolve(env.PATHS.DASHBOARD_EXPORTS, 'methane_observations.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const raw = fs.readFileSync(jsonPath, 'utf-8');
        const parsed = JSON.parse(raw);
        this.exportsCache['methane_observations'] = parsed;
        return parsed;
      } catch (err) {
        logger.warn(`[DataService] methane_observations.json read error: ${err.message}`);
      }
    }
    return [];
  }

  getMLPredictions() {
    if (this.exportsCache['mlp_predictions']) {
      return this.exportsCache['mlp_predictions'];
    }

    const jsonPath = path.resolve(env.PATHS.DASHBOARD_EXPORTS, 'mlp_predictions.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const raw = fs.readFileSync(jsonPath, 'utf-8');
        const parsed = JSON.parse(raw);
        this.exportsCache['mlp_predictions'] = parsed;
        return parsed;
      } catch (err) {
        logger.warn(`[DataService] mlp_predictions.json read error: ${err.message}`);
      }
    }
    return [];
  }

  getFoldSummary() {
    if (this.exportsCache['fold_summary']) {
      return this.exportsCache['fold_summary'];
    }

    const jsonPath = path.resolve(env.PATHS.DASHBOARD_EXPORTS, 'fold_summary.json');
    if (fs.existsSync(jsonPath)) {
      try {
        const raw = fs.readFileSync(jsonPath, 'utf-8');
        const parsed = JSON.parse(raw);
        this.exportsCache['fold_summary'] = parsed;
        return parsed;
      } catch (err) {
        logger.warn(`[DataService] fold_summary.json read error: ${err.message}`);
      }
    }
    return [];
  }
}

module.exports = new DataService();
