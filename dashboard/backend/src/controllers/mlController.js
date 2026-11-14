const mlService = require('../services/mlService');
const { success, error } = require('../utils/responseFormatter');

const getMetadata = async (req, res, next) => {
  try {
    const metrics = await mlService.getMetrics();
    return success(res, {
      model_name: metrics.model_name,
      status: metrics.status,
      architecture: metrics.architecture,
      training_context: metrics.training_context,
      features: metrics.features,
      target: metrics.target,
      key_findings: metrics.key_findings
    }, 'ML metadata retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getMetrics = async (req, res, next) => {
  try {
    const metrics = await mlService.getMetrics();
    return success(res, metrics, 'ML evaluation metrics retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const dataService = require('../services/dataService');

const getPredictions = async (req, res, next) => {
  try {
    const { fold, seed, live, limit } = req.query;

    if (live === 'true') {
      const prediction = await mlService.predict({
        fold: parseInt(fold || '1', 10),
        seed: parseInt(seed || '42', 10)
      });
      return success(res, prediction, 'Live CPU reference prediction executed');
    }

    // Retrieve historical evaluation predictions from release artifact
    let allPredictions = dataService.getMLPredictions();
    if (fold) {
      const fNum = parseInt(fold, 10);
      allPredictions = allPredictions.filter(p => p.fold === fNum);
    }
    if (seed) {
      const sNum = parseInt(seed, 10);
      allPredictions = allPredictions.filter(p => p.seed === sNum);
    }

    const maxItems = limit ? parseInt(limit, 10) : allPredictions.length;
    const sliced = allPredictions.slice(0, maxItems);

    return success(res, {
      total_records: allPredictions.length,
      returned_count: sliced.length,
      filter: { fold: fold || 'all', seed: seed || 'all' },
      predictions: sliced,
      scientific_notice: "720 historical cross-validation evaluation predictions across 3 chronological folds and 5 Monte Carlo seeds."
    }, 'Evaluation predictions retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const postInference = async (req, res, next) => {
  try {
    const { fold, seed, features } = req.body;
    const prediction = await mlService.predict({
      fold: parseInt(fold || '1', 10),
      seed: parseInt(seed || '42', 10),
      features: features || null
    });
    return success(res, prediction, 'Live CPU model inference executed successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getMetadata,
  getMetrics,
  getPredictions,
  postInference
};
