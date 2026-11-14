/**
 * NASA Earth Systems Trend Detective
 * Forecasting & Live Inference Controller
 */

const pythonService = require('../services/python-client.service');
const datasetService = require('../services/dataset.service');

exports.infer = async (req, res) => {
  try {
    const { features, fold = 1, seed = 42 } = req.body;

    if (!features || !Array.isArray(features)) {
      return res.status(400).json({
        success: false,
        message: 'Must supply an array of 8 numerical features: [T2M, PRECTOTCORR, RH2M, WS10M, latitude, longitude, month_sin, month_cos].'
      });
    }

    const prediction = await pythonService.predict({ features, fold, seed });
    res.json({
      success: true,
      data: prediction
    });
  } catch (err) {
    res.status(500).json({
      success: false,
      message: err.message
    });
  }
};

exports.getEvaluationComparison = (req, res) => {
  try {
    const metrics = datasetService.getFoldMetrics();
    res.json({
      success: true,
      data: {
        model_name: "Original MLP Reference Model",
        model_status: "Experimental Reference Model — Not Production Approved",
        summary: metrics.foldSummary,
        seedMetrics: metrics.seedMetrics,
        comparisons: metrics.comparisons,
        limitations: [
          "Only four observation months available (2019-05, 2021-02, 2021-08, 2023-11).",
          "August 2021 has only 11 observed evaluation nodes.",
          "Fold 3 has 56 of 66 test nodes previously observed during training.",
          "Negative R2 indicates performance worse than evaluation-set mean baseline.",
          "Negative bias indicates systematic underprediction.",
          "No reliable operational forecasting skill has been demonstrated."
        ]
      }
    });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
