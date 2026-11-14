const env = require('../config/environment');
const logger = require('../utils/logger');

class AIService {
  constructor() {
    this.geminiModel = env.GEMINI_MODEL || 'gemini-3.5-flash-lite';
    this.openaiModel = env.OPENAI_MODEL || 'gpt-4o-mini';
    this.defaultProvider = env.AI_PROVIDER || (env.GEMINI_API_KEY ? 'gemini' : (env.OPENAI_API_KEY ? 'openai' : 'grounded'));
  }

  /**
   * Generates a context-grounded AI answer to environmental inquiries.
   * @param {string} prompt User question
   * @param {object} context Active analysis context (variable, region, statistics, interpretation)
   * @param {object} options Optional execution parameters (e.g. { provider: 'gemini' | 'openai' | 'grounded' })
   */
  async generateResponse(prompt, context = {}, options = {}) {
      const selectedProvider = (options.provider || context.provider || this.defaultProvider || 'grounded').toLowerCase();

        // 1. Explicit Grounded Rule Engine
        if (selectedProvider === 'grounded') {
          return this._generateGroundedResponse(prompt, context);
        }

        // 2. Gemini Provider
        if (selectedProvider === 'gemini') {
          if (!env.GEMINI_API_KEY) {
            logger.warn('[AIService] Gemini provider requested but GEMINI_API_KEY is not configured. Falling back to grounded rule engine.');
            return this._generateGroundedResponse(prompt, context);
          }
          try {
            return await this._callGemini(prompt, context);
          } catch (err) {
            logger.warn(`[AIService] Gemini API call failed: ${err.message}. Falling back to grounded rule engine.`);
            return this._generateGroundedResponse(prompt, context);
          }
        }

        // 3. OpenAI Provider
        if (selectedProvider === 'openai') {
          if (!env.OPENAI_API_KEY) {
            logger.warn('[AIService] OpenAI provider requested but OPENAI_API_KEY is not configured. Falling back to grounded rule engine.');
            return this._generateGroundedResponse(prompt, context);
          }
          try {
            return await this._callOpenAI(prompt, context);
          } catch (err) {
            logger.warn(`[AIService] OpenAI API call failed: ${err.message}. Falling back to grounded rule engine.`);
            return this._generateGroundedResponse(prompt, context);
          }
        }

        // 4. Auto / Cascading Provider
        if (selectedProvider === 'auto') {
          if (env.GEMINI_API_KEY) {
            try {
              return await this._callGemini(prompt, context);
            } catch (err) {
              logger.warn(`[AIService] Gemini auto-call failed: ${err.message}. Trying next available provider.`);
            }
          }
          if (env.OPENAI_API_KEY) {
            try {
              return await this._callOpenAI(prompt, context);
            } catch (err) {
              logger.warn(`[AIService] OpenAI auto-call failed: ${err.message}. Falling back to grounded engine.`);
            }
          }
          return this._generateGroundedResponse(prompt, context);
        }

        // Default unknown fallback
        logger.warn(`[AIService] Unknown provider '${selectedProvider}'. Using grounded rule engine.`);
        return this._generateGroundedResponse(prompt, context);
      }

      _buildSystemPrompt(context) {
        const varName = context.variable_name || context.variable || 'Target Climate Variable';
        const regName = context.region_name || context.region || 'Selected Region';
        const units = context.units || '';
        const nMonths = context.date_range?.n_months ?? 120;
        const dateStart = context.date_range?.start ?? '2015-01';
        const dateEnd = context.date_range?.end ?? '2024-12';
        const olsSlope = context.ols?.slope_per_year !== undefined ? `${context.ols.slope_per_year} ${units}/year (p = ${context.ols.p_value})` : 'Not computed';
        const senSlope = context.sen_slope?.slope_per_year !== undefined ? `${context.sen_slope.slope_per_year} ${units}/year` : 'Not computed';
        const senDecade = context.sen_slope?.slope_per_decade !== undefined ? `${context.sen_slope.slope_per_decade} ${units}/decade` : 'Not computed';
        const mkP = context.mann_kendall?.p_value !== undefined ? `${context.mann_kendall.p_value}` : 'Not computed';
        const mkSig = context.mann_kendall?.is_significant !== undefined ? (context.mann_kendall.is_significant ? 'Yes (statistically significant)' : 'No (not statistically significant)') : 'Unknown';
        const summary = context.interpretation?.summary || 'Standard environmental time-series trend analysis.';

        return `You are an expert scientific research assistant for the NASA Space Apps platform "Earth Systems Trend Detective".
You strictly answer environmental questions based on verified backend observations:
- Variable: ${varName} (${units})
- Region: ${regName}
- Observation Window: ${nMonths} monthly observations (${dateStart} to ${dateEnd})
- OLS Linear Rate: ${olsSlope}
- Sen's Robust Rate: ${senSlope} (${senDecade})
- Mann-Kendall Significance: p = ${mkP}, Significant: ${mkSig}
- Scientific Summary: ${summary}

Core Scientific Rules:
1. Ground answers strictly in the figures above. Never invent numerical values or claim continuous methane coverage.
2. Sentinel-5P atmospheric methane is an exploratory 4-snapshot pilot (May 2019, Feb 2021, Aug 2021, Nov 2023).
3. Southeast India has 0 valid soundings in the pilot release due to optical cloud filtering (QA >= 0.50). Always describe it as unavailable observations, never zero concentration.
4. Total atmospheric column XCH4 (ppb) is NOT direct surface emissions flux.
5. Keep explanations scientifically rigorous, educational, concise, and accessible.`;
      }

  async _callGemini(prompt, context) {
        const model = this.geminiModel;
        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`;
        const systemPrompt = this._buildSystemPrompt(context);

        const payload = {
          contents: [
            {
              role: 'user',
              parts: [{ text: `${systemPrompt}\n\nUser Question: ${prompt}` }]
            }
          ],
          generationConfig: {
            temperature: 0.2,
            maxOutputTokens: 1024
          }
        };

        let res;
        try {
          res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } catch (netErr) {
          throw new Error(`Network failure connecting to Gemini: ${netErr.message}`);
        }

        let data;
        try {
          data = await res.json();
        } catch (parseErr) {
          throw new Error(`Gemini response is not valid JSON (HTTP ${res.status}): ${parseErr.message}`);
        }

        // Handle non-OK HTTP status codes safely without leaking keys
        if (!res.ok) {
          const errMsg = data?.error?.message || res.statusText || 'Unknown Gemini error';
          const errCode = data?.error?.code || res.status;
          const errStatus = data?.error?.status || '';
          throw new Error(`Gemini API HTTP ${errCode}${errStatus ? ` (${errStatus})` : ''}: ${errMsg}`);
        }

        // Inspect safety or prompt blocking
        if (data.promptFeedback?.blockReason) {
          throw new Error(`Gemini blocked prompt: ${data.promptFeedback.blockReason}`);
        }

        const candidate = data.candidates?.[0];
        if (!candidate) {
          throw new Error('Gemini returned an empty candidate list');
        }

        if (candidate.finishReason === 'SAFETY') {
          throw new Error('Gemini response blocked by content safety filters');
        }

        const parts = candidate.content?.parts;
        if (!parts || !Array.isArray(parts) || parts.length === 0) {
          throw new Error('Gemini candidate has no content parts');
        }

        const candidateText = parts.map(p => p.text).filter(Boolean).join('\n').trim();
        if (!candidateText) {
          throw new Error('Gemini candidate text is empty');
        }

        return {
          answer: candidateText,
          grounded_data: {
            provider: 'gemini',
            model,
            finish_reason: candidate.finishReason || 'STOP',
            usage: data.usageMetadata || null
          }
        };
      }

  async _callOpenAI(prompt, context) {
        const model = this.openaiModel;
        const endpoint = 'https://api.openai.com/v1/chat/completions';
        const systemPrompt = this._buildSystemPrompt(context);

        const payload = {
          model,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
          ],
          temperature: 0.2,
          max_tokens: 1024
        };

        let res;
        try {
          res = await fetch(endpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${env.OPENAI_API_KEY}`
            },
            body: JSON.stringify(payload)
          });
        } catch (netErr) {
          throw new Error(`Network failure connecting to OpenAI: ${netErr.message}`);
        }

        let data;
        try {
          data = await res.json();
        } catch (parseErr) {
          throw new Error(`OpenAI response is not valid JSON (HTTP ${res.status}): ${parseErr.message}`);
        }

        if (!res.ok) {
          const errMsg = data?.error?.message || res.statusText || 'Unknown OpenAI error';
          const errCode = data?.error?.code || res.status;
          const errType = data?.error?.type || '';
          throw new Error(`OpenAI API HTTP ${res.status} [${errCode || errType}]: ${errMsg}`);
        }

        const choice = data.choices?.[0];
        if (!choice) {
          throw new Error('OpenAI returned an empty choice list');
        }

        if (choice.finish_reason === 'content_filter') {
          throw new Error('OpenAI response blocked by content filter');
        }

        const content = (choice.message?.content || '').trim();
        if (!content) {
          throw new Error('OpenAI response content is empty');
        }

        return {
          answer: content,
          grounded_data: {
            provider: 'openai',
            model,
            finish_reason: choice.finish_reason || 'stop',
            usage: data.usage || null
          }
        };
      }

      _generateGroundedResponse(prompt, context) {
        const q = prompt.toLowerCase();
        const varName = context.variable_name || context.variable || 'Target Climate Variable';
        const regName = context.region_name || context.region || 'Selected Region';
        const unit = context.units || '';
        const ols = context.ols || {};
        const mk = context.mann_kendall || {};
        const sen = context.sen_slope || {};
        const dRange = context.date_range || {};

        const slopeYr = sen.slope_per_year ?? ols.slope_per_year;
        const slopeDec = sen.slope_per_decade ?? (slopeYr !== undefined ? slopeYr * 10 : undefined);
        const pVal = mk.p_value ?? ols.p_value;
        const isSig = mk.is_significant ?? (pVal !== undefined ? pVal < 0.05 : false);
        const sign = slopeYr > 0 ? '+' : '';

        // Intent 1: Is it increasing / decreasing / changing?
        if (q.includes('increasing') || q.includes('decreasing') || q.includes('warming') || q.includes('changing') || q.includes('trend')) {
          if (slopeYr === undefined) {
            return {
              answer: `To evaluate whether the trend is increasing or decreasing, please run an analysis first on the Trend Detective workspace. Select a variable (such as Air Temperature or Precipitation) and a region to inspect the computed slope and Mann-Kendall significance.`,
          grounded_data: { prompt, context_present: false, provider: 'grounded' }
            };
          }

          if (isSig) {
            const direction = slopeYr > 0 ? 'increasing (warming)' : 'decreasing (cooling)';
            return {
              answer: `Yes. Over the 10-year period (${dRange.start || '2015-01'} to ${dRange.end || '2024-12'}), **${varName}** in **${regName}** demonstrates a **statistically significant ${direction} trend**.\n\n` +
                `• **Robust Rate of Change (Sen's Slope):** ${sign}${slopeYr.toFixed(4)} ${unit}/year (${sign}${slopeDec.toFixed(3)} ${unit}/decade).\n` +
                `• **Statistical Test:** Mann-Kendall rank test yielded *p* = ${pVal.toFixed(4)}, which is strictly below the significance threshold (α = 0.05).\n` +
                `• **Confidence:** We reject the null hypothesis of no trend with 95% statistical confidence.`,
          grounded_data: { variable: varName, region: regName, slope_per_year: slopeYr, p_value: pVal, is_significant: true, provider: 'grounded' }
            };
          } else {
            return {
              answer: `No statistically significant long-term trend was detected for **${varName}** in **${regName}** over this period.\n\n` +
                `• **Observed Rate:** ${sign}${slopeYr ? slopeYr.toFixed(4) : '0.0000'} ${unit}/year (${sign}${slopeDec ? slopeDec.toFixed(3) : '0.000'} ${unit}/decade).\n` +
                `• **Mann-Kendall p-value:** *p* = ${pVal ? pVal.toFixed(4) : 'N/A'}, which is greater than the standard threshold (α = 0.05).\n` +
                `• **Scientific Meaning:** The observed month-to-month fluctuations fall within expected natural climatological variability and do not constitute a persistent trajectory over this 120-month window.`,
          grounded_data: { variable: varName, region: regName, slope_per_year: slopeYr, p_value: pVal, is_significant: false, provider: 'grounded' }
            };
          }
        }

        // Intent 2: What does the p-value mean?
        if (q.includes('p-value') || q.includes('p value') || q.includes('significance')) {
          return {
            answer: `In environmental trend detection, the **p-value** measures the probability that the observed change happened purely by random climate noise (the *null hypothesis*):\n\n` +
              `• **Calculated Value:** *p* = ${pVal !== undefined ? pVal.toFixed(4) : '0.05'}.\n` +
              `• **Significance Threshold (α = 0.05):** If *p* < 0.05, there is less than a 5% chance that random variation produced this pattern, allowing us to conclude that a real, persistent directional trend exists.\n` +
              `• **Current Analysis Result:** ${isSig ? `Since *p* (${pVal.toFixed(4)}) < 0.05, the trend is **statistically significant**.` : `Since *p* (${pVal ? pVal.toFixed(4) : '0.94'}) >= 0.05, the trend is **not statistically significant**.`}`,
        grounded_data: { p_value: pVal, alpha: 0.05, is_significant: isSig, provider: 'grounded' }
          };
        }

        // Intent 3: What is Sen's slope?
        if (q.includes('sen') || q.includes("sen's") || q.includes('theil-sen')) {
          return {
            answer: `**Theil-Sen Robust Slope** (or Sen's slope) is a non-parametric statistical estimator for measuring rates of change in environmental time series:\n\n` +
              `• **How it works:** It computes the slope between all possible pairs of points in the time series and takes the **median** of all pairwise slopes.\n` +
              `• **Why it matters:** Unlike standard Ordinary Least Squares (OLS) linear regression, Sen's slope is **immune to seasonal spikes and extreme outliers** (such as cyclone rainfall or heatwaves).\n` +
              `• **In this investigation:** Sen's slope for ${varName} in ${regName} is **${sign}${slopeYr !== undefined ? slopeYr.toFixed(4) : '0.0000'} ${unit}/year**.`,
        grounded_data: { sen_slope: slopeYr, units: unit, provider: 'grounded' }
          };
        }

        // Intent 4: Limitations and data caveats
        if (q.includes('limitation') || q.includes('caveat') || q.includes('gap') || q.includes('accuracy') || q.includes('methane')) {
          return {
            answer: `Here are the core scientific limitations governing this platform:\n\n` +
              `1. **Continuous Climate vs Sparse Methane:** NASA POWER climate variables (temperature, precipitation, humidity, wind) span a continuous 10-year monthly record (2015–2024, 30,600 rows). In contrast, Sentinel-5P atmospheric methane is an exploratory pilot of **4 snapshots** (May 2019, Feb 2021, Aug 2021, Nov 2023).\n` +
              `2. **Atmospheric Column vs Surface Emissions:** Sentinel-5P measures total column dry-air mole fraction (XCH4 in ppb). Atmospheric concentrations reflect wind advection and atmospheric transport, and **must never be equated to direct surface emissions fluxes** without inverse modeling.\n` +
              `3. **Monsoon Cloud Coverage & Southeast India Gap:** Optical satellite soundings require cloud-free conditions (QA >= 0.50). In August 2021 (Fold 2), only 11 soundings survived monsoon filtering across India. Furthermore, Southeast India had 0 valid soundings in the pilot release and is represented as unavailable observations, never zero.\n` +
              `4. **Experimental ML Status:** Our PyTorch neural network checkpoints represent exploratory research. Negative R² indicates spatial sparsity and that the model is not production-approved for operational forecasting.`,
        grounded_data: { climate_records: 30600, methane_snapshots: 4, ml_status: 'experimental', provider: 'grounded' }
          };
        }

        // Default intelligent overview
        return {
          answer: `Hello! I am your **NASA Earth Systems Trend Detective Research Assistant**.\n\n` +
            `Currently loaded context:\n` +
            `• **Target Variable:** ${varName} (${unit})\n` +
            `• **Geographic Scope:** ${regName}\n` +
            `• **Observed Trajectory:** ${sign}${slopeYr !== undefined ? slopeYr.toFixed(4) : 'N/A'} ${unit}/year (${isSig ? 'Statistically Significant' : 'No Significant Trend'})\n` +
            `• **Confidence:** Mann-Kendall *p* = ${pVal !== undefined ? pVal.toFixed(4) : 'N/A'}\n\n` +
            `You can ask me questions such as:\n` +
            `- *"Is temperature increasing in this region?"*\n` +
            `- *"What does the p-value mean?"*\n` +
            `- *"How does Sen's slope differ from linear regression?"*\n` +
            `- *"What are the scientific limitations of satellite methane data?"*`,
      grounded_data: { variable: varName, region: regName, slope: slopeYr, p_value: pVal, provider: 'grounded' }
        };
      }
    }

    module.exports = new AIService();
