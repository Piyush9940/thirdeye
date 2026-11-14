/**
 * NASA Earth Systems Trend Detective
 * Scientific Dataset Ingestion & Analysis Routes
 */

const express = require('express');
const router = express.Router();
const datasetController = require('../controllers/datasetController');
const fileUploadMiddleware = require('../middleware/fileUpload');

// Ingestion & Validation
router.post('/upload', fileUploadMiddleware, datasetController.uploadDataset);
router.post('/validate', fileUploadMiddleware, datasetController.validateDataset);

// Dataset Retrieval & Metadata
router.get('/', datasetController.getDatasets);
router.get('/:id', datasetController.getDatasetById);
router.get('/:id/metadata', datasetController.getDatasetMetadata);
router.delete('/:id', datasetController.deleteDataset);

// Dynamic Scientific Analysis on Ingested Data
router.post('/:id/analyze', datasetController.analyzeDataset);
router.post('/:id/compare', datasetController.compareDataset);

module.exports = router;
