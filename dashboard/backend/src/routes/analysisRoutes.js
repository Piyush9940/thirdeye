const express = require('express');
const router = express.Router();
const analysisController = require('../controllers/analysisController');
const { validateAnalysisRequest } = require('../middleware/requestValidator');
const { authenticateOptional } = require('../middleware/authentication');

router.post('/trend', validateAnalysisRequest, analysisController.postTrend);
router.get('/trend', validateAnalysisRequest, analysisController.postTrend);

router.post('/seasonal', validateAnalysisRequest, analysisController.postSeasonal);
router.get('/seasonal', validateAnalysisRequest, analysisController.postSeasonal);

router.post('/compare', validateAnalysisRequest, analysisController.postCompare);
router.get('/compare', validateAnalysisRequest, analysisController.postCompare);

router.get('/history', authenticateOptional, analysisController.getHistory);
router.post('/save', authenticateOptional, analysisController.saveAnalysis);

module.exports = router;
