/**
 * NASA Earth Systems Trend Detective — Regional Comparison Controller
 */

class RegionalComparison {
  constructor() {
    this.currentVariable = 'T2M';
    this.init();
  }

  async init() {
    this.setupListeners();
    await this.loadComparison();
  }

  setupListeners() {
    const varSelect = document.getElementById('compare-var-select');
    if (varSelect) {
      varSelect.addEventListener('change', (e) => {
        this.currentVariable = e.target.value;
        this.loadComparison();
      });
    }
  }

  async loadComparison() {
    const tableBody = document.getElementById('compare-table-body');
    if (tableBody) tableBody.innerHTML = '<tr><td colspan="6" class="text-center"><span class="spinner"></span> Comparing regions...</td></tr>';

    try {
      const data = await window.api.getCompare({ variable: this.currentVariable });
      this.renderTable(data);
      this.renderBarChart(data);
    } catch (err) {
      console.error('[RegionalComparison] Error:', err);
      window.showToast('Failed to compare regions', 'error');
    }
  }

  renderTable(data) {
    const tableBody = document.getElementById('compare-table-body');
    if (!tableBody) return;

    const list = data.comparisons || [];
    const unit = data.units || '';

    tableBody.innerHTML = list.map(item => {
      const sign = item.sen_slope_per_year > 0 ? '+' : '';
      const sigBadge = item.is_significant
        ? `<span class="badge badge-amber"><i class="fas fa-check"></i> Significant</span>`
        : `<span class="badge badge-cyan">Natural Variability</span>`;

      return `
        <tr>
          <td><b>${item.region_name}</b> <span class="text-dim font-mono">(${item.region})</span></td>
          <td class="font-mono">${item.mean_value?.toFixed(2)} ${unit}</td>
          <td class="font-mono text-cyan">${sign}${item.sen_slope_per_year?.toFixed(4)} ${unit}/yr</td>
          <td class="font-mono">${sign}${item.sen_slope_per_decade?.toFixed(3)} ${unit}/dec</td>
          <td class="font-mono">${item.mann_kendall_p?.toFixed(4)}</td>
          <td>${sigBadge}</td>
        </tr>
      `;
    }).join('');
  }

  renderBarChart(data) {
    const chartDiv = document.getElementById('compare-chart');
    if (!chartDiv || !window.Plotly) return;

    // Filter out All India for regional rank comparison
    const regionalOnly = (data.comparisons || []).filter(c => c.region !== 'ALL');
    const regions = regionalOnly.map(c => c.region_name);
    const slopes = regionalOnly.map(c => c.sen_slope_per_year);
    const colors = slopes.map(s => s >= 0 ? '#f59e0b' : '#00f2fe');

    const trace = {
      x: regions,
      y: slopes,
      type: 'bar',
      marker: {
        color: colors,
        line: { color: '#ffffff', width: 1 }
      },
      text: slopes.map(s => `${s > 0 ? '+' : ''}${s.toFixed(4)}`),
      textposition: 'auto',
      hovertemplate: `<b>%{x}</b><br>Rate: %{y:.4f} ${data.units}/yr<extra></extra>`
    };

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'rgba(11, 17, 33, 0.6)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
      margin: { t: 30, r: 20, b: 60, l: 60 },
      yaxis: {
        title: `Sen's Robust Slope (${data.units}/year)`,
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        zerolinecolor: 'rgba(255, 255, 255, 0.2)'
      },
      xaxis: {
        tickangle: -20,
        gridcolor: 'rgba(255, 255, 255, 0.05)'
      }
    };

    Plotly.newPlot(chartDiv, [trace], layout, { responsive: true, displayModeBar: false });
  }
}

window.RegionalComparison = RegionalComparison;
