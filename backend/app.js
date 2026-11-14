/**
 * NASA Earth Systems Trend Detective
 * Express Application Setup & Middleware Orchestration
 */

const express = require('express');
const cors = require('cors');
const path = require('path');

const datasetRoutes = require('./routes/dataset.routes');
const forecastRoutes = require('./routes/forecast.routes');
const reportRoutes = require('./routes/report.routes');
const assistantRoutes = require('./routes/assistant.routes');
const authRoutes = require('./routes/auth.routes');
const analysisRoutes = require('./routes/analysis.routes');
const hotspotRoutes = require('./routes/hotspot.routes');
const trendRoutes = require('./routes/trend.routes');

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve Frontend Static Assets
const frontendPath = path.resolve(__dirname, '../frontend');
app.use(express.static(frontendPath));

// API Routes
app.use('/api', datasetRoutes);
app.use('/api', forecastRoutes);
app.use('/api', reportRoutes);
app.use('/api', assistantRoutes);
app.use('/api', authRoutes);
app.use('/api', analysisRoutes);
app.use('/api', hotspotRoutes);
app.use('/api', trendRoutes);

// Fallback for HTML page routing
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) {
    return res.status(404).json({ success: false, message: 'API endpoint not found.' });
  }
  // Try to serve corresponding HTML or fallback to index.html
  const file = req.path === '/' ? 'index.html' : req.path.replace(/^\//, '');
  const candidate = path.join(frontendPath, file);
  if (path.extname(file) === '.html' && require('fs').existsSync(candidate)) {
    return res.sendFile(candidate);
  }
  res.sendFile(path.join(frontendPath, 'index.html'));
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('[App Error]', err);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Internal server error occurred.',
    error: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });
});

module.exports = app;
