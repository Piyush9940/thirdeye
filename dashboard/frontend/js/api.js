/**
 * NASA Earth Systems Trend Detective — Central API Client
 */

class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || `API request failed with status ${response.status}`);
      }

      return data.data !== undefined ? data.data : data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      if (window.showToast) {
        window.showToast(`Error: ${err.message}`, 'error');
      }
      throw err;
    }
  }

  // Metadata
  getMetadata() { return this.request('/metadata'); }
  getVariables() { return this.request('/metadata/variables'); }
  getRegions() { return this.request('/metadata/regions'); }

  // Statistical Trend Detective
  getTrend(params) {
    return this.request('/analysis/trend', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  getSeasonal(params) {
    return this.request('/analysis/seasonal', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  getCompare(params) {
    return this.request('/analysis/compare', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }

  // Map & Geospatial
  getMapNodes() { return this.request('/map/nodes'); }
  getMapEdges() { return this.request('/map/edges'); }
  async getBoundary() {
    const res = await fetch(`${this.baseUrl}/map/boundary`);
    return await res.json();
  }
  getSpatialValues(params) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/map/values?${qs}`);
  }

  // Methane
  getMethaneSummary() { return this.request('/methane/summary'); }

  // ML Insights
  getMLMetrics() { return this.request('/ml/metrics'); }
  runMLInference(payload) {
    return this.request('/ml/inference', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // AI Assistant
  askAssistant(prompt, context) {
    return this.request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt, context })
    });
  }

  // Reports
  generateReport(analysisData) {
    return this.request('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(analysisData)
    });
  }

  // Dynamic Dataset Ingestion & Scientific Exploration
  getDatasets() { return this.request('/datasets'); }
  getDataset(id) { return this.request(`/datasets/${id}`); }
  getDatasetMetadata(id) { return this.request(`/datasets/${id}/metadata`); }
  uploadDataset(payload) {
    return this.request('/datasets/upload', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
  validateDataset(payload) {
    return this.request('/datasets/validate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
  deleteDataset(id) {
    return this.request(`/datasets/${id}`, {
      method: 'DELETE'
    });
  }
  analyzeDataset(id, params) {
    return this.request(`/datasets/${id}/analyze`, {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
  compareDataset(id, params) {
    return this.request(`/datasets/${id}/compare`, {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
}

const api = new ApiClient();
window.api = api;
