/**
 * NASA Earth Systems Trend Detective
 * Dataset & Telemetry Routes
 */

const express = require('express');
const router = express.Router();
const datasetCtrl = require('../controllers/dataset.controller');

// Dashboard endpoints
router.get('/dashboard/stats', datasetCtrl.getKPIs);
router.get('/dashboard/overview', datasetCtrl.getKPIs); // Alias for overview
router.get('/dashboard/metadata', datasetCtrl.getMetadata);
router.get('/dashboard/charts', datasetCtrl.getCharts);

// Geospatial endpoints
router.get('/geo/nodes', datasetCtrl.getSpatialNodes);
router.get('/spatial/nodes', datasetCtrl.getSpatialNodes); // Alias for spatial nodes
router.get('/geo/nodes/geojson', datasetCtrl.getSpatialGeoJSON);
router.get('/geo/boundary', datasetCtrl.getIndiaBoundary);

// Scientific observation & model records
router.get('/methane/observations', datasetCtrl.getMethaneObservations);
router.get('/methane/regions', datasetCtrl.getRegionalStats);
router.get('/predictions/evaluations', datasetCtrl.getMLPPredictions);
router.get('/models/predictions', datasetCtrl.getMLPPredictions); // Alias
router.get('/models/experiments', datasetCtrl.getModelMetrics);
router.get('/models/metrics', datasetCtrl.getModelMetrics); // Alias
router.get('/climate/data', datasetCtrl.getClimateData);
router.get('/climate/observations', datasetCtrl.getClimateData); // Alias

// Project Findings & Methodology
router.get('/project/findings', datasetCtrl.getProjectFindings);
router.get('/research/methodology', datasetCtrl.getMethodology);

// Verified Dataset File Downloads
router.get('/data/download/:filename', datasetCtrl.downloadFile);

module.exports = router;
