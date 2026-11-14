const { error } = require('../utils/responseFormatter');

const VALID_VARIABLES = ['T2M', 'PRECTOTCORR', 'RH2M', 'WS10M', 'CH4'];
const VALID_REGIONS = ['ALL', 'NW', 'NE', 'CW', 'CE', 'SW', 'SE', 'NORTH_WEST', 'NORTH_EAST', 'CENTRAL_WEST', 'CENTRAL_EAST', 'SOUTH_WEST', 'SOUTH_EAST', 'INDIA'];

const validateAnalysisRequest = (req, res, next) => {
  const { variable, region, start_date, end_date } = req.body || {};

  if (variable && !VALID_VARIABLES.includes(variable.toUpperCase())) {
    return error(res, `Invalid variable '${variable}'. Allowed values: ${VALID_VARIABLES.join(', ')}`, 400);
  }

  if (region && !VALID_REGIONS.includes(region.toUpperCase().replace(/\s+/g, '_'))) {
    return error(res, `Invalid region '${region}'. Allowed values: ALL, NW, NE, CW, CE, SW, SE`, 400);
  }

  const dateRegex = /^\d{4}-\d{2}$/;
  if (start_date && !dateRegex.test(start_date)) {
    return error(res, `Invalid start_date '${start_date}'. Format must be YYYY-MM (e.g. 2015-01).`, 400);
  }

  if (end_date && !dateRegex.test(end_date)) {
    return error(res, `Invalid end_date '${end_date}'. Format must be YYYY-MM (e.g. 2024-12).`, 400);
  }

  next();
};

module.exports = {
  validateAnalysisRequest
};
