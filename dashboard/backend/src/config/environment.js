const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const ROOT_DIR = path.resolve(__dirname, '../../../../');
const DASHBOARD_DIR = path.resolve(__dirname, '../../../');
const BACKEND_DIR = path.resolve(__dirname, '../../');
const PYTHON_DIR = path.resolve(BACKEND_DIR, 'python');
const FRONTEND_DIR = path.resolve(DASHBOARD_DIR, 'frontend');
const DATA_DIR = path.resolve(ROOT_DIR, 'data');

module.exports = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV || 'development',
  API_PREFIX: process.env.API_PREFIX || '/api',
  MONGODB_URI: process.env.MONGODB_URI || 'mongodb://localhost:27017/earth_trend_detective',
  JWT_SECRET: process.env.JWT_SECRET || 'nasa_space_apps_earth_trend_detective_secret_key_2026',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',
  PYTHON_PATH: process.env.PYTHON_PATH || 'python',

  // AI Keys & Configuration
  AI_PROVIDER: process.env.AI_PROVIDER || (process.env.GEMINI_API_KEY ? 'gemini' : (process.env.OPENAI_API_KEY ? 'openai' : 'grounded')),
  GEMINI_API_KEY: process.env.GEMINI_API_KEY || '',
  GEMINI_MODEL: process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite',
  GROQ_API_KEY: process.env.GROQ_API_KEY || '',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  OPENAI_MODEL: process.env.OPENAI_MODEL || 'gpt-4o-mini',

  // Standalone ML Inference Service (FastAPI / Render)
  MODEL_SERVICE_URL: process.env.MODEL_SERVICE_URL || '',
  MODEL_SERVICE_TIMEOUT_MS: parseInt(process.env.MODEL_SERVICE_TIMEOUT_MS || '10000', 10),
  MODEL_SERVICE_API_KEY: process.env.MODEL_SERVICE_API_KEY || '',

  // Paths
  PATHS: {
    ROOT_DIR,
    DASHBOARD_DIR,
    BACKEND_DIR,
    FRONTEND_DIR,
    PYTHON_DIR,
    DATA_DIR,
    REPORTS_DIR: path.resolve(BACKEND_DIR, 'public/reports'),
    UPLOADS_DIR: path.resolve(BACKEND_DIR, 'uploads'),
    STORE_FILE: path.resolve(BACKEND_DIR, 'data/store.json'),
    STATISTICAL_ENGINE: path.resolve(PYTHON_DIR, 'statistical_engine.py'),
    DATASET_PROCESSOR: path.resolve(PYTHON_DIR, 'dataset_processor.py'),
    ML_INFERENCE: path.resolve(PYTHON_DIR, 'ml_inference.py'),
    REPORT_GENERATOR: path.resolve(PYTHON_DIR, 'report_generator.py'),
    NODES_CSV: path.resolve(DATA_DIR, 'processed/gnn_dataset/spherical_graph_nodes.csv'),
    EDGES_CSV: path.resolve(DATA_DIR, 'processed/gnn_dataset/spherical_graph_edges.csv'),
    EDGES_BIDI_CSV: path.resolve(DATA_DIR, 'processed/gnn_dataset/spherical_graph_edges_bidirectional.csv'),
    NASA_POWER_GRID_2DEG: path.resolve(DATA_DIR, 'processed/nasa_power_grid_2deg.parquet'),
    NASA_POWER_MERGED: path.resolve(DATA_DIR, 'processed/nasa_power_merged.parquet'),
    METHANE_PILOT_PARQUET: path.resolve(DATA_DIR, 'processed/gnn_dataset/methane_climate_node_month_pilot.parquet'),
    INDIA_GEOJSON: path.resolve(DATA_DIR, 'external/india_boundary/india_adm0.geojson'),
    DASHBOARD_EXPORTS: path.resolve(DATA_DIR, 'processed/dashboard_exports'),
    MODEL_RELEASE_MANIFEST: path.resolve(ROOT_DIR, 'reports/final_model_release/model_release_manifest.json'),
    MODEL_RELEASE_REPORT: path.resolve(ROOT_DIR, 'reports/final_model_release/FINAL_MODEL_RELEASE_REPORT.md'),
    PRODUCTION_PREDICTOR: path.resolve(ROOT_DIR, 'models/production_reference/inference/predictor.py')
  }
};
