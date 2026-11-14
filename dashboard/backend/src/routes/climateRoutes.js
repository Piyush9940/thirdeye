const express = require('express');
const router = express.Router();
const climateController = require('../controllers/climateController');

router.get('/series', climateController.getSeries);
router.get('/summary', climateController.getSummary);
router.get('/observations', climateController.getObservations);

module.exports = router;
