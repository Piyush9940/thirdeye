/**
 * NASA Earth Systems Trend Detective
 * Hotspot Controller
 */

const analysisService = require('../services/analysis.service');

exports.getHotspots = (req, res) => {
  try {
    const { period = '2023-11' } = req.query;
    const hotspots = analysisService.getHotspots(period);
    res.json({ success: true, count: hotspots.length, data: hotspots });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
