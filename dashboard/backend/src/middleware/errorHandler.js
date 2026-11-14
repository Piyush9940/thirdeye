const logger = require('../utils/logger');
const { error } = require('../utils/responseFormatter');

const errorHandler = (err, req, res, next) => {
  logger.error(`[Express] Unhandled Error on ${req.method} ${req.originalUrl}: ${err.message}`, err.stack);

  const status = err.statusCode || err.status || 500;
  const message = err.message || 'An unexpected internal error occurred.';

  return error(res, message, status, err.stack);
};

module.exports = errorHandler;
