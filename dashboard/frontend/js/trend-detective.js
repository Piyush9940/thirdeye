/**
 * NASA Earth Systems Trend Detective — Workspace Controller
 * Interactive Plotly Chart, Statistical Scorecard & Real-time Hypothesis Testing
 */

class TrendDetectiveWorkspace {
  constructor() {
    this.currentVariable = 'T2M';
    this.currentRegion = 'ALL';
    this.startDate = '2015-01';
    this.endDate = '2024-12';
    this.currentData = null;

    this.init();
  }

  async init() {
    this.setupListeners();
    await this.runAnalysis();
  }

  setupListeners() {
    // Variable Selector Pills
    const varPills = document.querySelectorAll('.variable-pill');
    varPills.forEach(pill => {
      pill.addEventListener('click', (e) => {
        varPills.forEach(p => p.classList.remove('active'));
        const target = e.currentTarget;
        target.classList.add('active');
        this.currentVariable = target.getAttribute('data-var');
        this.runAnalysis();
      });
    });

    // Region Dropdown
    const regSelect = document.getElementById('region-select');
    if (regSelect) {
      regSelect.addEventListener('change', (e) => {
        this.currentRegion = e.target.value;
        this.runAnalysis();
      });
    }

    // Date Range Inputs
    const startInput = document.getElementById('start-date-input');
    const endInput = document.getElementById('end-date-input');
    if (startInput && endInput) {
      startInput.addEventListener('change', (e) => {
        this.startDate = e.target.value;
      });
      endInput.addEventListener('change', (e) => {
        this.endDate = e.target.value;
      });
    }

    // Analyze Button
    const btnAnalyze = document.getElementById('btn-analyze');
    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.runAnalysis());
    }

    // Reset Button
    const btnReset = document.getElementById('btn-reset');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        this.currentVariable = 'T2M';
        this.currentRegion = 'ALL';
        this.startDate = '2015-01';
        this.endDate = '2024-12';

        if (regSelect) regSelect.value = 'ALL';
        if (startInput) startInput.value = '2015-01';
        if (endInput) endInput.value = '2024-12';

        varPills.forEach(p => {
          if (p.getAttribute('data-var') === 'T2M') p.classList.add('active');
          else p.classList.remove('active');
        });

        this.runAnalysis();
      });
    }

    // Generate Report PDF Button
    const btnPdf = document.getElementById('btn-generate-report');
    if (btnPdf) {
      btnPdf.addEventListener('click', () => this.generatePdfReport());
    }
  }

  async runAnalysis() {
    const loadingEl = document.getElementById('chart-loading');
    if (loadingEl) loadingEl.style.display = 'flex';

    try {
      const data = await window.api.getTrend({
        variable: this.currentVariable,
        region: this.currentRegion,
        start_date: this.startDate,
        end_date: this.endDate
      });

      this.currentData = data;
      this.renderScorecard(data);
      this.renderChart(data);
      this.renderInterpretation(data);
    } catch (err) {
      console.error('[TrendDetective] Analysis failed:', err);
      window.showToast(`Failed to calculate trend: ${err.message}`, 'error');
    } finally {
      if (loadingEl) loadingEl.style.display = 'none';
    }
  }

  renderScorecard(data) {
    const sen = data.sen_slope || {};
    const ols = data.ols || {};
    const mk = data.mann_kendall || {};
    const unit = data.units || '';

    // Sen's Rate
    const elSenRate = document.getElementById('stat-sen-rate');
    const elSenDec = document.getElementById('stat-sen-decade');
    const sign = sen.slope_per_year > 0 ? '+' : '';
    if (elSenRate) elSenRate.textContent = `${sign}${sen.slope_per_year?.toFixed(4) || '0.0000'} ${unit}/yr`;
    if (elSenDec) elSenDec.textContent = `${sign}${sen.slope_per_decade?.toFixed(3) || '0.000'} ${unit}/decade`;

    // Mann-Kendall p-value
    const elPval = document.getElementById('stat-mk-pval');
    const elPvalBadge = document.getElementById('stat-mk-verdict');
    if (elPval) elPval.textContent = mk.p_value !== undefined ? mk.p_value.toFixed(4) : '—';
    if (elPvalBadge) {
      if (mk.is_significant) {
        elPvalBadge.className = 'badge badge-amber';
        elPvalBadge.textContent = 'Significant (p < 0.05)';
      } else {
        elPvalBadge.className = 'badge badge-cyan';
        elPvalBadge.textContent = 'Not Significant (p ≥ 0.05)';
      }
    }

    // Mann-Kendall Tau & S
    const elTau = document.getElementById('stat-mk-tau');
    if (elTau) elTau.textContent = `τ = ${mk.tau?.toFixed(4) || '0.0000'} (S = ${mk.S || 0})`;

    // OLS R2 & CI
    const elR2 = document.getElementById('stat-ols-r2');
    const elCi = document.getElementById('stat-ols-ci');
    if (elR2) elR2.textContent = `R² = ${ols.r_squared?.toFixed(4) || '0.0000'}`;
    if (elCi) elCi.textContent = `95% CI: [${ols.ci_lower_per_year?.toFixed(3)}, ${ols.ci_upper_per_year?.toFixed(3)}]`;
  }

  renderChart(data) {
    const chartDiv = document.getElementById('trend-chart');
    if (!chartDiv || !window.Plotly) return;

    const series = data.time_series || [];
    const dates = series.map(d => d.date);
    const values = series.map(d => d.value);
    const olsLines = series.map(d => d.trend_ols);
    const senLines = series.map(d => d.trend_sen);
    const ciUpper = series.map(d => d.ci_upper);
    const ciLower = series.map(d => d.ci_lower);

    // 1. CI Upper Bound (Invisible edge of fill)
    const traceCiUpper = {
      x: dates,
      y: ciUpper,
      type: 'scatter',
      mode: 'lines',
      line: { width: 0, color: 'rgba(0,0,0,0)' },
      showlegend: false,
      hoverinfo: 'none'
    };

    // 2. CI Lower Bound (Fills to Upper Bound)
    const traceCiLower = {
      x: dates,
      y: ciLower,
      type: 'scatter',
      mode: 'lines',
      fill: 'tonexty',
      fillcolor: 'rgba(37, 99, 235, 0.12)',
      line: { width: 0, color: 'rgba(0,0,0,0)' },
      name: '95% Confidence Band',
      hoverinfo: 'none'
    };

    // 3. Observed Monthly Means
    const traceObs = {
      x: dates,
      y: values,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'NASA POWER Observed Monthly Mean',
      line: { color: '#00f2fe', width: 2 },
      marker: { size: 5, color: '#38bdf8' },
      hovertemplate: `<b>Date:</b> %{x}<br><b>Observed:</b> %{y:.2f} ${data.units}<extra></extra>`
    };

    // 4. OLS Linear Regression Line
    const traceOls = {
      x: dates,
      y: olsLines,
      type: 'scatter',
      mode: 'lines',
      name: `OLS Fit (${data.ols?.slope_per_year > 0 ? '+' : ''}${data.ols?.slope_per_year?.toFixed(4)} ${data.units}/yr)`,
      line: { color: '#f43f5e', width: 2.5 },
      hovertemplate: `<b>OLS Trend:</b> %{y:.2f} ${data.units}<extra></extra>`
    };

    // 5. Sen's Robust Median Slope Line
    const traceSen = {
      x: dates,
      y: senLines,
      type: 'scatter',
      mode: 'lines',
      name: `Sen's Robust Slope (${data.sen_slope?.slope_per_year > 0 ? '+' : ''}${data.sen_slope?.slope_per_year?.toFixed(4)} ${data.units}/yr)`,
      line: { color: '#10b981', width: 2.5, dash: 'dot' },
      hovertemplate: `<b>Sen's Slope:</b> %{y:.2f} ${data.units}<extra></extra>`
    };

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'rgba(11, 17, 33, 0.6)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
      margin: { t: 40, r: 30, b: 60, l: 60 },
      hovermode: 'x unified',
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.12,
        font: { size: 11, color: '#f8fafc' }
      },
      xaxis: {
        title: 'Monthly Observation Timeline',
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        zerolinecolor: 'rgba(255, 255, 255, 0.1)',
        tickangle: -45,
        nticks: 20
      },
      yaxis: {
        title: `${data.variable_name} (${data.units})`,
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        zerolinecolor: 'rgba(255, 255, 255, 0.1)'
      }
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    Plotly.newPlot(chartDiv, [traceCiUpper, traceCiLower, traceObs, traceOls, traceSen], layout, config);
  }

  renderInterpretation(data) {
    const interp = data.interpretation || {};
    const titleEl = document.getElementById('interp-title');
    const textEl = document.getElementById('interp-text');
    const caveatEl = document.getElementById('interp-caveat');

    if (titleEl) {
      if (interp.is_significant) {
        titleEl.innerHTML = `<i class="fas fa-triangle-exclamation text-amber"></i> ${interp.trend_direction === 'increasing' ? 'Statistically Significant Warming Detected' : 'Statistically Significant Decreasing Trend'}`;
      } else {
        titleEl.innerHTML = `<i class="fas fa-circle-check text-cyan"></i> No Statistically Significant Trend`;
      }
    }

    if (textEl) textEl.textContent = interp.summary || '';
    if (caveatEl) caveatEl.textContent = interp.recommendation || '';
  }

  async generatePdfReport() {
    if (!this.currentData) {
      window.showToast('Please wait for analysis to load before generating report', 'error');
      return;
    }

    const btn = document.getElementById('btn-generate-report');
    if (btn) btn.innerHTML = '<span class="spinner"></span> Generating Dossier...';

    try {
      const res = await window.api.generateReport(this.currentData);
      window.showToast('Dossier generated! Starting download...', 'success');

      // Trigger download
      const link = document.createElement('a');
      link.href = res.downloadUrl;
      link.download = res.fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      window.showToast(`Failed to generate PDF: ${err.message}`, 'error');
    } finally {
      if (btn) btn.innerHTML = '<i class="fas fa-file-pdf"></i> Download Research Dossier (PDF)';
    }
  }
}

window.TrendDetectiveWorkspace = TrendDetectiveWorkspace;
