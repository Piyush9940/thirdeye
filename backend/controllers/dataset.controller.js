/**
 * NASA Earth Systems Trend Detective
 * Scientific Dataset & Telemetry Controller
 */

const path = require('path');
const fs = require('fs');
const datasetService = require('../services/dataset.service');

exports.getKPIs = (req, res) => {
  try {
    const kpis = datasetService.getKPIs();
    res.json({ success: true, data: kpis });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getMetadata = (req, res) => {
  try {
    const metadata = datasetService.getMetadata();
    res.json({ success: true, data: metadata });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getCharts = (req, res) => {
  try {
    const { period = 'ALL', region = 'ALL' } = req.query;
    const chartData = datasetService.getChartData(period, region);
    res.json({ success: true, data: chartData });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getSpatialNodes = (req, res) => {
  try {
    const { period } = req.query;
    const nodes = datasetService.getSpatialNodes(period);
    res.json({ success: true, count: nodes.length, data: nodes });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getSpatialGeoJSON = (req, res) => {
  try {
    const { period } = req.query;
    const geojson = datasetService.getSpatialGeoJSON(period);
    if (!geojson) {
      return res.status(404).json({ success: false, message: 'GeoJSON not found.' });
    }
    res.json(geojson);
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getIndiaBoundary = (req, res) => {
  try {
    const boundary = datasetService.getIndiaBoundary();
    if (!boundary) {
      return res.status(404).json({ success: false, message: 'India boundary GeoJSON not found.' });
    }
    res.json(boundary);
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getMethaneObservations = (req, res) => {
  try {
    const { period, region, minCH4, maxCH4, limit = 1000, page = 1 } = req.query;
    const result = datasetService.getMethaneObservations({ period, region, minCH4, maxCH4, limit, page });
    res.json({ success: true, ...result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getMLPPredictions = (req, res) => {
  try {
    const { fold, seed, period, page = 1, limit = 1000 } = req.query;
    const result = datasetService.getPredictions({ fold, seed, period, page, limit });
    res.json({ success: true, ...result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getModelMetrics = (req, res) => {
  try {
    const metrics = datasetService.getFoldMetrics();
    res.json({ success: true, data: metrics });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getClimateData = (req, res) => {
  try {
    const obs = datasetService.getMethaneObservations({ limit: 10000 }).records;
    const climatePoints = obs.map(o => ({
      node_id: o.node_id,
      latitude: o.latitude,
      longitude: o.longitude,
      observation_period: o.observation_period,
      T2M: o.T2M,
      PRECTOTCORR: o.PRECTOTCORR,
      RH2M: o.RH2M,
      WS10M: o.WS10M,
      methane_median_ppb: o.methane_median_ppb
    }));
    res.json({ success: true, count: climatePoints.length, data: climatePoints });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getRegionalStats = (req, res) => {
  try {
    const regions = datasetService.getRegionalStats();
    res.json({ success: true, count: regions.length, data: regions });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getProjectFindings = (req, res) => {
  try {
    const findings = datasetService.getProjectFindings();
    res.json({ success: true, data: findings });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.getMethodology = (req, res) => {
  try {
    const methodology = datasetService.getMethodology();
    res.json({ success: true, data: methodology });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};

exports.downloadFile = (req, res) => {
  try {
    const { filename } = req.params;
    const allowedFiles = [
      'spatial_nodes.csv', 'spatial_nodes.json', 'spatial_nodes.geojson',
      'methane_observations.csv', 'methane_observations.json',
      'mlp_predictions.csv', 'mlp_predictions.json',
      'fold_seed_metrics.csv', 'fold_seed_metrics.json',
      'fold_summary.csv', 'fold_summary.json',
      'dashboard_metadata.json', 'india_adm0.geojson'
    ];

    if (!allowedFiles.includes(filename)) {
      return res.status(400).json({ success: false, message: 'Invalid or unauthorized export filename requested.' });
    }

    let filePath = path.join(datasetService.baseDir, filename);
    if (filename === 'india_adm0.geojson') {
      filePath = path.join(datasetService.geoDir, filename);
    }

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ success: false, message: 'Export file not found on server.' });
    }

    res.download(filePath, filename);
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
