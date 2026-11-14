/**
 * NASA Earth Systems Trend Detective
 * Python Service Configuration
 */

const env = require('./environment');

module.exports = {
  pythonPath: env.PYTHON_PATH,
  modelPackageDir: env.PROJECT_ROOT + '/models/production_reference',
  timeout: 15000,
  maxRetries: 2
};
