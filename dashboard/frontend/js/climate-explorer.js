/**
 * NASA Earth Systems Trend Detective — Climate Explorer Controller
 */

class ClimateExplorer {
  constructor() {
    this.currentVariable = 'T2M';
    this.currentRegion = 'ALL';
    this.init();
  }

  async init() {
    this.setupListeners();
    await this.loadClimatology();
  }

  setupListeners() {
    const varPills = document.querySelectorAll('.clim-var-pill');
    varPills.forEach(pill => {
      pill.addEventListener('click', (e) => {
        varPills.forEach(p => p.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.currentVariable = e.currentTarget.getAttribute('data-var');
        this.loadClimatology();
      });
    });

    const regSelect = document.getElementById('clim-region-select');
    if (regSelect) {
      regSelect.addEventListener('change', (e) => {
        this.currentRegion = e.target.value;
        this.loadClimatology();
      });
    }
  }

  async loadClimatology() {
    try {
      const data = await window.api.getSeasonal({
        variable: this.currentVariable,
        region: this.currentRegion
      });

      this.renderMonthlyCycleChart(data);
      this.renderSeasonalSummary(data);
    } catch (err) {
      console.error('[ClimateExplorer] Failed to load climate data:', err);
      window.showToast('Could not load climatology', 'error');
    }
  }

  renderMonthlyCycleChart(data) {
    const chartDiv = document.getElementById('climatology-chart');
    if (!chartDiv || !window.Plotly) return;

    const months = data.monthly_climatology.map(m => m.month_name);
    const means = data.monthly_climatology.map(m => m.mean);
    const mins = data.monthly_climatology.map(m => m.min);
    const maxs = data.monthly_climatology.map(m => m.max);

    const traceMin = {
      x: months,
      y: mins,
      type: 'scatter',
      mode: 'lines',
      line: { width: 0 },
      showlegend: false,
      hoverinfo: 'none'
    };

    const traceMax = {
      x: months,
      y: maxs,
      type: 'scatter',
      mode: 'lines',
      fill: 'tonexty',
      fillcolor: 'rgba(0, 242, 254, 0.1)',
      line: { width: 0 },
      name: 'Observed Range (Min-Max)',
      hoverinfo: 'none'
    };

    const traceMean = {
      x: months,
      y: means,
      type: 'scatter',
      mode: 'lines+markers',
      name: `10-Year Mean Climatology (${data.units})`,
      line: { color: '#00f2fe', width: 3 },
      marker: { size: 7, color: '#38bdf8' }
    };

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'rgba(11, 17, 33, 0.6)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
      margin: { t: 30, r: 20, b: 50, l: 60 },
      yaxis: {
        title: `${data.variable_name} (${data.units})`,
        gridcolor: 'rgba(255, 255, 255, 0.05)'
      },
      xaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.05)'
      }
    };

    Plotly.newPlot(chartDiv, [traceMin, traceMax, traceMean], layout, { responsive: true, displayModeBar: false });
  }

  renderSeasonalSummary(data) {
    const container = document.getElementById('seasonal-cards');
    if (!container) return;

    const seasons = data.seasonal_summary || [];
    const unit = data.units || '';

    container.innerHTML = seasons.map(s => `
      <div class="card">
        <div class="card-header">
          <div class="card-title">${s.season}</div>
          <span class="badge badge-cyan">${s.mean.toFixed(1)} ${unit}</span>
        </div>
        <div class="font-mono text-dim" style="font-size: 0.8rem;">
          Min: ${s.min.toFixed(1)} ${unit} | Max: ${s.max.toFixed(1)} ${unit}<br>
          Std Dev: ±${s.std.toFixed(2)}
        </div>
      </div>
    `).join('');
  }
}

window.ClimateExplorer = ClimateExplorer;
