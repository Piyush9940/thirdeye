/**
 * NASA Earth Systems Trend Detective
 * Authentication & User Routes
 */

const express = require('express');
const router = express.Router();
const storageService = require('../services/storage.service');
const authMiddleware = require('../middleware/auth');
const db = require('../config/database');

// Register
router.post('/auth/register', async (req, res) => {
  try {
    const { name, email, password, institution } = req.body;
    const result = await storageService.register({ name, email, password, institution });
    res.status(201).json({ success: true, ...result });
  } catch (err) {
    res.status(400).json({ success: false, message: err.message });
  }
});

// Login
router.post('/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const result = await storageService.login({ email, password });
    res.json({ success: true, ...result });
  } catch (err) {
    res.status(401).json({ success: false, message: err.message });
  }
});

// Current User Profile
router.get('/auth/me', authMiddleware, async (req, res) => {
  try {
    const user = await storageService.getUserById(req.user.id);
    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found.' });
    }
    res.json({ success: true, user });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// Save Analysis
router.post('/users/saved-analyses', authMiddleware, async (req, res) => {
  try {
    const list = await storageService.saveAnalysis(req.user.id, req.body);
    res.json({ success: true, data: list });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// Get Saved Analyses
router.get('/users/saved-analyses', authMiddleware, async (req, res) => {
  try {
    const list = await storageService.getSavedAnalyses(req.user.id);
    res.json({ success: true, data: list });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// Database status
router.get('/health', (req, res) => {
  res.json({
    status: 'online',
    platform: 'Earth Systems Trend Detective',
    version: '1.0.0',
    database: db.getDBStatus()
  });
});

module.exports = router;
