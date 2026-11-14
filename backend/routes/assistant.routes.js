/**
 * NASA Earth Systems Trend Detective
 * AI Research Assistant Routes
 */

const express = require('express');
const router = express.Router();
const assistantService = require('../services/assistant.service');

router.post('/assistant/chat', async (req, res) => {
  try {
    const { message, history } = req.body;
    const result = await assistantService.answerQuestion(message, history);
    res.json({ success: true, ...result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
