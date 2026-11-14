/**
 * NASA Earth Systems Trend Detective
 * Report Routes
 */

const express = require('express');
const router = express.Router();
const reportCtrl = require('../controllers/report.controller');

router.post('/reports/generate', reportCtrl.generateReport);

module.exports = router;
