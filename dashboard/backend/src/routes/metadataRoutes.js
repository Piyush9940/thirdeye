const express = require('express');
const router = express.Router();
const metadataController = require('../controllers/metadataController');

router.get('/', metadataController.getMetadata);
router.get('/variables', metadataController.getVariables);
router.get('/regions', metadataController.getRegions);
router.get('/coverage', metadataController.getCoverage);
router.get('/registry', metadataController.getDatasetRegistry);

module.exports = router;
