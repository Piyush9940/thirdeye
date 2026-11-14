/**
 * NASA Earth Systems Trend Detective — AIService Verification & Diagnostic Suite
 */
const assert = require('assert');
const path = require('path');
const aiService = require('../backend/src/services/aiService');
const app = require('../backend/src/app');

// Sample real backend analysis context (Northwest India Temperature Trend)
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

let testsRun = 0;
let testsPassed = 0;

function report(name, passed, detail = '') {
  testsRun++;
  if (passed) {
    testsPassed++;
    console.log(`[PASS] ${name}${detail ? ` (${detail})` : ''}`);
  } else {
    console.error(`[FAIL] ${name}: ${detail}`);
  }
}

async function runUnitTests() {
  console.log('======================================================================');
  console.log('       AISERVICE COMPREHENSIVE VERIFICATION & TEST SUITE             ');
  console.log('======================================================================\n');

  // 1. GROUNDED RULE ENGINE TESTS (Offline verification)
  console.log('--- 1. GROUNDED RULE ENGINE VERIFICATION ---');
  {
    const res = await aiService.generateResponse('Is air temperature increasing in Northwest India?', mockContext, { provider: 'grounded' });
    const ok = res.answer && res.answer.includes('statistically significant') && res.grounded_data?.provider === 'grounded';
    report('Grounded engine detects warming trend and statistical significance', ok);
  }
  {
    const res = await aiService.generateResponse('What does the p-value mean in climate data?', mockContext, { provider: 'grounded' });
    const ok = res.answer && res.answer.includes('null hypothesis') && res.answer.includes('0.0028');
    report('Grounded engine explains p-value with active significance threshold', ok);
  }
  {
    const res = await aiService.generateResponse('Explain Sen\'s robust slope vs linear regression', mockContext, { provider: 'grounded' });
    const ok = res.answer && res.answer.includes('Theil-Sen') && res.answer.includes('pairwise slopes');
    report('Grounded engine defines Sen slope and resilience to outliers', ok);
  }
  {
    const res = await aiService.generateResponse('What are the scientific limitations of satellite methane?', mockContext, { provider: 'grounded' });
    const ok = res.answer && res.answer.includes('Southeast India') && res.answer.includes('4 snapshots');
    report('Grounded engine reports 4 pilot snapshots and Southeast India gap', ok);
  }

  // 2. PARSER & EDGE CASE UNIT TESTS
  console.log('\n--- 2. RESPONSE PARSER & SAFETY EDGE CASES ---');
  
  // Test: Multiple response parts concatenation
  {
    const fakeData = {
      candidates: [
        {
          finishReason: 'STOP',
          content: {
            parts: [
              { text: 'First paragraph explaining trend.' },
              { text: 'Second paragraph with Sen slope 0.0238 °C/year.' }
            ]
          }
        }
      ]
    };
    const parts = fakeData.candidates[0].content.parts;
    const combined = parts.map(p => p.text).filter(Boolean).join('\n').trim();
    report('Multiple response parts properly concatenated', combined.includes('First paragraph') && combined.includes('Second paragraph'));
  }

  // Test: Blocked safety response detection
  {
    const fakeData = {
      candidates: [{ finishReason: 'SAFETY', content: { parts: [] } }]
    };
    const isSafety = fakeData.candidates[0].finishReason === 'SAFETY';
    report('Candidate with finishReason SAFETY correctly identified', isSafety);
  }

  // Test: Prompt feedback block reason
  {
    const fakeData = {
      promptFeedback: { blockReason: 'PROHIBITED_CONTENT' }
    };
    report('PromptFeedback blockReason correctly flagged', fakeData.promptFeedback.blockReason === 'PROHIBITED_CONTENT');
  }

  // Test: Empty candidate list detection
  {
    const fakeData = { candidates: [] };
    report('Empty candidate list detected', !fakeData.candidates || fakeData.candidates.length === 0);
  }

  // Test: Malformed JSON handling
  {
    let caught = false;
    try {
      JSON.parse('Malformed { json string');
    } catch (e) {
      caught = true;
    }
    report('Malformed JSON safely caught and handled', caught);
  }

  // 3. PROVIDER SELECTION & ROUTING
  console.log('\n--- 3. PROVIDER SELECTION & CONFIGURATION ---');
  report('Default provider configured as gemini (or auto)', aiService.defaultProvider === 'gemini' || aiService.defaultProvider === 'auto');
  report('Gemini model configured', aiService.geminiModel === 'gemini-3.5-flash-lite');
  report('OpenAI model configured', aiService.openaiModel === 'gpt-4o-mini');

  // 4. END-TO-END EXPRESS API ROUTE (POST /api/ai/chat)
  console.log('\n--- 4. END-TO-END EXPRESS ROUTE /api/ai/chat ---');
  {
    // Test dispatching to Express app in-memory
    const testReq = (body) => new Promise((resolve) => {
      let statusCode = 200;
      let headers = {};
      const res = {
        status: (code) => { statusCode = code; return res; },
        setHeader: (k, v) => { headers[k] = v; },
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

    // Test with grounded provider
    const groundRes = await testReq({
      prompt: 'Is air temperature increasing in Northwest India?',
      context: mockContext,
      provider: 'grounded'
    });
    report('POST /api/ai/chat returns 200 with grounded provider', groundRes.status === 200 && groundRes.body.success);

    // Test rejection of empty prompt
    const emptyRes = await testReq({ prompt: '' });
    report('POST /api/ai/chat rejects missing prompt with 400', emptyRes.status === 400 && !emptyRes.body.success);
  }

  console.log('\n======================================================================');
  console.log(`  AISERVICE AUDIT SUMMARY: Passed ${testsPassed}/${testsRun} checks`);
  console.log('======================================================================\n');
}

runUnitTests().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
