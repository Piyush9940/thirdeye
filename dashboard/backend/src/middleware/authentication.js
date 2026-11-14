const jwt = require('jsonwebtoken');
const env = require('../config/environment');

const authenticateOptional = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    req.user = { userId: 'guest_user', role: 'guest' };
    return next();
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, env.JWT_SECRET);
    req.user = decoded;
  } catch (err) {
    req.user = { userId: 'guest_user', role: 'guest' };
  }
  next();
};

const authenticateRequired = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: 'Authentication required.' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ success: false, message: 'Invalid or expired authorization token.' });
  }
};

module.exports = {
  authenticateOptional,
  authenticateRequired
};
