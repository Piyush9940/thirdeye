/**
 * NASA Earth Systems Trend Detective
 * Client API Connector & Data Layer
 */

const API = {
  // Utility for standard JSON API requests
  async request(endpoint, options = {}) {
    const url = `${window.APP_CONFIG.API_BASE}${endpoint}`;
    const token = localStorage.getItem('nasa_token');
    
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

    try {
      const response = await fetch(url, { credentials: 'same-origin', ...options, headers });
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || `Request failed with status ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  // 1. Dashboard Endpoints
  getDashboardKPIs() {
    return this.request('/api/dashboard/stats');
  },

  getDashboardCharts(period = 'ALL', region = 'ALL') {
    const q = new URLSearchParams({ period, region });
    return this.request(`/api/dashboard/charts?${q.toString()}`);
  },

  // 2. Geospatial Endpoints
  getSpatialNodes(period = null) {
    const q = period ? `?period=${encodeURIComponent(period)}` : '';
    return this.request(`/api/geo/nodes${q}`);
  },

  getIndiaBoundary() {
    return this.request('/api/geo/boundary');
  },

  // 3. Methane Observations
  getMethaneObservations(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/api/methane/observations?${q}`);
  },

  // 4. Model Predictions & Metrics
  getMLPPredictions(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/api/predictions/evaluations?${q}`);
  },

  getModelMetrics() {
    return this.request('/api/models/experiments');
  },

  predictMethane(features, fold = 1, seed = 42) {
    return this.request('/api/predictions/infer', {
      method: 'POST',
      body: JSON.stringify({ features, fold, seed })
    });
  },

  // 5. Climate Context Data
  getClimateData() {
    return this.request('/api/climate/data');
  },

  // 6. Reports Module
  generateReport(type, params = {}) {
    return this.request('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ type, params })
    });
  },

  // 7. AI Research Assistant
  chatWithAssistant(message, history = []) {
    return this.request('/api/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history })
    });
  },

  // 8. Auth Endpoints
  login(credentials) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  },

  register(userData) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  getUserProfile() {
    return this.request('/api/auth/me');
  },

  saveAnalysis(analysisData) {
    return this.request('/api/users/saved-analyses', {
      method: 'POST',
      body: JSON.stringify(analysisData)
    });
  },

  getSavedAnalyses() {
    return this.request('/api/users/saved-analyses');
  }
};

window.API = API;
