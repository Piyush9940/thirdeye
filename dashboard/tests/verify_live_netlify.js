const https = require('https');

const BASE_URL = 'https://earth-systems-trend-detective.netlify.app';

const pages = [
  '/',
  '/index.html',
  '/pages/trend-detective.html',
  '/pages/dataset-explorer.html',
  '/pages/overview.html',
  '/pages/earth-explorer.html',
  '/pages/regional-comparison.html',
  '/pages/climate-explorer.html',
  '/pages/methane-analysis.html',
  '/pages/ml-insights.html',
  '/pages/ai-assistant.html',
  '/pages/reports.html'
];

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    }).on('error', reject);
  });
}

async function run() {
  console.log('======================================================================');
  console.log('   LIVE NETLIFY FRONTEND PUBLIC DEPLOYMENT VERIFICATION              ');
  console.log('   Target: ' + BASE_URL);
  console.log('======================================================================\n');

  let total = 0;
  let passed = 0;
  let failed = 0;

  for (const page of pages) {
    total++;
    const url = `${BASE_URL}${page}`;
    try {
      const res = await fetchUrl(url);
      if (res.statusCode === 200 && res.body.length > 500 && res.body.includes('<!DOCTYPE html>')) {
        console.log(`[PASS] ${page} -> HTTP 200 OK (${res.body.length.toLocaleString()} bytes)`);
        passed++;
      } else {
        console.error(`[FAIL] ${page} -> HTTP ${res.statusCode} (length: ${res.body.length})`);
        failed++;
      }
    } catch (err) {
      console.error(`[FAIL] ${page} -> Error: ${err.message}`);
      failed++;
    }
  }

  // Verify ml-insights.html specific interactive DOM elements
  console.log('\n--- VERIFYING ML-INSIGHTS INTERACTIVE DOM ASSETS ---');
  total++;
  try {
    const mlPage = await fetchUrl(`${BASE_URL}/pages/ml-insights.html`);
    const requiredElements = [
      'id="ml-service-status-badge"',
      'id="btn-run-inference"',
      'id="inf-t2m"',
      'id="inf-prec"',
      'id="inf-rh"',
      'id="inf-ws"',
      'id="inf-lat"',
      'id="inf-lon"',
      'id="inf-fold"',
      'id="inf-seed"',
      'id="inf-result"',
      'id="ml-comparison-body"'
    ];

    const missing = requiredElements.filter(el => !mlPage.body.includes(el));
    if (missing.length === 0) {
      console.log(`[PASS] All 12 interactive ML sandbox DOM elements verified in live HTML`);
      passed++;
    } else {
      console.error(`[FAIL] Missing DOM elements: ${missing.join(', ')}`);
      failed++;
    }
  } catch (err) {
    console.error(`[FAIL] ML DOM inspection error: ${err.message}`);
    failed++;
  }

  // Verify static CSS and JS bundles
  console.log('\n--- VERIFYING LIVE CSS AND JAVASCRIPT ASSETS ---');
  const staticAssets = [
    '/css/main.css',
    '/js/api.js',
    '/js/ml-insights.js',
    '/js/trend-detective.js',
    '/js/dataset-explorer.js'
  ];

  for (const asset of staticAssets) {
    total++;
    try {
      const res = await fetchUrl(`${BASE_URL}${asset}`);
      if (res.statusCode === 200 && res.body.length > 100) {
        console.log(`[PASS] ${asset} -> HTTP 200 OK (${res.body.length.toLocaleString()} bytes)`);
        passed++;
      } else {
        console.error(`[FAIL] ${asset} -> HTTP ${res.statusCode}`);
        failed++;
      }
    } catch (err) {
      console.error(`[FAIL] ${asset} -> Error: ${err.message}`);
      failed++;
    }
  }

  console.log('\n======================================================================');
  console.log(`  PUBLIC FRONTEND AUDIT: Total: ${total} | Passed: ${passed} | Failed: ${failed}`);
  console.log('======================================================================');

  if (failed > 0) process.exit(1);
}

run();
