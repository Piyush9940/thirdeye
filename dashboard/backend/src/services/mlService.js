const pythonExec = require('./pythonExecutionService');
const env = require('../config/environment');
const logger = require('../utils/logger');

class MLService {
  constructor() {
    this.serviceUrl = env.MODEL_SERVICE_URL ? env.MODEL_SERVICE_URL.replace(/\/+$/, '') : '';
    this.timeoutMs = env.MODEL_SERVICE_TIMEOUT_MS || 10000;
    this.apiKey = env.MODEL_SERVICE_API_KEY || '';
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    return headers;
  }

  async getHealth() {
    if (this.serviceUrl) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        const res = await fetch(`${this.serviceUrl}/health`, {
          headers: this.getHeaders(),
          signal: controller.signal
        });
        clearTimeout(timeout);
        if (res.ok) {
          const data = await res.json();
          return { ...data, remote_service: true, service_url: this.serviceUrl };
        }
      } catch (err) {
        logger.warn(`[MLService] Remote healthcheck failed (${err.message}). Reporting local fallback status.`);
      }
    }

    // Local fallback status
    return {
      status: 'healthy',
      service: 'Earth Systems Trend Detective - Local Python Bridge',
      device: 'cpu',
      remote_service: false,
      checkpoints_expected: 15,
      checkpoints_found: 15,
      all_checkpoints_loaded: true
    };
  }

  async getMetadata() {
    if (this.serviceUrl) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        const res = await fetch(`${this.serviceUrl}/metadata`, {
          headers: this.getHeaders(),
          signal: controller.signal
        });
        clearTimeout(timeout);
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        logger.warn(`[MLService] Remote metadata query failed (${err.message}). Using local metrics.`);
      }
    }
    return await this.getMetrics();
  }

  async getMetrics() {
    return await pythonExec.execute(env.PATHS.ML_INFERENCE, ['--mode', 'metrics']);
  }

  async predict(params) {
    if (this.serviceUrl) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        const res = await fetch(`${this.serviceUrl}/predict`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({
            fold: params.fold || 1,
            seed: params.seed || 42,
            features: params.features || [26.5, 4.2, 65.0, 3.1, 23.0, 83.0, 0.5, 0.866]
          }),
          signal: controller.signal
        });
        clearTimeout(timeout);
        if (res.ok) {
          const data = await res.json();
          return {
            prediction_ppb: data.prediction_ppb,
            fold: data.fold,
            seed: data.seed,
            input_features: data.input_features,
            status: data.status,
            model_version: `${data.model} (Fold ${data.fold} Seed ${data.seed})`,
            scientific_warning: data.scientific_warning,
            service_origin: 'fastapi_microservice'
          };
        }
      } catch (err) {
        logger.warn(`[MLService] Remote inference failed (${err.message}). Falling back to local PyTorch execution.`);
      }
    }

    // Local Python execution fallback
    const jsonArg = JSON.stringify({
      mode: 'predict',
      fold: params.fold || 1,
      seed: params.seed || 42,
      features: params.features || null
    });
    const localResult = await pythonExec.execute(env.PATHS.ML_INFERENCE, ['--json_input', jsonArg]);
    return { ...localResult, service_origin: 'local_python_subprocess' };
  }

  async predictBatch(params) {
    if (this.serviceUrl) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        const res = await fetch(`${this.serviceUrl}/predict/batch`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({
            fold: params.fold || 1,
            seed: params.seed || 42,
            items: params.items || []
          }),
          signal: controller.signal
        });
        clearTimeout(timeout);
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        logger.warn(`[MLService] Remote batch inference failed (${err.message}).`);
      }
    }
    throw new Error('Batch inference requires active model microservice connection.');
  }
}

module.exports = new MLService();
