/**
 * NASA Earth Systems Trend Detective
 * Forecasting & Prediction Routes
 */

const express = require('express');
const router = express.Router();
const forecastCtrl = require('../controllers/forecast.controller');

router.post('/predictions/infer', forecastCtrl.infer);
router.get('/predictions/comparison', forecastCtrl.getEvaluationComparison);

module.exports = router;
