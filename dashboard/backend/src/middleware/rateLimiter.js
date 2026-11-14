const { error } = require('../utils/responseFormatter');

const hits = new Map();

/**
 * In-memory sliding window rate limiter
 * @param {number} maxRequests Max calls in window (default 120)
 * @param {number} windowMs Time window in ms (default 60s)
 */
const rateLimiter = (maxRequests = 120, windowMs = 60000) => {
  return (req, res, next) => {
    let ip = '127.0.0.1';
    try {
      ip = req.headers['x-forwarded-for'] || (req.socket && req.socket.remoteAddress) || req.ip || '127.0.0.1';
    } catch (_) {
      ip = '127.0.0.1';
    }
    const now = Date.now();

    if (!hits.has(ip)) {
      hits.set(ip, []);
    }

    const timestamps = hits.get(ip).filter(t => now - t < windowMs);
    if (timestamps.length >= maxRequests) {
      return error(res, 'Too many requests. Please slow down and try again shortly.', 429);
    }

    timestamps.push(now);
    hits.set(ip, timestamps);
    next();
  };
};

module.exports = rateLimiter;
