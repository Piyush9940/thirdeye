/**
 * NASA Earth Systems Trend Detective
 * Express Application & REST API Orchestration
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const env = require('./config/environment');
const rateLimiter = require('./middleware/rateLimiter');
const errorHandler = require('./middleware/errorHandler');

// Route Modules
const metadataRoutes = require('./routes/metadataRoutes');
const analysisRoutes = require('./routes/analysisRoutes');
const climateRoutes = require('./routes/climateRoutes');
const mapRoutes = require('./routes/mapRoutes');
const methaneRoutes = require('./routes/methaneRoutes');
const mlRoutes = require('./routes/mlRoutes');
const aiRoutes = require('./routes/aiRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const datasetRoutes = require('./routes/datasetRoutes');

const app = express();

// Security & Parsing Middleware
app.use(cors());
app.use(express.json({ limit: '15mb' }));
app.use(express.urlencoded({ extended: true, limit: '15mb' }));
app.use(rateLimiter(200, 60000)); // 200 requests/minute

// Serve Generated Reports Directory
app.use('/reports', express.static(env.PATHS.REPORTS_DIR));

// Serve Frontend Static Assets
app.use(express.static(env.PATHS.FRONTEND_DIR));

// Health Endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    project: 'Earth Systems Trend Detective',
    challenge: 'NASA Space Apps Challenge 2026',
    uptime_seconds: Math.floor(process.uptime()),
    timestamp: new Date().toISOString()
  });
});

// API Routes
const metadataController = require('./controllers/metadataController');
app.get('/api/variables', metadataController.getVariables);
app.get('/api/regions', metadataController.getRegions);
app.get('/api/coverage', metadataController.getCoverage);

app.use('/api/metadata', metadataRoutes);
app.use('/api/analysis', analysisRoutes);
app.use('/api/climate', climateRoutes);
app.use('/api/map', mapRoutes);
app.use('/api/methane', methaneRoutes);
app.use('/api/ml', mlRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/users', userRoutes);
app.use('/api/datasets', datasetRoutes);

// Clean HTML Page Routing
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) {
    return res.status(404).json({ success: false, message: 'API endpoint not found.' });
  }

  const cleanPath = req.path.replace(/^\//, '');

  // 1. Direct match in frontend/pages/ (e.g. "trend-detective.html" or "trend-detective")
  const pageCandidates = [
    path.join(env.PATHS.FRONTEND_DIR, 'pages', cleanPath),
    path.join(env.PATHS.FRONTEND_DIR, 'pages', cleanPath + '.html'),
    path.join(env.PATHS.FRONTEND_DIR, cleanPath),
    path.join(env.PATHS.FRONTEND_DIR, cleanPath + '.html')
  ];

  for (const candidate of pageCandidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      return res.sendFile(candidate);
    }
  }

  // 2. Fallback to index.html
  const indexPath = path.join(env.PATHS.FRONTEND_DIR, 'index.html');
  if (fs.existsSync(indexPath)) {
    return res.sendFile(indexPath);
  }

  res.send('NASA Earth Systems Trend Detective — Initializing Frontend UI...');
});

// Global Error Handler
app.use(errorHandler);

module.exports = app;
