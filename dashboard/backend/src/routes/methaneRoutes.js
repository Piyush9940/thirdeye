const express = require('express');
const router = express.Router();
const methaneController = require('../controllers/methaneController');

router.get('/summary', methaneController.getSummary);
router.get('/observations', methaneController.getObservations);
router.get('/regions', methaneController.getRegions);

module.exports = router;
