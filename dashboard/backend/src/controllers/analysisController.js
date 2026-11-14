const statisticalService = require('../services/statisticalService');
const { localStore } = require('../config/database');
const { success, error } = require('../utils/responseFormatter');

const postTrend = async (req, res, next) => {
  try {
    const params = {
      variable: req.body.variable || req.query.variable || 'T2M',
      region: req.body.region || req.query.region || 'ALL',
      node_id: req.body.node_id || req.query.node_id || null,
      start_date: req.body.start_date || req.query.start_date || '2015-01',
      end_date: req.body.end_date || req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getTrend(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, result, 'Statistical trend calculated successfully');
  } catch (err) {
    next(err);
  }
};

const postSeasonal = async (req, res, next) => {
  try {
    const params = {
      variable: req.body.variable || req.query.variable || 'T2M',
      region: req.body.region || req.query.region || 'ALL',
      start_date: req.body.start_date || req.query.start_date || '2015-01',
      end_date: req.body.end_date || req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getSeasonal(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, result, 'Seasonal climatological analysis calculated successfully');
  } catch (err) {
    next(err);
  }
};

const postCompare = async (req, res, next) => {
  try {
    const params = {
      variable: req.body.variable || req.query.variable || 'T2M',
      start_date: req.body.start_date || req.query.start_date || '2015-01',
      end_date: req.body.end_date || req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getCompare(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, result, 'Cross-regional trend comparison generated successfully');
  } catch (err) {
    next(err);
  }
};

const getHistory = (req, res, next) => {
  try {
    const userId = req.user?.userId || 'anonymous';
    const history = localStore.find('savedAnalyses', a => a.userId === userId || !a.userId);
    return success(res, history, 'Analysis history retrieved');
  } catch (err) {
    next(err);
  }
};

const saveAnalysis = (req, res, next) => {
  try {
    const { title, variable, region, dateRange, statisticalResults } = req.body;
    const userId = req.user?.userId || 'anonymous';

    const saved = localStore.insert('savedAnalyses', {
      title: title || `${variable} in ${region}`,
      variable,
      region,
      dateRange,
      statisticalResults,
      userId
    });

    return success(res, saved, 'Analysis saved successfully', 201);
  } catch (err) {
    next(err);
  }
};

module.exports = {
  postTrend,
  postSeasonal,
  postCompare,
  getHistory,
  saveAnalysis
};
