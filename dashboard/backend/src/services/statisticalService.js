const pythonExec = require('./pythonExecutionService');
const env = require('../config/environment');
const logger = require('../utils/logger');

class StatisticalService {
  constructor() {
    this.cache = new Map();
  }

  _makeCacheKey(mode, params) {
    return `${mode}:${params.variable || 'T2M'}:${params.region || 'ALL'}:${params.node_id || ''}:${params.start_date || ''}:${params.end_date || ''}`;
  }

  async getTrend(params) {
    const key = this._makeCacheKey('trend', params);
    if (this.cache.has(key)) {
      logger.debug(`[StatisticalService] Cache hit: ${key}`);
      return this.cache.get(key);
    }

    const jsonArg = JSON.stringify({
      mode: 'trend',
      variable: params.variable || 'T2M',
      region: params.region || 'ALL',
      node_id: params.node_id || null,
      start_date: params.start_date || '2015-01',
      end_date: params.end_date || '2024-12'
    });

    const result = await pythonExec.execute(env.PATHS.STATISTICAL_ENGINE, ['--json_input', jsonArg]);
    this.cache.set(key, result);
    return result;
  }

  async getSeasonal(params) {
    const key = this._makeCacheKey('seasonal', params);
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }

    const jsonArg = JSON.stringify({
      mode: 'seasonal',
      variable: params.variable || 'T2M',
      region: params.region || 'ALL',
      start_date: params.start_date || '2015-01',
      end_date: params.end_date || '2024-12'
    });

    const result = await pythonExec.execute(env.PATHS.STATISTICAL_ENGINE, ['--json_input', jsonArg]);
    this.cache.set(key, result);
    return result;
  }

  async getCompare(params) {
    const key = this._makeCacheKey('compare', params);
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }

    const jsonArg = JSON.stringify({
      mode: 'compare',
      variable: params.variable || 'T2M',
      start_date: params.start_date || '2015-01',
      end_date: params.end_date || '2024-12'
    });

    const result = await pythonExec.execute(env.PATHS.STATISTICAL_ENGINE, ['--json_input', jsonArg]);
    this.cache.set(key, result);
    return result;
  }

  async getSpatialValues(params) {
    const key = this._makeCacheKey('spatial_values', params);
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }

    const jsonArg = JSON.stringify({
      mode: 'spatial_values',
      variable: params.variable || 'T2M',
      start_date: params.start_date || '2015-01',
      end_date: params.end_date || '2024-12'
    });

    const result = await pythonExec.execute(env.PATHS.STATISTICAL_ENGINE, ['--json_input', jsonArg]);
    this.cache.set(key, result);
    return result;
  }
}

module.exports = new StatisticalService();
