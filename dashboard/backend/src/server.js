/**
 * NASA Earth Systems Trend Detective
 * Server Entry Point
 */

const app = require('./app');
const env = require('./config/environment');
const { connectDB } = require('./config/database');
const logger = require('./utils/logger');

const startServer = async () => {
  // Connect to database (with automatic fallback to local store)
  await connectDB();

  const server = app.listen(env.PORT, () => {
    logger.info(`
======================================================================
  NASA SPACE APPS CHALLENGE 2026: EARTH SYSTEMS TREND DETECTIVE
  Discover What Is Changing on Earth. Understand Where. Measure How Much.
======================================================================
  Primary Backend:   Node.js + Express
  Server listening:  http://localhost:${env.PORT}
  Environment:       ${env.NODE_ENV}
  Data Provenance:   NASA POWER Grid 2-deg (30,600 continuous observations)
  Spatial Mesh:      255 Nodes (8-NN Adjacency, 6 Custom Regions)
  Methane Status:    Sentinel-5P Pilot Soundings (4 Snapshots, 226 obs)
  ML Model Status:   Experimental Reference (PyTorch CPU Checkpoints)
======================================================================
    `);
  });

  const shutdown = () => {
    logger.info('[Server] Shutting down gracefully...');
    server.close(() => {
      logger.info('[Server] Process exited.');
      process.exit(0);
    });
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
};

if (require.main === module) {
  startServer();
}

module.exports = app;
