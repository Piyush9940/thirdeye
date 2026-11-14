const pythonExec = require('./pythonExecutionService');
const env = require('../config/environment');

class MLService {
  async getMetrics() {
    return await pythonExec.execute(env.PATHS.ML_INFERENCE, ['--mode', 'metrics']);
  }

  async predict(params) {
    const jsonArg = JSON.stringify({
      mode: 'predict',
      fold: params.fold || 1,
      seed: params.seed || 42,
      features: params.features || null
    });
    return await pythonExec.execute(env.PATHS.ML_INFERENCE, ['--json_input', jsonArg]);
  }
}

module.exports = new MLService();
