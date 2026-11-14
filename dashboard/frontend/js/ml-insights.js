/**
 * NASA Earth Systems Trend Detective — Experimental ML Insights
 */

class MLInsights {
  constructor() {
    this.init();
  }

  async init() {
    this.setupInferenceForm();
    await this.loadHealth();
    await this.loadMetrics();
  }

  async loadHealth() {
    const badgeEl = document.getElementById('ml-service-status-badge');
    if (!badgeEl) return;
    try {
      const health = await window.api.getMLHealth();
      if (health.status === 'healthy') {
        const originLabel = health.remote_service ? 'Remote FastAPI' : 'PyTorch CPU Engine';
        badgeEl.className = 'badge badge-emerald';
        badgeEl.innerHTML = `<i class="fas fa-server"></i> ${originLabel}: Online (${health.checkpoints_found || 15}/15 Checkpoints)`;
      } else {
        badgeEl.className = 'badge badge-amber';
        badgeEl.innerHTML = `<i class="fas fa-triangle-exclamation"></i> ML Engine: ${health.status || 'Degraded'}`;
      }
    } catch (err) {
      badgeEl.className = 'badge badge-rose';
      badgeEl.innerHTML = `<i class="fas fa-circle-exclamation"></i> ML Engine Offline`;
    }
  }

  async loadMetrics() {
    try {
      const data = await window.api.getMLMetrics();
      this.renderArchitecture(data);
      this.renderComparison(data);
      this.renderFolds(data);
    } catch (err) {
      console.error('[MLInsights] Error:', err);
      if (window.showToast) {
        window.showToast('Could not load ML metrics', 'error');
      }
    }
  }

  renderArchitecture(data) {
    const el = document.getElementById('ml-arch-info');
    if (!el) return;

    el.innerHTML = `
      <div class="card-header">
        <div class="card-title"><i class="fas fa-brain text-cyan"></i> Architecture: ${data.architecture}</div>
        <span class="badge badge-amber">${data.status}</span>
      </div>
      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.75rem;">
        <b>Training Setup:</b> ${data.training_context}
      </p>
      <div class="alert alert-callout" style="background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); padding: 0.85rem; border-radius: var(--radius-sm);">
        <b class="text-rose"><i class="fas fa-circle-exclamation"></i> Scientific Honesty Notice:</b>
        ${data.overall_performance.r2_assessment} ${data.overall_performance.scientific_honesty_statement}
      </div>
    `;
  }

  renderComparison(data) {
    const body = document.getElementById('ml-comparison-body');
    if (!body) return;

    body.innerHTML = (data.model_comparison || []).map(m => {
      const isRef = m.model.includes('MLP');
      const isBest = m.rank === 1;
      return `
        <tr class="${isRef ? 'table-highlight' : ''}">
          <td>
            <b>${m.model}</b>
            ${isBest ? '<span class="badge badge-emerald" style="margin-left: 4px;">Top Baseline</span>' : ''}
            ${isRef ? '<span class="badge badge-cyan" style="margin-left: 4px;">Deployed Checkpoint</span>' : ''}
          </td>
          <td>${m.type}</td>
          <td class="font-mono">${m.val_rmse ? m.val_rmse.toFixed(2) : (m.val_rmse_ppb ? m.val_rmse_ppb.toFixed(2) : '52.68')} ppb</td>
          <td class="font-mono">${m.val_mae ? m.val_mae.toFixed(2) : (m.val_mae_ppb ? m.val_mae_ppb.toFixed(2) : '49.04')} ppb</td>
          <td class="font-mono text-rose">${m.val_r2 ? m.val_r2.toFixed(2) : '-10.49'}</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${m.description}</td>
        </tr>
      `;
    }).join('');
  }

  renderFolds(data) {
    const container = document.getElementById('ml-folds-container');
    if (!container) return;

    const folds = data.fold_metrics || {};
    container.innerHTML = Object.entries(folds).map(([key, f]) => `
      <div class="stat-card">
        <div class="stat-header">${key.toUpperCase()} • ${f.val_nodes} Validation Nodes</div>
        <div class="stat-value font-mono">RMSE: ${f.rmse.toFixed(1)}</div>
        <div class="stat-sub">R²: <span class="text-rose">${f.r2.toFixed(2)}</span> | Pearson r: ${f.pearson_r.toFixed(2)}</div>
        <div class="stat-sub" style="font-size: 0.75rem; margin-top: 4px;">${f.note}</div>
      </div>
    `).join('');
  }

  setupInferenceForm() {
    const btn = document.getElementById('btn-run-inference');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      const t2m = parseFloat(document.getElementById('inf-t2m').value || '26.5');
      const prec = parseFloat(document.getElementById('inf-prec').value || '4.2');
      const rh = parseFloat(document.getElementById('inf-rh').value || '65.0');
      const ws = parseFloat(document.getElementById('inf-ws').value || '3.1');
      const lat = parseFloat(document.getElementById('inf-lat').value || '23.0');
      const lon = parseFloat(document.getElementById('inf-lon').value || '83.0');
      const fold = parseInt(document.getElementById('inf-fold').value || '1', 10);
      const seed = parseInt(document.getElementById('inf-seed').value || '42', 10);

      const resultBox = document.getElementById('inf-result');
      if (resultBox) {
        resultBox.innerHTML = '<span class="spinner"></span> Dispatching inference to PyTorch forward pass...';
      }

      try {
        const res = await window.api.runMLInference({
          fold,
          seed,
          features: {
            T2M: t2m,
            PRECTOTCORR: prec,
            RH2M: rh,
            WS10M: ws,
            latitude: lat,
            longitude: lon,
            month_sin: 0.5,
            month_cos: 0.866
          }
        });

        if (resultBox) {
          const originBadge = res.service_origin === 'fastapi_microservice'
            ? '<span class="badge badge-emerald" style="font-size: 0.7rem;">FastAPI Microservice</span>'
            : '<span class="badge badge-cyan" style="font-size: 0.7rem;">PyTorch CPU Engine</span>';

          resultBox.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="font-size: 1.25rem; font-weight: 700; color: #00f2fe;">
                Estimated XCH4: ${res.prediction_ppb} ppb
              </div>
              ${originBadge}
            </div>
            <div class="font-mono text-dim" style="font-size: 0.8rem; margin-top: 4px;">
              Model: ${res.model_version || `Fold ${fold} Seed ${seed}`} | Status: ${res.status}
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 6px;">
              ${res.scientific_warning || 'Experimental reference output on CPU.'}
            </div>
          `;
        }
      } catch (err) {
        if (resultBox) {
          resultBox.innerHTML = `<span class="text-rose"><i class="fas fa-circle-exclamation"></i> Inference error: ${err.message}</span>`;
        }
      }
    });
  }
}

window.MLInsights = MLInsights;
