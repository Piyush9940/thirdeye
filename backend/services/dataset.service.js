/**
 * NASA Earth Systems Trend Detective
 * Scientific Dataset Service - Reads & Caches Verified Project Exports
 */

const fs = require('fs');
const path = require('path');

class DatasetService {
  constructor() {
    this.baseDir = path.resolve(__dirname, '../../data/processed/dashboard_exports');
    this.reportsDir = path.resolve(__dirname, '../../reports');
    this.geoDir = path.resolve(__dirname, '../../data/external/india_boundary');

    this.metadata = null;
    this.spatialNodes = [];
    this.spatialGeoJSON = null;
    this.methaneObservations = [];
    this.predictions = [];
    this.foldSeedMetrics = [];
    this.foldSummary = [];
    this.indiaBoundary = null;
    this.modelComparisons = [];

    this.init();
  }

  init() {
    try {
      console.log('[DatasetService] Loading verified exports from:', this.baseDir);

      // 1. Metadata
      const metaPath = path.join(this.baseDir, 'dashboard_metadata.json');
      if (fs.existsSync(metaPath)) {
        this.metadata = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
      }

      // 2. Spatial Nodes
      const nodesPath = path.join(this.baseDir, 'spatial_nodes.json');
      if (fs.existsSync(nodesPath)) {
        this.spatialNodes = JSON.parse(fs.readFileSync(nodesPath, 'utf8'));
      }

      const geoPath = path.join(this.baseDir, 'spatial_nodes.geojson');
      if (fs.existsSync(geoPath)) {
        this.spatialGeoJSON = JSON.parse(fs.readFileSync(geoPath, 'utf8'));
      }

      // 3. Methane Observations
      const ch4Path = path.join(this.baseDir, 'methane_observations.json');
      if (fs.existsSync(ch4Path)) {
        this.methaneObservations = JSON.parse(fs.readFileSync(ch4Path, 'utf8'));
      }

      // 4. MLP Predictions
      const predPath = path.join(this.baseDir, 'mlp_predictions.json');
      if (fs.existsSync(predPath)) {
        this.predictions = JSON.parse(fs.readFileSync(predPath, 'utf8'));
      }

      // 5. Fold & Seed Metrics
      const metricsPath = path.join(this.baseDir, 'fold_seed_metrics.json');
      if (fs.existsSync(metricsPath)) {
        this.foldSeedMetrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
      }

      const summaryPath = path.join(this.baseDir, 'fold_summary.json');
      if (fs.existsSync(summaryPath)) {
        this.foldSummary = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
      }

      // 6. India ADM0 GeoJSON
      const boundaryPath = path.join(this.geoDir, 'india_adm0.geojson');
      if (fs.existsSync(boundaryPath)) {
        this.indiaBoundary = JSON.parse(fs.readFileSync(boundaryPath, 'utf8'));
      }

      // 7. Benchmark Comparisons from reports
      const compCsvPath = path.join(this.reportsDir, 'final_model_comparison_overall_summary.csv');
      if (fs.existsSync(compCsvPath)) {
        this.modelComparisons = this.parseCSV(fs.readFileSync(compCsvPath, 'utf8'));
      }

      console.log(`[DatasetService] Successfully loaded:
        - Nodes: ${this.spatialNodes.length}
        - Observations: ${this.methaneObservations.length}
        - Predictions: ${this.predictions.length}
        - Metrics: ${this.foldSeedMetrics.length} seeds across ${this.foldSummary.length} folds`);
    } catch (err) {
      console.error('[DatasetService] Initialization failed:', err);
    }
  }

  parseCSV(content) {
    const lines = content.trim().split('\n');
    if (lines.length < 2) return [];
    const headers = lines[0].split(',').map(h => h.trim());
    return lines.slice(1).map(line => {
      const parts = line.split(',').map(p => p.trim());
      const row = {};
      headers.forEach((h, i) => {
        const val = parts[i];
        row[h] = isNaN(val) ? val : parseFloat(val);
      });
      return row;
    });
  }

  getMetadata() {
    return this.metadata;
  }

  getKPIs() {
    return {
      spatialNodesCount: this.spatialNodes.length, // 255
      observedNodesCount: this.metadata?.coverage?.observed_nodes || 98,
      observationRecordsCount: this.methaneObservations.length, // 226
      evaluationPredictionsCount: this.predictions.length, // 720
      observationPeriods: this.metadata?.coverage?.observation_periods || ['2019-05', '2021-02', '2021-08', '2023-11'],
      modelCheckpointsCount: 15, // 3 folds * 5 seeds
      studyArea: 'India (7°N - 37°N, 69°E - 97°E, 2° resolution)',
      modelName: this.metadata?.model_name || 'Original MLP Reference Model',
      modelStatus: this.metadata?.model_status || 'Experimental reference model',
      scientificWarnings: this.metadata?.scientific_warnings || []
    };
  }

  getSpatialNodes(period = null) {
    if (!period || period === 'ALL') {
      return this.spatialNodes;
    }
    // Augment nodes with observation for the requested period
    const obsMap = new Map();
    this.methaneObservations
      .filter(o => o.observation_period === period)
      .forEach(o => obsMap.set(o.node_id, o));

    return this.spatialNodes.map(node => {
      const obs = obsMap.get(node.node_id);
      return {
        ...node,
        observed_in_period: !!obs,
        observation: obs || null
      };
    });
  }

  getSpatialGeoJSON(period = null) {
    if (!this.spatialGeoJSON) return null;
    if (!period || period === 'ALL') {
      return this.spatialGeoJSON;
    }

    const obsMap = new Map();
    this.methaneObservations
      .filter(o => o.observation_period === period)
      .forEach(o => obsMap.set(o.node_id, o));

    return {
      ...this.spatialGeoJSON,
      features: this.spatialGeoJSON.features.map(f => {
        const nodeId = f.properties.node_id;
        const obs = obsMap.get(nodeId);
        return {
          ...f,
          properties: {
            ...f.properties,
            observed_in_period: !!obs,
            methane_median_ppb: obs ? obs.methane_median_ppb : null,
            methane_mean_ppb: obs ? obs.methane_mean_ppb : null,
            methane_std_ppb: obs ? obs.methane_std_ppb : null,
            T2M: obs ? obs.T2M : null,
            PRECTOTCORR: obs ? obs.PRECTOTCORR : null,
            RH2M: obs ? obs.RH2M : null,
            WS10M: obs ? obs.WS10M : null
          }
        };
      })
    };
  }

  getIndiaBoundary() {
    return this.indiaBoundary;
  }

  getMethaneObservations({ period, region, minCH4, maxCH4, limit = 1000, page = 1 } = {}) {
    let results = [...this.methaneObservations];

    if (period && period !== 'ALL') {
      results = results.filter(r => r.observation_period === period);
    }

    if (region && region !== 'ALL') {
      results = results.filter(r => this.classifyRegion(r.latitude, r.longitude) === region);
    }

    if (minCH4 !== undefined && !isNaN(minCH4)) {
      results = results.filter(r => r.methane_median_ppb >= parseFloat(minCH4));
    }

    if (maxCH4 !== undefined && !isNaN(maxCH4)) {
      results = results.filter(r => r.methane_median_ppb <= parseFloat(maxCH4));
    }

    const total = results.length;
    const startIndex = (page - 1) * limit;
    const paginated = results.slice(startIndex, startIndex + parseInt(limit));

    return {
      total,
      page: parseInt(page),
      limit: parseInt(limit),
      records: paginated
    };
  }

  classifyRegion(lat, lon) {
    if (lat >= 25.0) {
      return lon < 82.0 ? 'North_West' : 'North_East';
    } else if (lat >= 15.0) {
      return lon < 82.0 ? 'Central_West' : 'Central_East';
    } else {
      return lon < 82.0 ? 'South_West' : 'South_East';
    }
  }

  getPredictions({ fold, seed, period, page = 1, limit = 1000 } = {}) {
    let results = [...this.predictions];

    if (fold) {
      results = results.filter(r => r.fold === parseInt(fold));
    }
    if (seed) {
      results = results.filter(r => r.seed === parseInt(seed));
    }
    if (period && period !== 'ALL') {
      results = results.filter(r => r.evaluation_period === period);
    }

    const total = results.length;
    const startIndex = (page - 1) * limit;
    const paginated = results.slice(startIndex, startIndex + parseInt(limit));

    return {
      total,
      page: parseInt(page),
      limit: parseInt(limit),
      records: paginated
    };
  }

  getFoldMetrics() {
    return {
      seedMetrics: this.foldSeedMetrics,
      foldSummary: this.foldSummary,
      comparisons: this.modelComparisons
    };
  }

  getChartData(period = 'ALL', region = 'ALL') {
    let obs = [...this.methaneObservations];
    let preds = [...this.predictions];

    if (period && period !== 'ALL') {
      obs = obs.filter(o => o.observation_period === period);
      preds = preds.filter(p => p.evaluation_period === period);
    }

    if (region && region !== 'ALL') {
      obs = obs.filter(o => this.classifyRegion(o.latitude, o.longitude) === region);
      preds = preds.filter(p => this.classifyRegion(p.latitude, p.longitude) === region);
    }

    // 1. Methane Concentration Distribution
    const ch4Values = obs.map(o => o.methane_median_ppb).sort((a, b) => a - b);

    // 2. Regional Methane Comparison
    const regionalData = {};
    const regions = ['North_West', 'North_East', 'Central_West', 'Central_East', 'South_West', 'South_East'];
    regions.forEach(r => regionalData[r] = []);
    this.methaneObservations.forEach(o => {
      const reg = this.classifyRegion(o.latitude, o.longitude);
      if (regionalData[reg]) {
        regionalData[reg].push(o.methane_median_ppb);
      }
    });

    // 3. Observations per Period
    const periodsCount = {
      '2019-05': 0,
      '2021-02': 0,
      '2021-08': 0,
      '2023-11': 0
    };
    this.methaneObservations.forEach(o => {
      if (periodsCount[o.observation_period] !== undefined) {
        periodsCount[o.observation_period]++;
      }
    });

    // 4. Climate Variables Distribution
    const climateDist = {
      T2M: obs.map(o => o.T2M),
      PRECTOTCORR: obs.map(o => o.PRECTOTCORR),
      RH2M: obs.map(o => o.RH2M),
      WS10M: obs.map(o => o.WS10M)
    };

    // 5. Observed vs Predicted (from predictions)
    // To avoid overplotting 720 points on single plot if seed=42 or default seed is desired,
    // let's take seed 42 or average across seeds per node
    const obsVsPred = preds.filter(p => p.seed === 42).map(p => ({
      node_id: p.node_id,
      actual: p.actual_methane_ppb,
      predicted: p.predicted_methane_ppb,
      fold: p.fold,
      error: p.error_ppb
    }));

    // 6. Fold Evaluation Metrics (MAE, RMSE, R2, Bias)
    const foldMetrics = this.foldSummary;

    // 7. Seed-wise stability
    const seedStability = this.foldSeedMetrics;

    // 8. Error Distribution
    const errorDist = preds.map(p => p.error_ppb).sort((a, b) => a - b);

    // 9. Spatial coverage
    const observedNodeIds = new Set(this.methaneObservations.map(o => o.node_id));
    const coverageStats = {
      totalNodes: this.spatialNodes.length, // 255
      observedNodesCount: observedNodeIds.size, // 98
      unobservedNodesCount: this.spatialNodes.length - observedNodeIds.size, // 157
      periodBreakdown: periodsCount
    };

    return {
      ch4Values,
      regionalData,
      periodsCount,
      climateDist,
      obsVsPred,
      foldMetrics,
      seedStability,
      errorDist,
      coverageStats
    };
  }

  getRegionalStats() {
    const regions = [
      { id: 'North_West', name: 'Northwest', criteria: 'Lat ≥ 25°N, Lon < 82°E' },
      { id: 'North_East', name: 'Northeast', criteria: 'Lat ≥ 25°N, Lon ≥ 82°E' },
      { id: 'Central_West', name: 'Central-West', criteria: '15°N ≤ Lat < 25°N, Lon < 82°E' },
      { id: 'Central_East', name: 'Central-East', criteria: '15°N ≤ Lat < 25°N, Lon ≥ 82°E' },
      { id: 'South_West', name: 'Southwest', criteria: 'Lat < 15°N, Lon < 82°E' },
      { id: 'South_East', name: 'Southeast', criteria: 'Lat < 15°N, Lon ≥ 82°E' }
    ];

    return regions.map(reg => {
      const matchingObs = this.methaneObservations.filter(o => this.classifyRegion(o.latitude, o.longitude) === reg.id);
      const matchingNodes = this.spatialNodes.filter(n => this.classifyRegion(n.latitude, n.longitude) === reg.id);
      const ch4Vals = matchingObs.map(o => o.methane_median_ppb);
      
      const count = ch4Vals.length;
      const isUnavailable = count === 0;

      let mean = null;
      let median = null;
      let min = null;
      let max = null;

      if (!isUnavailable) {
        mean = ch4Vals.reduce((a, b) => a + b, 0) / count;
        const sorted = [...ch4Vals].sort((a, b) => a - b);
        median = sorted[Math.floor(count / 2)];
        min = sorted[0];
        max = sorted[count - 1];
      }

      return {
        id: reg.id,
        name: reg.name,
        criteria: reg.criteria,
        totalGridNodes: matchingNodes.length,
        observationCount: count,
        status: isUnavailable ? 'UNAVAILABLE_OBSERVATIONS' : 'OBSERVED',
        note: isUnavailable 
          ? 'Zero satellite pixels met QA threshold (≥ 0.50) in this pilot dataset. Represented as unavailable, never zero.' 
          : 'Observations recorded across available pilot periods.',
        stats: isUnavailable ? null : {
          mean_ppb: parseFloat(mean.toFixed(2)),
          median_ppb: parseFloat(median.toFixed(2)),
          min_ppb: parseFloat(min.toFixed(2)),
          max_ppb: parseFloat(max.toFixed(2))
        }
      };
    });
  }

  getProjectFindings() {
    return {
      title: 'What We Discovered: Environmental Findings & Honest Limitations',
      pilotDatasetMetrics: {
        qualityFilteredPixels: 73045,
        spatialGridNodes: 255,
        methaneNodeMonthRecords: 226,
        uniqueObservedNodes: 98,
        availableObservationMonths: 4,
        periods: ['May 2019', 'February 2021', 'August 2021', 'November 2023']
      },
      findings: [
        {
          id: 'spatial_heterogeneity',
          title: 'Unequal Satellite Observation Distribution',
          summary: 'Observations are clustered primarily in Northern and Central corridors, reflecting orbital track geometry and seasonal cloud patterns.',
          details: 'Of 255 spatial lattice nodes, only 98 have at least one observation meeting the QA ≥ 0.50 threshold across the 4 snapshot months. Southeast India has 0 valid soundings in this pilot release.'
        },
        {
          id: 'monsoon_filtering_gap',
          title: 'Monsoon Cloud Masking Impact (August 2021)',
          summary: 'Intense monsoon convection and optical cloud thickness severely reduce valid soundings in August 2021.',
          details: 'Only 11 nodes passed quality filtering in August 2021 compared to 82 nodes in May 2019 and 67 nodes in February 2021. This demonstrates why continuous monthly monitoring requires advanced interpolation or microwave sensing.'
        },
        {
          id: 'climate_coupling',
          title: 'Atmospheric Meteorology Coupling',
          summary: 'Surface air temperature (T2M) and wind dispersion (WS10M) show consistent physical relationships with column concentration.',
          details: 'Atmospheric methane concentration (XCH4) exhibits seasonal variability coupled to synoptic meteorological shifts, but surface correlations do not prove direct causality.'
        },
        {
          id: 'pilot_nature',
          title: 'Pilot Character: Not a Continuous National Record',
          summary: 'This dataset represents four discrete temporal snapshots, not an unbroken monthly time series.',
          details: 'Data users must not extrapolate continuous nationwide trends from four isolated snapshot periods.'
        }
      ],
      limitations: [
        'Atmospheric column concentration (ppb) is not surface emission flux (kg/hr).',
        'Spatial resolution is 2° (~220 km), representing regional bulk atmospheric mixing rather than point sources.',
        'Machine learning models are strictly experimental references with negative R² out-of-fold and do not demonstrate operational forecasting skill.'
      ]
    };
  }

  getMethodology() {
    return {
      title: 'Project Scientific Methodology',
      steps: [
        { step: 1, title: 'Satellite Earth Observation', desc: 'Sentinel-5P TROPOMI acquires total column soundings in the SWIR spectral band.' },
        { step: 2, title: 'Stringent Quality Filtering', desc: 'Soundings with QA value < 0.50 (heavy clouds, snow/ice, high aerosol optical thickness) are discarded. 73,045 quality-filtered pixels retained.' },
        { step: 3, title: 'Spatial Grid Discretization', desc: 'India is mapped onto a 2° regular spherical lattice (255 nodes, 7°N–37°N, 69°E–97°E).' },
        { step: 4, title: 'Meteorological Integration', desc: 'Collocated with NASA POWER surface reanalysis (T2M, PRECTOTCORR, RH2M, WS10M).' },
        { step: 5, title: 'Spatial Graph Topology', desc: 'Constructed spatial adjacency graph capturing geographical neighbor relationships and geodesic distances.' },
        { step: 6, title: 'Exploratory Environmental Analysis', desc: 'Evaluating regional distributions, seasonal shifts, and monsoon observation gaps.' },
        { step: 7, title: 'Machine Learning Experiments', desc: 'Benchmarking Multi-Layer Perceptrons, Distance-Weighted GCNs, and ablation baselines.' },
        { step: 8, title: 'Rigorous Chronological Evaluation', desc: 'Evaluating across 3 temporal expanding folds and 5 random seeds to test out-of-sample stability.' },
        { step: 9, title: 'Interactive Environmental Dissemination', desc: 'Publishing open datasets, interactive 3D visualizations, and grounded AI assistant for public education.' }
      ]
    };
  }
}

module.exports = new DatasetService();
