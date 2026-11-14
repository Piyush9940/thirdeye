/**
 * NASA Earth Systems Trend Detective
 * Trend Analysis Controller
 */

const analysisService = require('../services/analysis.service');

exports.getTrends = (req, res) => {
  try {
    const trends = analysisService.getTrends();
    res.json({ success: true, data: trends });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
