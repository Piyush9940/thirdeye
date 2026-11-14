const express = require('express');
const router = express.Router();
const mlController = require('../controllers/mlController');

router.get('/health', mlController.getHealth);
router.get('/metadata', mlController.getMetadata);
router.get('/metrics', mlController.getMetrics);
router.get('/predictions', mlController.getPredictions);
router.post('/inference', mlController.postInference);
router.post('/batch', mlController.postBatchInference);

module.exports = router;
