/**
 * NASA Earth Systems Trend Detective
 * Hotspot Routes
 */

const express = require('express');
const router = express.Router();
const hotspotCtrl = require('../controllers/hotspot.controller');

router.get('/hotspots', hotspotCtrl.getHotspots);

module.exports = router;
