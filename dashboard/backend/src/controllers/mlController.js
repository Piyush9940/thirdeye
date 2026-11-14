const mlService = require('../services/mlService');
const dataService = require('../services/dataService');
const { success, error } = require('../utils/responseFormatter');

const getHealth = async (req, res, next) => {
  try {
    const health = await mlService.getHealth();
    return success(res, health, 'ML service health verified');
  } catch (err) {
    next(err);
  }
};

const getMetadata = async (req, res, next) => {
  try {
    const meta = await mlService.getMetadata();
    return success(res, meta, 'ML metadata retrieved successfully');
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
    return success(res, prediction, 'Live model inference executed successfully');
  } catch (err) {
    next(err);
  }
};

const postBatchInference = async (req, res, next) => {
  try {
    const { fold, seed, items } = req.body;
    if (!items || !Array.isArray(items) || items.length === 0) {
      return error(res, 'Batch items array is required.', 400);
    }
    const result = await mlService.predictBatch({
      fold: parseInt(fold || '1', 10),
      seed: parseInt(seed || '42', 10),
      items
    });
    return success(res, result, 'Batch model inference executed successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getHealth,
  getMetadata,
  getMetrics,
  getPredictions,
  postInference,
  postBatchInference
};
