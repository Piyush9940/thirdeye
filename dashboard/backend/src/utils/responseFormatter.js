/**
 * Standardized API Response Formatter
 */

const success = (res, data = {}, message = 'Operation completed successfully', statusCode = 200) => {
  return res.status(statusCode).json({
    success: true,
    message,
    data,
    timestamp: new Date().toISOString()
  });
};

const error = (res, message = 'An unexpected error occurred', statusCode = 500, details = null) => {
  return res.status(statusCode).json({
    success: false,
    message,
    details: details ? (process.env.NODE_ENV === 'development' ? details : undefined) : undefined,
    timestamp: new Date().toISOString()
  });
};

module.exports = {
  success,
  error
};
