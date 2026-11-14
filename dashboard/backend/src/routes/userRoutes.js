const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const { authenticateOptional } = require('../middleware/authentication');

router.get('/preferences', authenticateOptional, userController.getPreferences);
router.put('/preferences', authenticateOptional, userController.updatePreferences);

module.exports = router;
