const methaneService = require('../services/methaneService');
const { success } = require('../utils/responseFormatter');

const getSummary = (req, res, next) => {
  try {
    const summary = methaneService.getRegionalSummary();
    return success(res, summary, 'Methane pilot summary retrieved');
  } catch (err) {
    next(err);
  }
};

const getObservations = (req, res, next) => {
  try {
    const obs = methaneService.getObservations();
    return success(res, obs, 'Methane observations retrieved');
  } catch (err) {
    next(err);
  }
};

const getRegions = (req, res, next) => {
  try {
    const summary = methaneService.getRegionalSummary();
    return success(res, summary.regions, 'Methane regional coverage retrieved');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getSummary,
  getObservations,
  getRegions
};
