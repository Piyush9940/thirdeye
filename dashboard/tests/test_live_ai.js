/**
 * NASA Earth Systems Trend Detective — Live AI Provider End-to-End Verification
 */
const app = require('../backend/src/app');

const mockContext = {
  variable_name: 'Air Temperature at 2m',
  variable: 'T2M',
  units: '°C',
  region_name: 'Northwest India',
  region: 'NW',
  date_range: { start: '2015-01', end: '2024-12', n_months: 120 },
  ols: { slope_per_year: 0.0245, p_value: 0.0031 },
  sen_slope: { slope_per_year: 0.0238, slope_per_decade: 0.238 },
  mann_kendall: { p_value: 0.0028, is_significant: true },
  interpretation: { summary: 'Statistically significant warming trend detected in Northwest India over 2015-2024.' }
};

const dispatchPost = (body) => new Promise((resolve) => {
  let statusCode = 200;
  const res = {
    status: (code) => { statusCode = code; return res; },
    setHeader: () => {},
    json: (data) => resolve({ status: statusCode, body: data }),
    send: (data) => resolve({ status: statusCode, body: data }),
    end: () => resolve({ status: statusCode, body: null })
  };
  const req = {
    method: 'POST',
    url: '/api/ai/chat',
    headers: { 'content-type': 'application/json' },
    body
  };
  app(req, res);
});

async function runLiveTests() {
  console.log('======================================================================');
  console.log('         LIVE AI PROVIDER & FALLBACK END-TO-END VERIFICATION          ');
  console.log('======================================================================\n');

  // Test 1: Live Gemini Provider
  console.log('1. Testing Live Gemini Provider (gemini-3.5-flash-lite)...');
  const geminiRes = await dispatchPost({
    prompt: 'Is air temperature increasing in Northwest India and is it statistically significant?',
    context: mockContext,
    provider: 'gemini'
  });
  console.log('Gemini HTTP Status:', geminiRes.status);
  console.log('Gemini Provider in response:', geminiRes.body.data?.grounded_data?.provider);
  console.log('Gemini Model:', geminiRes.body.data?.grounded_data?.model);
  console.log('Gemini Answer Preview:\n', geminiRes.body.data?.answer?.substring(0, 300) + '...\n');

  // Test 2: Live OpenAI Provider (Handling Insufficient Quota 429)
  console.log('2. Testing OpenAI Provider (with quota error -> safe fallback)...');
  const openaiRes = await dispatchPost({
    prompt: 'Is air temperature increasing in Northwest India?',
    context: mockContext,
    provider: 'openai'
  });
  console.log('OpenAI fallback HTTP Status:', openaiRes.status);
  console.log('OpenAI response provider (after fallback):', openaiRes.body.data?.grounded_data?.provider);
  console.log('Fallback Answer Preview:\n', openaiRes.body.data?.answer?.substring(0, 300) + '...\n');

  // Test 3: Explicit Grounded Provider
  console.log('3. Testing Explicit Grounded Engine Provider...');
  const groundedRes = await dispatchPost({
    prompt: 'What are the scientific limitations of satellite methane?',
    context: mockContext,
    provider: 'grounded'
  });
  console.log('Grounded HTTP Status:', groundedRes.status);
  console.log('Grounded provider:', groundedRes.body.data?.grounded_data?.provider);
  console.log('Grounded Answer Preview:\n', groundedRes.body.data?.answer?.substring(0, 300) + '...\n');

  // Test 4: Default Provider Route (No explicit provider parameter in body)
  console.log('4. Testing Default Provider Route (POST /api/ai/chat default)...');
  const defaultRes = await dispatchPost({
    prompt: 'Summarize the warming rate and significance in Northwest India',
    context: mockContext
  });
  console.log('Default HTTP Status:', defaultRes.status);
  console.log('Default response provider:', defaultRes.body.data?.grounded_data?.provider);
  console.log('Default Answer Preview:\n', defaultRes.body.data?.answer?.substring(0, 300) + '...\n');

  console.log('======================================================================');
  console.log('         LIVE AI INTEGRATION VERIFICATION COMPLETE                    ');
  console.log('======================================================================');
}

runLiveTests().catch(err => {
  console.error('Test error:', err);
  process.exit(1);
});
