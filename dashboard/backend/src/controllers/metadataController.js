const dataService = require('../services/dataService');
const { success } = require('../utils/responseFormatter');

const getMetadata = (req, res, next) => {
  try {
    const meta = dataService.getMetadata();
    const registry = dataService.getDatasetRegistry();
    return success(res, { ...meta, registry }, 'Project metadata & dataset registry retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getDatasetRegistry = (req, res, next) => {
  try {
    const reg = dataService.getDatasetRegistry();
    return success(res, reg, 'Central scientific dataset registry retrieved');
  } catch (err) {
    next(err);
  }
};

const getVariables = (req, res, next) => {
  try {
    const meta = dataService.getMetadata();
    return success(res, meta.variables, 'Available environmental variables retrieved');
  } catch (err) {
    next(err);
  }
};

const getRegions = (req, res, next) => {
  try {
    const meta = dataService.getMetadata();
    return success(res, meta.regions, 'Geographic regions retrieved');
  } catch (err) {
    next(err);
  }
};

const getCoverage = (req, res, next) => {
  try {
    const meta = dataService.getMetadata();
    return success(res, {
      geographic: meta.geographic_coverage,
      temporal: meta.temporal_coverage
    }, 'Dataset coverage specifications retrieved');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getMetadata,
  getVariables,
  getRegions,
  getCoverage,
  getDatasetRegistry
};
