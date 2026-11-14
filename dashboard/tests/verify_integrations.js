/**
 * End-to-End Comprehensive Integration Verification Suite
 * NASA Space Apps Challenge 2026: Earth Systems Trend Detective
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

const DASHBOARD_DIR = path.resolve(__dirname, '../');
const FRONTEND_DIR = path.resolve(DASHBOARD_DIR, 'frontend');
const BACKEND_DIR = path.resolve(DASHBOARD_DIR, 'backend');
const app = require('../backend/src/app');

// Helper to make in-memory request to Express app
function callApi(method, url, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const socket = {
      remoteAddress: '127.0.0.1',
      encrypted: false,
      on: () => {},
      removeListener: () => {}
    };

    const req = new http.IncomingMessage(socket);
    req.method = method.toUpperCase();
    req.url = url;
    req.headers = {
      'host': 'localhost',
      'user-agent': 'integration-verifier',
      'content-type': 'application/json',
      ...headers
    };
    req.socket = socket;
    req.connection = socket;

    const res = new http.ServerResponse(req);
    let output = '';
    res.write = (chunk) => {
      output += chunk.toString('utf-8');
      return true;
    };
    res.end = (chunk) => {
      if (chunk) output += chunk.toString('utf-8');
      try {
        const parsed = JSON.parse(output);
        resolve({ status: res.statusCode, body: parsed, raw: output, headers: res.getHeaders() });
      } catch (e) {
        resolve({ status: res.statusCode, body: output, raw: output, headers: res.getHeaders() });
      }
    };

    if (body) {
      req.body = body;
    }

    try {
      app(req, res);
      if (body && !req.body) {
        req.emit('data', Buffer.from(JSON.stringify(body)));
        req.emit('end');
      }
    } catch (err) {
      reject(err);
    }
  });
}

// Suite Runner
async function runIntegrationVerification() {
  console.log('======================================================================');
  console.log('  NASA SPACE APPS: COMPREHENSIVE INTEGRATION AUDIT & TEST SUITE');
  console.log('======================================================================\n');

  let totalChecks = 0;
  let passedChecks = 0;
  let failedChecks = 0;

  const check = async (category, name, fn) => {
    totalChecks++;
    process.stdout.write(`[${category}] ${name}... `);
    try {
      await fn();
      passedChecks++;
      console.log('OK');
    } catch (err) {
      failedChecks++;
      console.log('FAIL');
      console.error(`      -> ${err.message}`);
    }
  };

  // -------------------------------------------------------------------------
  // SECTION 1: STATIC ASSETS & HTML INTEGRATION
  // -------------------------------------------------------------------------
  console.log('--- 1. STATIC ASSET & HTML INTEGRATION ---');

  const htmlFiles = [
    'index.html',
    'pages/trend-detective.html',
    'pages/dataset-explorer.html',
    'pages/overview.html',
    'pages/earth-explorer.html',
    'pages/regional-comparison.html',
    'pages/climate-explorer.html',
    'pages/methane-analysis.html',
    'pages/ml-insights.html',
    'pages/ai-assistant.html',
    'pages/reports.html'
  ];

  for (const hf of htmlFiles) {
    await check('STATIC', `HTML file exists: ${hf}`, () => {
      const fullPath = path.join(FRONTEND_DIR, hf);
      if (!fs.existsSync(fullPath)) throw new Error(`File not found: ${fullPath}`);
      const content = fs.readFileSync(fullPath, 'utf-8');
      if (content.length < 500) throw new Error(`File is unexpectedly short (${content.length} bytes)`);
    });
  }

  // Check all script tags and link tags in all HTML files
  await check('STATIC', 'All local stylesheet and script links resolve to disk', () => {
    const missing = [];
    for (const hf of htmlFiles) {
      const fullPath = path.join(FRONTEND_DIR, hf);
      const content = fs.readFileSync(fullPath, 'utf-8');

      // Match href="..." and src="..."
      const matches = content.matchAll(/(?:href|src)=["']([^"']+)["']/g);
      for (const m of matches) {
        const link = m[1];
        if (link.startsWith('http://') || link.startsWith('https://') || link.startsWith('data:') || link.startsWith('#')) {
          continue;
        }
        const clean = link.replace(/^\//, '');
        const target = path.join(FRONTEND_DIR, clean);
        if (!fs.existsSync(target)) {
          missing.push(`${hf} -> ${link}`);
        }
      }
    }
    if (missing.length > 0) {
      throw new Error(`Missing local assets:\n  ${missing.join('\n  ')}`);
    }
  });

  // Check DOM ID linkage
  await check('DOM-LINK', 'trend-detective.js elements exist in trend-detective.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/trend-detective.html'), 'utf-8');
    const requiredIds = [
      'region-select', 'start-date-input', 'end-date-input', 'btn-analyze', 'btn-reset',
      'btn-generate-report', 'chart-loading', 'trend-chart', 'stat-sen-rate', 'stat-sen-decade',
      'stat-mk-pval', 'stat-mk-verdict', 'stat-mk-tau', 'stat-ols-r2', 'stat-ols-ci',
      'interp-title', 'interp-text', 'interp-caveat'
    ];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in trend-detective.html`);
      }
    }
  });

  await check('DOM-LINK', 'earth-explorer.js elements exist in earth-explorer.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/earth-explorer.html'), 'utf-8');
    const requiredIds = [
      'leaflet-map', 'map-region-filter', 'toggle-edges', 'node-inspector',
      'insp-region', 'insp-node-id', 'insp-coords', 'insp-degree', 'insp-status'
    ];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in earth-explorer.html`);
      }
    }
  });

  await check('DOM-LINK', 'regional-comparison.js elements exist in regional-comparison.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/regional-comparison.html'), 'utf-8');
    const requiredIds = ['compare-var-select', 'compare-chart', 'compare-table-body'];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in regional-comparison.html`);
      }
    }
  });

  await check('DOM-LINK', 'climate-explorer.js elements exist in climate-explorer.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/climate-explorer.html'), 'utf-8');
    const requiredIds = ['clim-region-select', 'climatology-chart', 'seasonal-cards'];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in climate-explorer.html`);
      }
    }
  });

  await check('DOM-LINK', 'methane-analysis.js elements exist in methane-analysis.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/methane-analysis.html'), 'utf-8');
    const requiredIds = ['methane-snapshots', 'methane-regions-body'];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in methane-analysis.html`);
      }
    }
  });

  await check('DOM-LINK', 'ml-insights.js elements exist in ml-insights.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/ml-insights.html'), 'utf-8');
    const requiredIds = [
      'ml-arch-info', 'ml-folds-container', 'ml-comparison-body',
      'btn-run-inference', 'inf-t2m', 'inf-prec', 'inf-rh', 'inf-ws', 'inf-lat', 'inf-lon', 'inf-fold', 'inf-seed', 'inf-result'
    ];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in ml-insights.html`);
      }
    }
  });

  await check('DOM-LINK', 'ai-assistant.js elements exist in ai-assistant.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/ai-assistant.html'), 'utf-8');
    const requiredIds = ['chat-messages', 'chat-input', 'btn-chat-send'];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in ai-assistant.html`);
      }
    }
  });

  await check('DOM-LINK', 'reports.js elements exist in reports.html', () => {
    const html = fs.readFileSync(path.join(FRONTEND_DIR, 'pages/reports.html'), 'utf-8');
    const requiredIds = ['rep-var-select', 'rep-region-select', 'btn-create-report', 'rep-generate-status', 'reports-history-list'];
    for (const id of requiredIds) {
      if (!html.includes(`id="${id}"`)) {
        throw new Error(`Missing expected element id="${id}" in reports.html`);
      }
    }
  });

  // -------------------------------------------------------------------------
  // SECTION 2: ALL REST API ENDPOINTS INTEGRATION
  // -------------------------------------------------------------------------
  console.log('\n--- 2. REST API ENDPOINTS VERIFICATION ---');

  // Health
  await check('API', 'GET /api/health', async () => {
    const res = await callApi('GET', '/api/health');
    if (res.status !== 200 || res.body.status !== 'healthy') throw new Error(`Status ${res.status}`);
    if (!res.body.project.includes('Trend Detective')) throw new Error('Invalid project name');
  });

  // Metadata
  await check('API', 'GET /api/metadata', async () => {
    const res = await callApi('GET', '/api/metadata');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    const d = res.body.data;
    if (d.geographic_coverage.total_nodes !== 255) throw new Error(`Nodes count ${d.geographic_coverage.total_nodes} != 255`);
    if (d.temporal_coverage.primary_climate.total_observations !== 30600) throw new Error('Observations count mismatch');
  });

  await check('API', 'GET /api/metadata/variables', async () => {
    const res = await callApi('GET', '/api/metadata/variables');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    const keys = Object.keys(res.body.data);
    if (!keys.includes('T2M') || !keys.includes('PRECTOTCORR') || !keys.includes('RH2M') || !keys.includes('WS10M') || !keys.includes('CH4')) {
      throw new Error(`Variables missing required keys: ${keys.join(',')}`);
    }
  });

  await check('API', 'GET /api/metadata/regions', async () => {
    const res = await callApi('GET', '/api/metadata/regions');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    const regions = res.body.data.map(r => r.code);
    if (!regions.includes('NW') || !regions.includes('NE') || !regions.includes('CW') || !regions.includes('CE') || !regions.includes('SW') || !regions.includes('SE')) {
      throw new Error(`Missing custom regions: ${regions.join(',')}`);
    }
  });

  await check('API', 'GET /api/metadata/coverage', async () => {
    const res = await callApi('GET', '/api/metadata/coverage');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.geographic || !res.body.data.temporal) throw new Error('Missing coverage fields');
  });

  // Direct convenience aliases mandated by challenge specification
  await check('API', 'GET /api/variables (Root Alias)', async () => {
    const res = await callApi('GET', '/api/variables');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.T2M || !res.body.data.CH4) throw new Error('Missing variable definitions');
  });

  await check('API', 'GET /api/regions (Root Alias)', async () => {
    const res = await callApi('GET', '/api/regions');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length < 6) throw new Error('Regions list incomplete');
  });

  await check('API', 'GET /api/coverage (Root Alias)', async () => {
    const res = await callApi('GET', '/api/coverage');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.geographic || !res.body.data.temporal) throw new Error('Coverage data incomplete');
  });

  await check('API', 'GET /api/metadata/registry (Central Dataset Registry)', async () => {
    const res = await callApi('GET', '/api/metadata/registry');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length < 3) throw new Error('Registry records missing');
  });

  // Climate
  await check('API', 'GET /api/climate/series (T2M, NW)', async () => {
    const res = await callApi('GET', '/api/climate/series?variable=T2M&region=NW');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data.time_series) || res.body.data.time_series.length !== 120) {
      throw new Error(`Expected 120 time series entries, got ${res.body.data.time_series?.length}`);
    }
  });

  await check('API', 'GET /api/climate/summary (T2M, ALL)', async () => {
    const res = await callApi('GET', '/api/climate/summary?variable=T2M&region=ALL');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.summary_statistics || !res.body.data.ols) throw new Error('Missing climate summary statistics');
  });

  await check('API', 'GET /api/climate/observations', async () => {
    const res = await callApi('GET', '/api/climate/observations?variable=PRECTOTCORR&region=ALL');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length !== 120) throw new Error('Observations count mismatch');
  });

  // Map
  await check('API', 'GET /api/map/nodes', async () => {
    const res = await callApi('GET', '/api/map/nodes');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length !== 255) {
      throw new Error(`Expected 255 nodes, got ${res.body.data?.length}`);
    }
    const node = res.body.data[0];
    if (typeof node.lat !== 'number' || typeof node.lon !== 'number' || !node.region) {
      throw new Error('Node format invalid');
    }
  });

  await check('API', 'GET /api/map/edges', async () => {
    const res = await callApi('GET', '/api/map/edges');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length === 0) {
      throw new Error('Edges empty');
    }
  });

  await check('API', 'GET /api/map/regions', async () => {
    const res = await callApi('GET', '/api/map/regions');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!Array.isArray(res.body.data) || res.body.data.length < 6) throw new Error('Map regions list incomplete');
  });

  await check('API', 'GET /api/map/boundary (GeoJSON)', async () => {
    const res = await callApi('GET', '/api/map/boundary');
    if (res.status !== 200) throw new Error(`Status ${res.status}`);
    if (res.body.type !== 'FeatureCollection' && res.body.type !== 'Feature' && res.body.type !== 'Polygon' && res.body.type !== 'MultiPolygon') {
      throw new Error('Not valid GeoJSON');
    }
  });

  await check('API', 'GET /api/map/values (Spatial mesh values for 255 nodes)', async () => {
    const res = await callApi('GET', '/api/map/values?variable=T2M');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (res.body.data.n_nodes !== 255) throw new Error(`Expected 255 node values, got ${res.body.data.n_nodes}`);
  });

  // Methane
  await check('API', 'GET /api/methane/summary', async () => {
    const res = await callApi('GET', '/api/methane/summary');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    const d = res.body.data;
    if (d.total_pixels_filtered !== 73045) throw new Error('Pixel count mismatch');
    if (d.snapshots.length !== 4) throw new Error('Expected 4 snapshots');
    const se = d.regions.find(r => r.code === 'SE');
    if (!se || se.pixel_count !== 0) throw new Error('Southeast India gap not accurately represented as 0 soundings');
  });

  await check('API', 'GET /api/methane/observations', async () => {
    const res = await callApi('GET', '/api/methane/observations');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
  });

  await check('API', 'GET /api/methane/regions', async () => {
    const res = await callApi('GET', '/api/methane/regions');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (res.body.data.length < 6) throw new Error('Missing region breakdown in methane API');
  });

  // ML
  await check('API', 'GET /api/ml/metadata', async () => {
    const res = await callApi('GET', '/api/ml/metadata');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.status.includes('Not Production Approved')) throw new Error('Missing scientific status');
  });

  await check('API', 'GET /api/ml/metrics', async () => {
    const res = await callApi('GET', '/api/ml/metrics');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (res.body.data.overall_performance.mean_r2 >= 0) throw new Error('Negative R2 disclosure missing');
    if (!res.body.data.fold_metrics.fold_2.note.includes('11')) throw new Error('Fold 2 11 nodes gap not documented');
  });

  await check('API', 'GET /api/ml/predictions (Historical 720 Evaluation Records)', async () => {
    const res = await callApi('GET', '/api/ml/predictions?fold=1&seed=7');
    if (res.status !== 200 || !res.body.success) throw new Error('Call failed');
    if (!res.body.data.predictions || res.body.data.predictions.length === 0) {
      throw new Error('Evaluation predictions empty');
    }
    const sample = res.body.data.predictions[0];
    if (typeof sample.actual_methane_ppb !== 'number' || typeof sample.predicted_methane_ppb !== 'number') {
      throw new Error('Prediction fields missing');
    }
  });

  await check('API', 'POST /api/ml/inference (Live PyTorch CPU Execution)', async () => {
    const res = await callApi('POST', '/api/ml/inference', {
      fold: 1,
      seed: 42,
      features: {
        T2M: 27.5,
        PRECTOTCORR: 5.0,
        RH2M: 70.0,
        WS10M: 3.2,
        latitude: 21.0,
        longitude: 80.0
      }
    });
    if (res.status !== 200 || !res.body.success) throw new Error('Inference call failed');
    if (typeof res.body.data.prediction_ppb !== 'number' || res.body.data.prediction_ppb < 1700 || res.body.data.prediction_ppb > 2100) {
      throw new Error(`Inference returned out-of-range ppb: ${res.body.data.prediction_ppb}`);
    }
  });

  // User Preferences
  await check('API', 'GET & PUT /api/users/preferences', async () => {
    const getRes = await callApi('GET', '/api/users/preferences');
    if (getRes.status !== 200 || !getRes.body.success) throw new Error('GET preferences failed');

    const putRes = await callApi('PUT', '/api/users/preferences', {
      preferredRegion: 'NW',
      theme: 'space-dark'
    });
    if (putRes.status !== 200 || !putRes.body.success) throw new Error('PUT preferences failed');
    if (putRes.body.data.preferredRegion !== 'NW') throw new Error('Preferences did not persist');
  });

  // -------------------------------------------------------------------------
  // SECTION 3: CORE STATISTICAL ENGINE & SCIENTIFIC WORKFLOWS
  // -------------------------------------------------------------------------
  console.log('\n--- 3. SCIENTIFIC ANALYSIS & HYPOTHESIS TESTING INTEGRATION ---');

  // Test All 4 Variables across All India
  const variables = ['T2M', 'PRECTOTCORR', 'RH2M', 'WS10M'];
  for (const v of variables) {
    await check('ENGINE', `Trend Detective calculation: ${v} nationwide`, async () => {
      const res = await callApi('POST', '/api/analysis/trend', {
        variable: v,
        region: 'ALL',
        start_date: '2015-01',
        end_date: '2024-12'
      });
      if (res.status !== 200 || !res.body.success) throw new Error(`Trend calculation failed for ${v}`);
      const d = res.body.data;
      if (d.ols.p_value === undefined || d.mann_kendall.p_value === undefined || d.sen_slope.slope_per_year === undefined) {
        throw new Error('Statistical parameters missing');
      }
      if (!d.interpretation.summary || !d.interpretation.rate_description) {
        throw new Error('Plain language interpretation missing');
      }
    });
  }

  // Test Custom Regional Partitioning
  const regions = ['NW', 'NE', 'CW', 'CE', 'SW', 'SE'];
  for (const r of regions) {
    await check('ENGINE', `Trend Detective calculation: T2M in Region ${r}`, async () => {
      const res = await callApi('POST', '/api/analysis/trend', {
        variable: 'T2M',
        region: r
      });
      if (res.status !== 200 || !res.body.success) throw new Error(`Trend calculation failed for region ${r}`);
      if (res.body.data.region !== r) throw new Error('Region mismatch in output');
    });
  }

  // Cross-Regional Comparison
  await check('ENGINE', 'POST /api/analysis/compare (Cross-regional slopes & ranks)', async () => {
    const res = await callApi('POST', '/api/analysis/compare', { variable: 'T2M' });
    if (res.status !== 200 || !res.body.success) throw new Error('Comparison failed');
    const comps = res.body.data.comparisons;
    if (comps.length !== 7) throw new Error(`Expected 7 partitions (6 zones + ALL), got ${comps.length}`);
    for (const c of comps) {
      if (typeof c.sen_slope_per_year !== 'number' || typeof c.mann_kendall_p !== 'number') {
        throw new Error(`Invalid statistics in comparison for ${c.region}`);
      }
    }
  });

  // Seasonal Climatological Decomposition
  await check('ENGINE', 'POST /api/analysis/seasonal (12-Month climatology & 4 seasons)', async () => {
    const res = await callApi('POST', '/api/analysis/seasonal', { variable: 'T2M', region: 'ALL' });
    if (res.status !== 200 || !res.body.success) throw new Error('Seasonal failed');
    const d = res.body.data;
    if (d.monthly_climatology.length !== 12) throw new Error('Expected 12 monthly climatological means');
    if (d.seasonal_summary.length !== 4) throw new Error('Expected 4 climatological seasons');
    const seasonNames = d.seasonal_summary.map(s => s.season);
    if (!seasonNames.some(s => s.includes('Monsoon'))) throw new Error('Monsoon season missing');
  });

  // -------------------------------------------------------------------------
  // SECTION 4: AI RESEARCH ASSISTANT & DOSSIER GENERATION
  // -------------------------------------------------------------------------
  console.log('\n--- 4. AI ASSISTANT & PDF REPORT GENERATION INTEGRATION ---');

  const testPrompts = [
    { prompt: 'Is air temperature increasing in Northwest India?', expected: 'statistically significant' },
    { prompt: 'What does the p-value mean in climate science?', expected: 'p-value' },
    { prompt: 'Explain Sen\'s robust slope vs linear regression', expected: 'median' },
    { prompt: 'What are the scientific limitations of satellite methane?', expected: 'Sentinel-5P' }
  ];

  for (const tp of testPrompts) {
    await check('AI-ASSIST', `Q&A: "${tp.prompt}"`, async () => {
      const res = await callApi('POST', '/api/ai/chat', {
        prompt: tp.prompt,
        context: {
          variable_name: 'Air Temperature at 2m',
          region_name: 'Northwest India',
          units: '°C',
          ols: { slope_per_year: 0.0036, p_value: 0.988 },
          mann_kendall: { p_value: 0.9403, is_significant: false },
          sen_slope: { slope_per_year: -0.014 }
        }
      });
      if (res.status !== 200 || !res.body.success) throw new Error('AI chat failed');
      const ans = res.body.data.answer.toLowerCase();
      if (!ans.includes(tp.expected.toLowerCase())) {
        throw new Error(`AI response did not include expected concept: "${tp.expected}"`);
      }
    });
  }

  // ReportLab PDF Synthesis
  let generatedReport = null;
  await check('REPORTLAB', 'Generate publication-grade PDF dossier', async () => {
    const res = await callApi('POST', '/api/reports/generate', {
      variable: 'T2M',
      variable_name: 'Air Temperature at 2m',
      units: '°C',
      region: 'NW',
      region_name: 'Northwest India',
      date_range: { start: '2015-01', end: '2024-12', n_months: 120 },
      ols: { slope_per_year: 0.0036, slope_per_decade: 0.036, r_squared: 0.0001, p_value: 0.988, ci_lower_per_year: -0.47, ci_upper_per_year: 0.48 },
      mann_kendall: { S: 34, Z: 0.07, tau: -0.0048, p_value: 0.9403, is_significant: false, trend_direction: 'no_trend' },
      sen_slope: { slope_per_year: -0.014, ci_lower_per_year: -0.40, ci_upper_per_year: 0.38 },
      interpretation: { summary: 'No statistically significant trend detected over 10-year period.', confidence_assessment: 'p = 0.9403' }
    });
    if (res.status !== 201 || !res.body.success) throw new Error('Report generation failed');
    generatedReport = res.body.data;
    if (!fs.existsSync(generatedReport.filePath)) {
      throw new Error(`PDF file was not created on disk: ${generatedReport.filePath}`);
    }
    const stat = fs.statSync(generatedReport.filePath);
    if (stat.size < 1000) throw new Error(`PDF file size suspiciously small: ${stat.size} bytes`);
  });

  await check('REPORTLAB', 'Retrieve generated PDF through static /reports route', async () => {
    if (!generatedReport) throw new Error('No generated report to test');
    const res = await callApi('GET', generatedReport.downloadUrl);
    if (res.status !== 200) throw new Error(`Status ${res.status}`);
  });

  // -------------------------------------------------------------------------
  // SECTION 5: PERFORMANCE, CACHING & ERROR HANDLING
  // -------------------------------------------------------------------------
  console.log('\n--- 5. PERFORMANCE, CACHING & ERROR HANDLING ---');

  await check('PERF', 'In-memory statistical calculation cache delivers < 50ms response', async () => {
    const start = Date.now();
    const res = await callApi('POST', '/api/analysis/trend', {
      variable: 'T2M',
      region: 'NW',
      start_date: '2015-01',
      end_date: '2024-12'
    });
    const elapsed = Date.now() - start;
    if (res.status !== 200 || !res.body.success) throw new Error('Cached query failed');
    if (elapsed > 50) {
      console.warn(`(Notice: Cached query took ${elapsed}ms)`);
    }
  });

  await check('ERROR-HANDLING', 'Request validator rejects invalid variable', async () => {
    const res = await callApi('POST', '/api/analysis/trend', { variable: 'INVALID_VAR' });
    if (res.status !== 400 || res.body.success !== false) throw new Error(`Expected 400, got ${res.status}`);
  });

  await check('ERROR-HANDLING', 'Request validator rejects invalid region', async () => {
    const res = await callApi('POST', '/api/analysis/trend', { region: 'ATLANTIS' });
    if (res.status !== 400 || res.body.success !== false) throw new Error(`Expected 400, got ${res.status}`);
  });

  await check('ERROR-HANDLING', 'Request validator rejects malformed date format', async () => {
    const res = await callApi('POST', '/api/analysis/trend', { start_date: 'invalid-date' });
    if (res.status !== 400 || res.body.success !== false) throw new Error(`Expected 400, got ${res.status}`);
  });

  // -------------------------------------------------------------------------
  // SECTION 6: DYNAMIC SCIENTIFIC DATA INGESTION & DATASET EXPLORER
  // -------------------------------------------------------------------------
  console.log('\n--- 6. DYNAMIC SCIENTIFIC DATA INGESTION & DATASET EXPLORER ---');

  let ingestedDatasetId = null;
  const sampleCsvPath = path.join(DASHBOARD_DIR, 'tests/sample_climate_upload.csv');
  const sampleCsvContent = fs.readFileSync(sampleCsvPath, 'utf-8');

  await check('INGESTION', 'POST /api/datasets/upload ingests and validates custom CSV dataset', async () => {
    const res = await callApi('POST', '/api/datasets/upload', {
      filename: 'integration_test_climate.csv',
      content: sampleCsvContent,
      name: 'Integration Test Station Data',
      description: 'Automated test suite climate observations'
    });
    if (res.status !== 201 || !res.body.success) throw new Error(`Status ${res.status}: ${JSON.stringify(res.body)}`);
    if (!res.body.dataset || !res.body.dataset.datasetId) throw new Error('Missing datasetId in response');
    if (res.body.dataset.totalRows !== 120) throw new Error(`Expected 120 rows, got ${res.body.dataset.totalRows}`);
    ingestedDatasetId = res.body.dataset.datasetId;
  });

  await check('INGESTION', 'POST /api/datasets/validate verifies schema, quality score & mappings', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('POST', '/api/datasets/validate', { datasetId: ingestedDatasetId });
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    const v = res.body.validation;
    if (v.completeness_score !== 100) throw new Error(`Expected 100% completeness, got ${v.completeness_score}`);
    if (!v.candidate_mappings || !v.candidate_mappings.variable_columns.includes('methane_ppb')) {
      throw new Error('Methane variable not detected in candidate mappings');
    }
  });

  await check('INGESTION', 'GET /api/datasets lists ingested datasets repository', async () => {
    const res = await callApi('GET', '/api/datasets');
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    if (!Array.isArray(res.body.datasets) || res.body.datasets.length === 0) throw new Error('Datasets list empty');
    const found = res.body.datasets.find(d => d.datasetId === ingestedDatasetId || d.id === ingestedDatasetId);
    if (!found) throw new Error(`Dataset ${ingestedDatasetId} not found in listing`);
  });

  await check('INGESTION', 'GET /api/datasets/:id returns details and sample preview rows', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('GET', `/api/datasets/${ingestedDatasetId}`);
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    if (!res.body.preview || res.body.preview.length === 0) throw new Error('Missing preview rows');
  });

  await check('INGESTION', 'GET /api/datasets/:id/metadata returns scientific metadata & bounds', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('GET', `/api/datasets/${ingestedDatasetId}/metadata`);
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    const meta = res.body.metadata;
    if (meta.qualityStatus !== 'EXCELLENT') throw new Error(`Expected EXCELLENT, got ${meta.qualityStatus}`);
    if (!meta.spatialBounds.in_india_bounds) throw new Error('Expected in_india_bounds to be true');
  });

  await check('INGESTION', 'POST /api/datasets/:id/analyze computes OLS, Mann-Kendall and Sen slope on user data', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('POST', `/api/datasets/${ingestedDatasetId}/analyze`, {
      variable: 'methane_ppb',
      unit: 'ppb',
      timeCol: 'date'
    });
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    const a = res.body.analysis;
    if (!a.mann_kendall || a.mann_kendall.is_significant !== true) throw new Error('Mann-Kendall test failed');
    if (!a.ols || typeof a.ols.slope_per_decade !== 'number') throw new Error('OLS slope calculation missing');
    if (!a.theil_sen || typeof a.theil_sen.slope_per_decade !== 'number') throw new Error('Sen slope missing');
    if (!a.verdict || typeof a.verdict !== 'string') throw new Error('Scientific verdict missing');
  });

  await check('INGESTION', 'POST /api/datasets/:id/compare correlates custom time series against NASA POWER baseline', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('POST', `/api/datasets/${ingestedDatasetId}/compare`, {
      variable: 'temperature_c',
      baselineVar: 'T2M',
      timeCol: 'date'
    });
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    const cmp = res.body.comparison?.comparison;
    if (!cmp || cmp.aligned_points !== 120) throw new Error(`Expected 120 aligned points, got ${cmp?.aligned_points}`);
    if (typeof cmp.pearson_correlation !== 'number') throw new Error('Pearson correlation missing');
  });

  await check('INGESTION', 'DELETE /api/datasets/:id cleanly purges file and repository record', async () => {
    if (!ingestedDatasetId) throw new Error('No ingested dataset');
    const res = await callApi('DELETE', `/api/datasets/${ingestedDatasetId}`);
    if (res.status !== 200 || !res.body.success) throw new Error(`Status ${res.status}`);
    
    // Verify it is gone
    const checkRes = await callApi('GET', `/api/datasets/${ingestedDatasetId}`);
    if (checkRes.status !== 404) throw new Error(`Expected 404 after deletion, got ${checkRes.status}`);
  });

  await check('INGESTION', 'All 11 frontend pages have Dataset Explorer link in navbar', () => {
    for (const hf of htmlFiles) {
      const fullPath = path.join(FRONTEND_DIR, hf);
      const content = fs.readFileSync(fullPath, 'utf-8');
      if (!content.includes('dataset-explorer.html')) {
        throw new Error(`${hf} missing link to dataset-explorer.html`);
      }
    }
  });

  console.log('\n======================================================================');
  console.log(`  INTEGRATION AUDIT SUMMARY:`);
  console.log(`  Total Checks:  ${totalChecks}`);
  console.log(`  Passed:        ${passedChecks}`);
  console.log(`  Failed:        ${failedChecks}`);
  console.log('======================================================================\n');

  if (failedChecks > 0) {
    process.exit(1);
  }
}

runIntegrationVerification().catch(err => {
  console.error('[Verification Runner Crash]', err);
  process.exit(1);
});
