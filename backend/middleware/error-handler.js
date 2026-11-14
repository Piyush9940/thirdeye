/**
 * NASA Earth Systems Trend Detective
 * Error Handling Middleware
 */

module.exports = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  console.error(`[Global Error Handler] [${req.method} ${req.url}]:`, err.message);

  res.status(statusCode).json({
    success: false,
    message: err.message || 'An unexpected error occurred.',
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
};
