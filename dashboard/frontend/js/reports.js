/**
 * NASA Earth Systems Trend Detective — Reports & Dossiers Controller
 */

class ReportsManager {
  constructor() {
    this.init();
  }

  async init() {
    this.setupListeners();
    await this.loadHistory();
  }

  setupListeners() {
    const btn = document.getElementById('btn-create-report');
    if (btn) {
      btn.addEventListener('click', () => this.createCustomReport());
    }
  }

  async loadHistory() {
    const container = document.getElementById('reports-history-list');
    if (!container) return;

    try {
      const history = await window.api.request('/reports/history');
      if (!history || !history.length) {
        container.innerHTML = '<p class="text-dim">No previous reports generated in this session. Generate your first research dossier above.</p>';
        return;
      }

      container.innerHTML = history.map(r => `
        <div class="card" style="margin-bottom: 0.75rem; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <div style="font-weight: 700; color: #fff;">${r.title}</div>
            <div class="font-mono text-dim" style="font-size: 0.78rem;">
              Generated: ${new Date(r.createdAt).toLocaleString()} | File: ${r.fileName}
            </div>
          </div>
          <a href="${r.downloadUrl}" class="btn btn-outline-cyan btn-sm" download>
            <i class="fas fa-download"></i> Download PDF
          </a>
        </div>
      `).join('');
    } catch (err) {
      console.warn('[ReportsManager] Could not load history:', err);
    }
  }

  async createCustomReport() {
    const variable = document.getElementById('rep-var-select')?.value || 'T2M';
    const region = document.getElementById('rep-region-select')?.value || 'ALL';
    const statusEl = document.getElementById('rep-generate-status');

    if (statusEl) statusEl.innerHTML = '<span class="spinner"></span> Running statistical synthesis and generating publication PDF...';

    try {
      // First get fresh statistical analysis
      const analysisData = await window.api.getTrend({
        variable,
        region,
        start_date: '2015-01',
        end_date: '2024-12'
      });

      const report = await window.api.generateReport(analysisData);
      if (statusEl) {
        statusEl.innerHTML = `
          <div class="text-cyan" style="font-weight: 600; margin-bottom: 0.5rem;">
            <i class="fas fa-circle-check"></i> Dossier generated successfully!
          </div>
          <a href="${report.downloadUrl}" class="btn btn-primary" download>
            <i class="fas fa-file-pdf"></i> Download ${report.fileName}
          </a>
        `;
      }
      this.loadHistory();
    } catch (err) {
      if (statusEl) statusEl.innerHTML = `<span class="text-rose">Error: ${err.message}</span>`;
    }
  }
}

window.ReportsManager = ReportsManager;
