/**
 * Verification Test Suite for NASA Space Apps Backend REST APIs
 * Validates all endpoints using direct in-memory Express dispatch.
 */

const http = require('http');
const app = require('../backend/src/app');

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
      'user-agent': 'nasa-trend-test-suite',
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
        resolve({ status: res.statusCode, body: parsed, raw: output });
      } catch (e) {
        resolve({ status: res.statusCode, body: output, raw: output });
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

const runTests = async () => {
  console.log('======================================================================');
  console.log('  NASA SPACE APPS: RUNNING BACKEND REST API ACCEPTANCE TESTS');
  console.log('======================================================================');

  let totalTests = 0;
  let passedTests = 0;

  const test = async (name, fn) => {
    totalTests++;
    process.stdout.write(`  [Test ${totalTests}] ${name}... `);
    try {
      await fn();
      passedTests++;
      console.log('PASSED');
    } catch (err) {
      console.log('FAILED');
      console.error(`       Error: ${err.message}`);
    }
  };

  // 1. Health
  await test('GET /api/health', async () => {
    const res = await callApi('GET', '/api/health');
    if (res.status !== 200 || res.body.status !== 'healthy') throw new Error(`Unexpected status ${res.status}`);
  });

  // 2. Metadata
  await test('GET /api/metadata', async () => {
    const res = await callApi('GET', '/api/metadata');
    if (!res.body.success || !res.body.data.geographic_coverage || res.body.data.geographic_coverage.total_nodes !== 255) {
      throw new Error('Metadata missing or invalid node count');
    }
  });

  // 3. Variables
  await test('GET /api/metadata/variables', async () => {
    const res = await callApi('GET', '/api/metadata/variables');
    if (!res.body.success || !res.body.data.T2M || !res.body.data.PRECTOTCORR) {
      throw new Error('Variables missing expected T2M or PRECTOTCORR');
    }
  });

  // 4. Map Nodes (255 nodes)
  await test('GET /api/map/nodes', async () => {
    const res = await callApi('GET', '/api/map/nodes');
    if (!res.body.success || !Array.isArray(res.body.data) || res.body.data.length !== 255) {
      throw new Error(`Expected 255 nodes, got ${res.body.data?.length}`);
    }
  });

  // 5. Statistical Trend Detective Engine (T2M in Northwest India)
  await test('POST /api/analysis/trend (T2M, NW)', async () => {
    const res = await callApi('POST', '/api/analysis/trend', {
      variable: 'T2M',
      region: 'NW',
      start_date: '2015-01',
      end_date: '2024-12'
    });
    if (!res.body.success) throw new Error(res.body.message || 'Analysis failed');
    const d = res.body.data;
    if (!d.ols || !d.mann_kendall || !d.sen_slope || !d.interpretation) {
      throw new Error('Missing core statistical outputs');
    }
    if (d.date_range.n_months !== 120) {
      throw new Error(`Expected 120 months, got ${d.date_range.n_months}`);
    }
  });

  // 6. Seasonal Analysis
  await test('POST /api/analysis/seasonal (T2M, ALL)', async () => {
    const res = await callApi('POST', '/api/analysis/seasonal', {
      variable: 'T2M',
      region: 'ALL'
    });
    if (!res.body.success || !res.body.data.monthly_climatology || res.body.data.monthly_climatology.length !== 12) {
      throw new Error('Expected 12 monthly climatological means');
    }
  });

  // 7. Multi-Region Comparison
  await test('POST /api/analysis/compare (T2M)', async () => {
    const res = await callApi('POST', '/api/analysis/compare', {
      variable: 'T2M'
    });
    if (!res.body.success || !res.body.data.comparisons || res.body.data.comparisons.length < 6) {
      throw new Error('Comparison did not return all regions');
    }
  });

  // 8. Methane Pilot Observations & Caveats
  await test('GET /api/methane/summary', async () => {
    const res = await callApi('GET', '/api/methane/summary');
    if (!res.body.success || res.body.data.total_pixels_filtered !== 73045) {
      throw new Error('Methane summary mismatch');
    }
  });

  // 9. ML Evaluation Metrics & Negative R2 disclosure
  await test('GET /api/ml/metrics', async () => {
    const res = await callApi('GET', '/api/ml/metrics');
    if (!res.body.success || !res.body.data.overall_performance || res.body.data.overall_performance.mean_r2 >= 0) {
      throw new Error('Negative R2 disclosure missing or falsified');
    }
  });

  // 10. AI Research Assistant Grounded Response
  await test('POST /api/ai/chat (Trend Explanation)', async () => {
    const res = await callApi('POST', '/api/ai/chat', {
      prompt: 'Is temperature increasing in Northwest India?',
      context: {
        variable_name: 'Air Temperature at 2m',
        region_name: 'Northwest India',
        units: '°C',
        ols: { slope_per_year: 0.0036, p_value: 0.988 },
        mann_kendall: { p_value: 0.9403, is_significant: false }
      }
    });
    if (!res.body.success || !res.body.data.answer || !res.body.data.answer.includes('statistically significant')) {
      throw new Error('AI assistant response missing expected statistical explanation');
    }
  });

  // 11. PDF Report Generation
  await test('POST /api/reports/generate (Dossier PDF)', async () => {
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
    if (!res.body.success || !res.body.data.downloadUrl) {
      throw new Error('Report generation did not return downloadUrl');
    }
  });

  // 12. Frontend Homepage Route (GET /)
  await test('GET / (HTML Homepage)', async () => {
    const res = await callApi('GET', '/');
    if (res.status !== 200 || !res.raw.includes('Earth Systems Trend Detective')) {
      throw new Error('Homepage HTML failed to load');
    }
  });

  // 13. Frontend Workspace Route (GET /pages/trend-detective.html)
  await test('GET /pages/trend-detective.html (HTML Workspace)', async () => {
    const res = await callApi('GET', '/pages/trend-detective.html');
    if (res.status !== 200 || !res.raw.includes('Trend Detective')) {
      throw new Error('Trend Detective Workspace HTML failed to load');
    }
  });

  console.log(`\n======================================================`);
  console.log(`  RESULTS: ${passedTests}/${totalTests} Tests Passed successfully!`);
  console.log(`======================================================\n`);

  if (passedTests !== totalTests) {
    process.exit(1);
  }
};

runTests().catch(err => {
  console.error('[Test Suite Error]', err);
  process.exit(1);
});
