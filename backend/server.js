/**
 * NASA Earth Systems Trend Detective
 * Server Entry Point
 */

const app = require('./app');
const env = require('./config/environment');
const { connectDB } = require('./config/database');

const startServer = async () => {
  // Connect to DB (with automatic graceful fallback)
  await connectDB();

  const server = app.listen(env.PORT, () => {
    console.log(`
======================================================================
  NASA SPACE APPS CHALLENGE — EARTH SYSTEMS TREND DETECTIVE
  AI-Powered Earth Observation & Methane Intelligence Platform
======================================================================
  Server running at: http://localhost:${env.PORT}
  Environment:       ${env.NODE_ENV}
  Data Source:       Verified Dashboard Exports (255 nodes, 226 obs)
  ML Status:         Experimental Reference Model
======================================================================
    `);
  });

  // Graceful shutdown handling
  const shutdown = () => {
    console.log('[Server] Shutting down gracefully...');
    server.close(() => {
      console.log('[Server] Process terminated.');
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
