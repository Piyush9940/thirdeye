/**
 * NASA Earth Systems Trend Detective — Node.js ML Endpoint Verification Suite
 */
const assert = require('assert');
const app = require('../backend/src/app');

const dispatchReq = (method, url, body = null) => new Promise((resolve) => {
  let statusCode = 200;
  const res = {
    status: (code) => { statusCode = code; return res; },
    setHeader: () => {},
    json: (data) => resolve({ status: statusCode, body: data }),
    send: (data) => resolve({ status: statusCode, body: data }),
    end: () => resolve({ status: statusCode, body: null })
  };
  const req = {
    method,
    url,
    headers: { 'content-type': 'application/json' },
    body
  };
  app(req, res);
});

async function runNodeMLTests() {
  console.log('======================================================================');
  console.log('         NODE.JS ML ROUTE & SERVICE CLIENT TEST SUITE                 ');
  console.log('======================================================================\n');

  let passed = 0;
  let total = 0;

  function report(name, ok, detail = '') {
    total++;
    if (ok) {
      passed++;
      console.log(`[PASS] ${name}${detail ? ` (${detail})` : ''}`);
    } else {
      console.error(`[FAIL] ${name}: ${detail}`);
    }
  }

  // 1. GET /api/ml/health
  {
    const res = await dispatchReq('GET', '/api/ml/health');
    const ok = res.status === 200 && res.body.data?.status === 'healthy';
    report('GET /api/ml/health returns healthy status', ok, `checkpoints: ${res.body.data?.checkpoints_found}`);
  }

  // 2. GET /api/ml/metadata
  {
    const res = await dispatchReq('GET', '/api/ml/metadata');
    const ok = res.status === 200 && res.body.data?.architecture;
    report('GET /api/ml/metadata returns model architecture', ok);
  }

  // 3. GET /api/ml/metrics
  {
    const res = await dispatchReq('GET', '/api/ml/metrics');
    const ok = res.status === 200 && res.body.data?.model_comparison?.length >= 4;
    report('GET /api/ml/metrics returns model benchmark rankings', ok, `rankings: ${res.body.data?.model_comparison?.length}`);
  }

  // 4. GET /api/ml/predictions
  {
    const res = await dispatchReq('GET', '/api/ml/predictions?limit=10');
    const ok = res.status === 200 && res.body.data?.predictions?.length === 10;
    report('GET /api/ml/predictions returns historical cross-validation records', ok, `total: ${res.body.data?.total_records}`);
  }

  // 5. POST /api/ml/inference (Forward Pass)
  {
    const res = await dispatchReq('POST', '/api/ml/inference', {
      fold: 1,
      seed: 42,
      features: {
        T2M: 26.5,
        PRECTOTCORR: 4.2,
        RH2M: 65.0,
        WS10M: 3.1,
        latitude: 23.0,
        longitude: 83.0
      }
    });
    const ok = res.status === 200 && res.body.data?.prediction_ppb > 1700;
    report('POST /api/ml/inference returns valid methane prediction', ok, `${res.body.data?.prediction_ppb} ppb`);
  }

  // 6. POST /api/ml/batch (Empty items rejection)
  {
    const res = await dispatchReq('POST', '/api/ml/batch', {
      fold: 1,
      seed: 42,
      items: []
    });
    report('POST /api/ml/batch rejects empty items with 400', res.status === 400);
  }

  console.log('\n======================================================================');
  console.log(`  NODE.JS ML ROUTE AUDIT: Passed ${passed}/${total} checks`);
  console.log('======================================================================\n');
}

runNodeMLTests().catch(err => {
  console.error('Test error:', err);
  process.exit(1);
});
