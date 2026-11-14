const express = require('express');
const router = express.Router();
const reportController = require('../controllers/reportController');
const { authenticateOptional } = require('../middleware/authentication');

router.post('/generate', authenticateOptional, reportController.postGenerate);
router.get('/history', authenticateOptional, reportController.getHistory);
router.get('/:id', reportController.getById);

module.exports = router;
