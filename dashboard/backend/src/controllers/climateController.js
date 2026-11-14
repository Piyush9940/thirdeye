const statisticalService = require('../services/statisticalService');
const { success, error } = require('../utils/responseFormatter');

const getSeries = async (req, res, next) => {
  try {
    const params = {
      variable: req.query.variable || 'T2M',
      region: req.query.region || 'ALL',
      node_id: req.query.node_id || null,
      start_date: req.query.start_date || '2015-01',
      end_date: req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getTrend(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, {
      variable: result.variable,
      units: result.units,
      region: result.region,
      time_series: result.time_series
    }, 'Climate series retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getSummary = async (req, res, next) => {
  try {
    const params = {
      variable: req.query.variable || 'T2M',
      region: req.query.region || 'ALL',
      start_date: req.query.start_date || '2015-01',
      end_date: req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getTrend(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, {
      variable: result.variable,
      units: result.units,
      region: result.region,
      summary_statistics: result.summary_statistics,
      ols: result.ols,
      mann_kendall: result.mann_kendall,
      sen_slope: result.sen_slope,
      interpretation: result.interpretation
    }, 'Climate summary retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getObservations = async (req, res, next) => {
  try {
    const params = {
      variable: req.query.variable || 'T2M',
      region: req.query.region || 'ALL',
      start_date: req.query.start_date || '2015-01',
      end_date: req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getTrend(params);
    return success(res, result.time_series || [], 'Observations retrieved');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getSeries,
  getSummary,
  getObservations
};
