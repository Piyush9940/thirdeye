/**
 * NASA Earth Systems Trend Detective
 * Analysis Controller
 */

const analysisService = require('../services/analysis.service');

exports.getOverview = (req, res) => {
  try {
    const data = analysisService.getMethaneOverview();
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
