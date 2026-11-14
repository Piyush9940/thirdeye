/**
 * NASA Earth Systems Trend Detective
 * Dashboard Visualizations Controller (10 Interactive Plotly Charts)
 */

document.addEventListener('DOMContentLoaded', async () => {
  const periodFilter = document.getElementById('periodFilter');
  const regionFilter = document.getElementById('regionFilter');
  const resetBtn = document.getElementById('resetFiltersBtn');
  const statusText = document.getElementById('filterStatusText');

  // Load KPIs
  try {
    const kpiRes = await API.getDashboardKPIs();
    if (kpiRes && kpiRes.data) {
      const d = kpiRes.data;
      document.getElementById('kpiNodes').textContent = d.spatialNodesCount || 255;
      document.getElementById('kpiObservations').textContent = d.observationRecordsCount || 226;
      document.getElementById('kpiPredictions').textContent = d.evaluationPredictionsCount || 720;
    }
  } catch (e) {
    console.warn('KPI load error:', e);
  }

  // Common Plotly Dark Layout
  const baseLayout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 11 },
    margin: { t: 25, r: 25, b: 45, l: 55 },
    autosize: true,
    xaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      zerolinecolor: 'rgba(0, 210, 255, 0.15)',
      tickfont: { size: 10, color: '#94a3b8' }
    },
    yaxis: {
      gridcolor: 'rgba(255, 255, 255, 0.05)',
      zerolinecolor: 'rgba(0, 210, 255, 0.15)',
      tickfont: { size: 10, color: '#94a3b8' }
    }
  };

  const config = { responsive: true, displayModeBar: false };

  async function loadAndRenderCharts() {
    const period = periodFilter.value;
    const region = regionFilter.value;

    statusText.textContent = `Rendering: Period [${period}], Region [${region}]...`;

    try {
      const res = await API.getDashboardCharts(period, region);
      if (!res || !res.data) throw new Error('No chart data returned');
      const data = res.data;

      // 1. Chart 1: Methane Concentration Distribution (Histogram)
      Plotly.newPlot('chartCH4Distribution', [{
        x: data.ch4Values,
        type: 'histogram',
        nbinsx: 20,
        marker: {
          color: '#00d2ff',
          line: { color: 'rgba(255,255,255,0.3)', width: 1 }
        },
        opacity: 0.85,
        hovertemplate: 'Concentration: %{x:.1f} ppb<br>Count: %{y}<extra></extra>'
      }], {
        ...baseLayout,
        xaxis: { ...baseLayout.xaxis, title: { text: 'CH₄ Concentration (ppb)', font: { size: 11 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Node Count', font: { size: 11 } } }
      }, config);

      // 2. Chart 2: Regional Methane Comparison (Box Plot)
      const regTraces = Object.entries(data.regionalData).map(([regName, vals]) => ({
        y: vals,
        type: 'box',
        name: regName.replace('_', ' '),
        boxpoints: 'all',
        jitter: 0.3,
        pointpos: -1.8,
        marker: { size: 4, color: '#38bdf8' },
        line: { width: 1.5 }
      }));
      Plotly.newPlot('chartRegionalComparison', regTraces, {
        ...baseLayout,
        showlegend: false,
        yaxis: { ...baseLayout.yaxis, title: { text: 'Median CH₄ (ppb)', font: { size: 11 } } }
      }, config);

      // 3. Chart 3: Temporal Distribution (Bar chart)
      const periods = Object.keys(data.periodsCount);
      const counts = Object.values(data.periodsCount);
      Plotly.newPlot('chartPeriodCounts', [{
        x: periods,
        y: counts,
        type: 'bar',
        marker: {
          color: ['#10b981', '#38bdf8', '#f59e0b', '#00d2ff'],
          line: { color: 'rgba(255,255,255,0.2)', width: 1 }
        },
        text: counts.map(c => `${c} nodes`),
        textposition: 'auto',
        hovertemplate: 'Period: %{x}<br>Observed Nodes: %{y}<extra></extra>'
      }], {
        ...baseLayout,
        xaxis: { ...baseLayout.xaxis, title: { text: 'Observation Period', font: { size: 11 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Observed Nodes Count', font: { size: 11 } } }
      }, config);

      // 4. Chart 4: Climate Variable Distributions (Box Plots)
      const cDist = data.climateDist;
      Plotly.newPlot('chartClimateDist', [
        { y: cDist.T2M, type: 'box', name: 'T2M (°C)', marker: { color: '#ef4444' } },
        { y: cDist.PRECTOTCORR, type: 'box', name: 'Precip (mm/d)', marker: { color: '#38bdf8' } },
        { y: cDist.RH2M, type: 'box', name: 'RH2M (%)', marker: { color: '#10b981' } },
        { y: cDist.WS10M, type: 'box', name: 'WS10M (m/s)', marker: { color: '#f59e0b' } }
      ], {
        ...baseLayout,
        showlegend: false,
        yaxis: { ...baseLayout.yaxis, title: { text: 'Parameter Values', font: { size: 11 } } }
      }, config);

      // 5. Chart 5: Observed vs Predicted (Scatter with 1:1 line)
      const actuals = data.obsVsPred.map(d => d.actual);
      const preds = data.obsVsPred.map(d => d.predicted);
      const minVal = Math.min(...actuals, ...preds) - 10;
      const maxVal = Math.max(...actuals, ...preds) + 10;

      Plotly.newPlot('chartObsVsPred', [
        {
          x: actuals,
          y: preds,
          mode: 'markers',
          type: 'scatter',
          marker: { color: '#00d2ff', size: 6, opacity: 0.8 },
          name: 'Evaluations',
          hovertemplate: 'Actual: %{x:.1f} ppb<br>Pred: %{y:.1f} ppb<extra></extra>'
        },
        {
          x: [minVal, maxVal],
          y: [minVal, maxVal],
          mode: 'lines',
          line: { dash: 'dash', color: '#f59e0b', width: 1.5 },
          name: '1:1 Ideal Line'
        }
      ], {
        ...baseLayout,
        showlegend: true,
        legend: { x: 0.05, y: 0.95, font: { color: '#94a3b8', size: 10 } },
        xaxis: { ...baseLayout.xaxis, title: { text: 'Observed CH₄ (ppb)', font: { size: 11 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Predicted CH₄ (ppb)', font: { size: 11 } } }
      }, config);

      // 6. Chart 6: Model Evaluation Metrics by Fold
      const foldLabels = data.foldMetrics.map(f => `Fold ${f.fold} (${f.evaluation_period})`);
      const maes = data.foldMetrics.map(f => f.mean_MAE_ppb);
      const rmses = data.foldMetrics.map(f => f.mean_RMSE_ppb);
      const r2s = data.foldMetrics.map(f => f.mean_R2);

      Plotly.newPlot('chartFoldMetrics', [
        { x: foldLabels, y: maes, type: 'bar', name: 'MAE (ppb)', marker: { color: '#38bdf8' } },
        { x: foldLabels, y: rmses, type: 'bar', name: 'RMSE (ppb)', marker: { color: '#f59e0b' } },
        { x: foldLabels, y: r2s, type: 'scatter', mode: 'lines+markers', yaxis: 'y2', name: 'R²', line: { color: '#ef4444', width: 2 } }
      ], {
        ...baseLayout,
        barmode: 'group',
        showlegend: true,
        legend: { x: 0.02, y: 1.15, orientation: 'h', font: { size: 10 } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Error (ppb)', font: { size: 11 } } },
        yaxis2: {
          title: { text: 'R² Score', font: { size: 11, color: '#ef4444' } },
          tickfont: { color: '#ef4444' },
          overlaying: 'y',
          side: 'right',
          gridcolor: 'transparent'
        }
      }, config);

      // 7. Chart 7: Seed Stability (15 Seed-level metrics)
      const seedNums = data.seedStability.map(s => `F${s.fold}-S${s.seed}`);
      const seedMaes = data.seedStability.map(s => s.MAE_ppb);

      Plotly.newPlot('chartSeedStability', [{
        x: seedNums,
        y: seedMaes,
        type: 'bar',
        marker: {
          color: data.seedStability.map(s => s.fold === 1 ? '#38bdf8' : (s.fold === 2 ? '#f59e0b' : '#10b981'))
        },
        hovertemplate: 'Fold/Seed: %{x}<br>MAE: %{y:.2f} ppb<extra></extra>'
      }], {
        ...baseLayout,
        xaxis: { ...baseLayout.xaxis, title: { text: 'Fold & Seed Configurations', font: { size: 10 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'MAE (ppb)', font: { size: 11 } } }
      }, config);

      // 8. Chart 8: Prediction Error Distribution
      Plotly.newPlot('chartErrorDist', [{
        x: data.errorDist,
        type: 'histogram',
        nbinsx: 25,
        marker: { color: '#ef4444', line: { color: 'rgba(255,255,255,0.2)', width: 1 } },
        hovertemplate: 'Residual (Pred - Act): %{x:.1f} ppb<br>Count: %{y}<extra></extra>'
      }], {
        ...baseLayout,
        shapes: [{
          type: 'line',
          x0: 0, x1: 0,
          y0: 0, y1: 1,
          yref: 'paper',
          line: { color: '#ffffff', dash: 'dash', width: 1.5 }
        }],
        xaxis: { ...baseLayout.xaxis, title: { text: 'Prediction Error (ppb)', font: { size: 11 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Evaluation Row Count', font: { size: 11 } } }
      }, config);

      // 9. Chart 9: Spatial Grid Node Observation Status (Pie/Donut)
      Plotly.newPlot('chartSpatialCoverage', [{
        labels: ['Observed Nodes (98)', 'Unobserved / Filtered (157)'],
        values: [data.coverageStats.observedNodesCount, data.coverageStats.unobservedNodesCount],
        type: 'pie',
        hole: 0.55,
        marker: { colors: ['#00d2ff', '#334155'] },
        textinfo: 'label+percent',
        insidetextfont: { color: '#ffffff', size: 10 }
      }], {
        ...baseLayout,
        showlegend: false
      }, config);

      // 10. Chart 10: Missingness & Observation Coverage by Period
      const totalNodes = data.coverageStats.totalNodes;
      const covPeriods = Object.keys(data.coverageStats.periodBreakdown);
      const covCounts = Object.values(data.coverageStats.periodBreakdown);
      const unobsCounts = covCounts.map(c => totalNodes - c);

      Plotly.newPlot('chartMissingness', [
        {
          x: covPeriods,
          y: covCounts.map(c => ((c / totalNodes) * 100).toFixed(1)),
          name: '% Observed',
          type: 'bar',
          marker: { color: '#10b981' }
        },
        {
          x: covPeriods,
          y: unobsCounts.map(u => ((u / totalNodes) * 100).toFixed(1)),
          name: '% Unobserved / Filtered',
          type: 'bar',
          marker: { color: '#475569' }
        }
      ], {
        ...baseLayout,
        barmode: 'stack',
        showlegend: true,
        legend: { x: 0.05, y: 1.15, orientation: 'h', font: { size: 10 } },
        xaxis: { ...baseLayout.xaxis, title: { text: 'Period', font: { size: 11 } } },
        yaxis: { ...baseLayout.yaxis, title: { text: 'Grid Node Coverage (%)', font: { size: 11 } } }
      }, config);

      statusText.textContent = `Active: ${period === 'ALL' ? 'All Periods' : period} • ${region === 'ALL' ? 'All India' : region.replace('_', ' ')}`;
    } catch (err) {
      console.error('Error loading dashboard charts:', err);
      statusText.textContent = `Error loading charts: ${err.message}`;
    }
  }

  // Bind filter events
  periodFilter.addEventListener('change', loadAndRenderCharts);
  regionFilter.addEventListener('change', loadAndRenderCharts);
  resetBtn.addEventListener('click', () => {
    periodFilter.value = 'ALL';
    regionFilter.value = 'ALL';
    loadAndRenderCharts();
  });

  // Initial render
  loadAndRenderCharts();
});
