/**
 * NASA Earth Systems Trend Detective
 * In-Memory Sliding-Window Rate Limiter
 */

const requests = new Map();

module.exports = (options = { windowMs: 60000, max: 120 }) => {
  return (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress || 'unknown';
    const now = Date.now();
    const windowStart = now - options.windowMs;

    let timestamps = requests.get(ip) || [];
    timestamps = timestamps.filter(t => t > windowStart);

    if (timestamps.length >= options.max) {
      return res.status(429).json({
        success: false,
        message: 'Too many requests. Please slow down and try again shortly.'
      });
    }

    timestamps.push(now);
    requests.set(ip, timestamps);
    next();
  };
};
