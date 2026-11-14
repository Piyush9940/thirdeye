/**
 * NASA Earth Systems Trend Detective — Sentinel-5P Methane Module
 */

class MethaneAnalysis {
  constructor() {
    this.init();
  }

  async init() {
    try {
      const data = await window.api.getMethaneSummary();
      this.renderSnapshots(data);
      this.renderRegions(data);
    } catch (err) {
      console.error('[MethaneAnalysis] Error:', err);
      window.showToast('Could not load methane data', 'error');
    }
  }

  renderSnapshots(data) {
    const list = document.getElementById('methane-snapshots');
    if (!list) return;

    list.innerHTML = (data.snapshots || []).map(s => `
      <div class="stat-card">
        <div class="stat-header">${s.season} • ${s.period}</div>
        <div class="stat-value text-cyan">${s.valid_nodes} Nodes</div>
        <div class="stat-sub">Mean: ${s.mean_ppb.toFixed(1)} ppb</div>
        <div class="stat-sub" style="font-size: 0.72rem; color: var(--text-dim); margin-top: 4px;">${s.description}</div>
      </div>
    `).join('');
  }

  renderRegions(data) {
    const body = document.getElementById('methane-regions-body');
    if (!body) return;

    body.innerHTML = (data.regions || []).map(r => {
      const isMissing = r.pixel_count === 0;
      const statusBadge = isMissing
        ? `<span class="badge badge-rose"><i class="fas fa-ban"></i> Data Gap (0 Soundings)</span>`
        : `<span class="badge badge-emerald"><i class="fas fa-satellite"></i> ${r.pixel_count.toLocaleString()} Pixels</span>`;

      return `
        <tr class="${isMissing ? 'bg-rose-subtle' : ''}">
          <td><b>${r.name}</b> <span class="font-mono text-dim">(${r.code})</span></td>
          <td>${statusBadge}</td>
          <td class="font-mono">${r.median_ppb ? r.median_ppb.toFixed(2) + ' ppb' : '<span class="text-rose">N/A (Gap)</span>'}</td>
          <td style="font-size: 0.85rem; color: var(--text-muted);">${r.notes}</td>
        </tr>
      `;
    }).join('');
  }
}

window.MethaneAnalysis = MethaneAnalysis;
