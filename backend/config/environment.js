/**
 * NASA Earth Systems Trend Detective
 * Environment Configuration
 */

const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

module.exports = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV || 'development',
  MONGODB_URI: process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/nasa_earth_detective',
  JWT_SECRET: process.env.JWT_SECRET || 'nasa_space_apps_earth_detective_secret_key_2026',
  GEMINI_API_KEY: process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || '',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  AI_PROVIDER: process.env.AI_PROVIDER || 'gemini', // 'gemini', 'openai', 'heuristic'
  PYTHON_PATH: path.resolve(__dirname, '../../.venv/Scripts/python.exe'),
  PROJECT_ROOT: path.resolve(__dirname, '../../'),
  DATA_ROOT: path.resolve(__dirname, '../data/processed/dashboard_exports')
};
