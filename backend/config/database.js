/**
 * NASA Earth Systems Trend Detective
 * Database Connection & Dual-Mode Adapter
 */

const mongoose = require('mongoose');
const env = require('./environment');

let isConnected = false;

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(env.MONGODB_URI, {
      serverSelectionTimeoutMS: 2500, // Quick timeout to prevent blocking if local mongod is absent
    });
    isConnected = true;
    console.log(`[MongoDB] Connected to database: ${conn.connection.host}/${conn.connection.name}`);
    return true;
  } catch (err) {
    isConnected = false;
    console.warn(`[MongoDB] Offline or unreachable (${err.message}). Activating local memory/JSON fallback mode for user state.`);
    return false;
  }
};

const getDBStatus = () => ({
  connected: isConnected,
  mode: isConnected ? 'mongodb' : 'local_fallback',
  uri: env.MONGODB_URI.replace(/\/\/.*@/, '//***:***@') // Mask credentials if present
});

module.exports = {
  connectDB,
  getDBStatus,
  get isConnected() { return isConnected; }
};
