const express = require('express');
const router = express.Router();
const mapController = require('../controllers/mapController');
const metadataController = require('../controllers/metadataController');

router.get('/nodes', mapController.getNodes);
router.get('/edges', mapController.getEdges);
router.get('/regions', metadataController.getRegions);
router.get('/boundary', mapController.getBoundary);
router.get('/values', mapController.getSpatialValues);

module.exports = router;
