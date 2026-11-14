/**
 * NASA Earth Systems Trend Detective
 * Analysis Routes
 */

const express = require('express');
const router = express.Router();
const analysisCtrl = require('../controllers/analysis.controller');

router.get('/analysis/overview', analysisCtrl.getOverview);

module.exports = router;
