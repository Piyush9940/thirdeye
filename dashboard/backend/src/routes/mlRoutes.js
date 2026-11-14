const express = require('express');
const router = express.Router();
const mlController = require('../controllers/mlController');

router.get('/metadata', mlController.getMetadata);
router.get('/metrics', mlController.getMetrics);
router.get('/predictions', mlController.getPredictions);
router.post('/inference', mlController.postInference);

module.exports = router;
