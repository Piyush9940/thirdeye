/**
 * NASA Earth Systems Trend Detective
 * Request Validation Middleware
 */

exports.validateInferenceInput = (req, res, next) => {
  const { features, fold, seed } = req.body;

  if (!features || !Array.isArray(features) || features.length !== 8) {
    return res.status(400).json({
      success: false,
      message: 'Features must be an array of exactly 8 finite numerical values.'
    });
  }

  for (let i = 0; i < features.length; i++) {
    if (typeof features[i] !== 'number' || isNaN(features[i])) {
      return res.status(400).json({
        success: false,
        message: `Feature at index ${i} is not a valid number.`
      });
    }
  }

  if (fold && ![1, 2, 3].includes(parseInt(fold))) {
    return res.status(400).json({
      success: false,
      message: 'Fold must be 1, 2, or 3.'
    });
  }

  if (seed && ![7, 21, 42, 77, 123].includes(parseInt(seed))) {
    return res.status(400).json({
      success: false,
      message: 'Seed must be one of: 7, 21, 42, 77, 123.'
    });
  }

  next();
};
