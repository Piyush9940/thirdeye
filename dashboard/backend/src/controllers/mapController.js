const dataService = require('../services/dataService');
const statisticalService = require('../services/statisticalService');
const { success, error } = require('../utils/responseFormatter');

const getNodes = (req, res, next) => {
  try {
    const nodes = dataService.getSpatialNodes();
    return success(res, nodes, 'Spatial nodes retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getEdges = (req, res, next) => {
  try {
    const edges = dataService.getSpatialEdges();
    return success(res, edges, 'Spherical graph edges retrieved successfully');
  } catch (err) {
    next(err);
  }
};

const getBoundary = (req, res, next) => {
  try {
    const boundary = dataService.getBoundaryGeoJSON();
    if (!boundary) {
      return error(res, 'Boundary GeoJSON not available', 404);
    }
    return res.json(boundary);
  } catch (err) {
    next(err);
  }
};

const getSpatialValues = async (req, res, next) => {
  try {
    const params = {
      variable: req.query.variable || 'T2M',
      start_date: req.query.start_date || '2015-01',
      end_date: req.query.end_date || '2024-12'
    };

    const result = await statisticalService.getSpatialValues(params);
    if (result.error) {
      return error(res, result.error, 400);
    }
    return success(res, result, 'Spatial node values retrieved successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getNodes,
  getEdges,
  getBoundary,
  getSpatialValues
};
