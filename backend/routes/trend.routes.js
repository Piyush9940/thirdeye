/**
 * NASA Earth Systems Trend Detective
 * Trend Routes
 */

const express = require('express');
const router = express.Router();
const trendCtrl = require('../controllers/trend.controller');

router.get('/trends', trendCtrl.getTrends);

module.exports = router;
