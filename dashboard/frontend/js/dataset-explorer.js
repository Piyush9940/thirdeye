/**
 * NASA Earth Systems Trend Detective — Dynamic Dataset Ingestion & Scientific Explorer
 */

document.addEventListener('DOMContentLoaded', () => {
  let selectedFile = null;
  let currentDatasetId = null;
  let currentDataset = null;
  let currentValidation = null;

  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const datasetNameInput = document.getElementById('dataset-name-input');
  const datasetDescInput = document.getElementById('dataset-desc-input');
  const btnUploadSubmit = document.getElementById('btn-upload-submit');
  const btnLoadSample = document.getElementById('btn-load-sample');
  const btnRunAnalysis = document.getElementById('btn-run-analysis');
  const btnTriggerCompare = document.getElementById('btn-trigger-compare');
  const btnRefreshDatasets = document.getElementById('btn-refresh-datasets');

  const mappingCard = document.getElementById('mapping-card');
  const previewCard = document.getElementById('preview-card');
  const analysisSection = document.getElementById('analysis-results-section');
  const datasetsTableBody = document.getElementById('datasets-table-body');

  const mapTimeCol = document.getElementById('map-time-col');
  const mapVarCol = document.getElementById('map-var-col');
  const mapUnit = document.getElementById('map-unit');
  const mapLatCol = document.getElementById('map-lat-col');
  const mapLonCol = document.getElementById('map-lon-col');

  // Drag and Drop Handlers
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files.length > 0) {
      handleFileSelected(dt.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    dropzone.querySelector('h3').textContent = `Selected: ${file.name}`;
    dropzone.querySelector('p').textContent = `Size: ${(file.size / 1024).toFixed(1)} KB | Ready for upload`;
    btnUploadSubmit.disabled = false;
    if (!datasetNameInput.value) {
      datasetNameInput.value = file.name.replace(/\.[^/.]+$/, "");
    }
  }

  // Upload & Ingest Submit
  btnUploadSubmit.addEventListener('click', async () => {
    if (!selectedFile) return;

    btnUploadSubmit.disabled = true;
    btnUploadSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating & Ingesting...';

    try {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Data = reader.result.split(',')[1];
          const payload = {
            filename: selectedFile.name,
            content: base64Data,
            isBase64: true,
            name: datasetNameInput.value || selectedFile.name,
            description: datasetDescInput.value || 'User-uploaded scientific observation dataset'
          };

          const res = await api.uploadDataset(payload);
          if (res && res.dataset) {
            currentDatasetId = res.dataset.datasetId;
            currentDataset = res.dataset;
            displayValidationScorecard(res.dataset);
            populateMappingDropdowns(res.dataset);
            renderPreviewTable(res.preview || []);
            loadDatasetsLibrary();

            if (window.showToast) {
              window.showToast('Scientific dataset successfully validated and ingested!', 'success');
            }
          }
        } catch (err) {
          alert(`Dataset ingestion error: ${err.message}`);
        } finally {
          btnUploadSubmit.disabled = false;
          btnUploadSubmit.innerHTML = '<i class="fas fa-upload"></i> Upload & Validate Dataset';
        }
      };
      reader.readAsDataURL(selectedFile);
    } catch (err) {
      btnUploadSubmit.disabled = false;
      btnUploadSubmit.innerHTML = '<i class="fas fa-upload"></i> Upload & Validate Dataset';
      alert(`Upload error: ${err.message}`);
    }
  });

  // Load Sample India Dataset
  btnLoadSample.addEventListener('click', async () => {
    btnLoadSample.disabled = true;
    btnLoadSample.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating 10-Yr Sample...';

    try {
      // Generate 120-month India climate & methane sample
      const dates = [];
      const rows = ["date,latitude,longitude,temperature_c,methane_ppb,precipitation_mm"];
      let d = new Date(2015, 0, 1);
      
      for (let i = 0; i < 120; i++) {
        const ymStr = d.toISOString().slice(0, 10);
        const temp = (24.0 + 0.03 * i + 5.0 * Math.sin(2 * Math.PI * i / 12) + (Math.random() - 0.5)).toFixed(2);
        const ch4 = (1880 + 0.82 * i + (Math.random() - 0.5) * 8).toFixed(1);
        const prec = Math.max(0, (2.5 + 4.0 * Math.sin(2 * Math.PI * (i - 5) / 12) + (Math.random() - 0.5) * 2)).toFixed(2);
        rows.push(`${ymStr},28.61,77.23,${temp},${ch4},${prec}`);
        d.setMonth(d.getMonth() + 1);
      }

      const csvContent = rows.join("\n");
      const base64Content = btoa(csvContent);

      const payload = {
        filename: "india_delhi_climate_methane_10yr.csv",
        content: base64Content,
        isBase64: true,
        name: "North India Ground Station (10-Yr Climate & CH4)",
        description: "120 monthly observations (2015–2024) across temperature, methane, and precipitation at Delhi reference node."
      };

      const res = await api.uploadDataset(payload);
      if (res && res.dataset) {
        currentDatasetId = res.dataset.datasetId;
        currentDataset = res.dataset;
        displayValidationScorecard(res.dataset);
        populateMappingDropdowns(res.dataset);
        renderPreviewTable(res.preview || []);
        loadDatasetsLibrary();

        if (window.showToast) {
          window.showToast('Pre-loaded 10-year India sample dataset ingested!', 'success');
        }

        // Auto-trigger analysis on methane_ppb
        setTimeout(() => {
          if (mapVarCol.querySelector('option[value="methane_ppb"]')) {
            mapVarCol.value = "methane_ppb";
            mapUnit.value = "ppb";
          }
          btnRunAnalysis.click();
        }, 400);
      }
    } catch (err) {
      alert(`Sample loading error: ${err.message}`);
    } finally {
      btnLoadSample.disabled = false;
      btnLoadSample.innerHTML = '<i class="fas fa-flask"></i> Load Sample India Dataset';
    }
  });

  // Display Quality & Validation Scorecard
  function displayValidationScorecard(dataset) {
    document.getElementById('val-rows-cols').textContent = `${dataset.totalRows} rows / ${dataset.totalColumns} cols`;
    document.getElementById('val-filesize').textContent = `Size: ${(dataset.fileSize / 1024).toFixed(1)} KB | Clean format`;
    document.getElementById('val-completeness').textContent = `${dataset.completenessScore}%`;

    const badge = document.getElementById('quality-badge');
    badge.className = `badge-quality ${dataset.qualityStatus.toLowerCase()}`;
    badge.innerHTML = `<i class="fas fa-circle-check"></i> ${dataset.qualityStatus} Quality`;

    const tempRange = dataset.temporalRange || {};
    if (tempRange.has_temporal) {
      document.getElementById('val-temporal-span').textContent = `${tempRange.min_date.slice(0,7)} → ${tempRange.max_date.slice(0,7)}`;
      document.getElementById('val-frequency').textContent = `Frequency: ${tempRange.estimated_frequency} (${tempRange.time_points_count} timesteps)`;
    } else {
      document.getElementById('val-temporal-span').textContent = 'Sequential Steps';
      document.getElementById('val-frequency').textContent = 'Frequency: Irregular';
    }

    const spatBounds = dataset.spatialBounds || {};
    if (spatBounds.has_spatial) {
      document.getElementById('val-spatial-bounds').textContent = `${spatBounds.lat_min}°N, ${spatBounds.lon_min}°E`;
      document.getElementById('val-spatial-status').textContent = spatBounds.in_india_bounds ? "Domain: India Subcontinent Verified" : "Domain: Global / Regional Bounds";
    } else {
      document.getElementById('val-spatial-bounds').textContent = 'Non-spatial / Station';
      document.getElementById('val-spatial-status').textContent = 'Domain: Single Point Time Series';
    }

    const auditList = document.getElementById('audit-notes-list');
    auditList.innerHTML = '';
    (dataset.auditNotes || []).forEach(note => {
      const li = document.createElement('li');
      li.innerHTML = `<i class="fas fa-check-circle text-cyan"></i> ${note}`;
      auditList.appendChild(li);
    });

    mappingCard.style.display = 'block';
    previewCard.style.display = 'block';
  }

  // Populate Mapping Dropdowns
  function populateMappingDropdowns(dataset) {
    const candidates = dataset.candidateMappings || {};
    const suggested = dataset.suggestedMapping || {};
    const allCols = (dataset.columns || []).map(c => c.name);

    // Time col
    mapTimeCol.innerHTML = '<option value="">-- Auto-detect / Timestep Index --</option>';
    allCols.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col;
      if (suggested.time_col === col || (candidates.time_columns && candidates.time_columns.includes(col))) {
        opt.selected = true;
      }
      mapTimeCol.appendChild(opt);
    });

    // Target Variable
    mapVarCol.innerHTML = '';
    const numericCols = (dataset.columns || []).filter(c => c.is_numeric).map(c => c.name);
    numericCols.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col;
      if (suggested.variable_col === col || (candidates.variable_columns && candidates.variable_columns.includes(col))) {
        opt.selected = true;
      }
      mapVarCol.appendChild(opt);
    });

    // Auto set unit
    updateUnitPlaceholder();

    // Lat col
    mapLatCol.innerHTML = '<option value="">-- None / Fixed Station --</option>';
    allCols.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col;
      if (suggested.lat_col === col) opt.selected = true;
      mapLatCol.appendChild(opt);
    });

    // Lon col
    mapLonCol.innerHTML = '<option value="">-- None / Fixed Station --</option>';
    allCols.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col;
      if (suggested.lon_col === col) opt.selected = true;
      mapLonCol.appendChild(opt);
    });
  }

  mapVarCol.addEventListener('change', updateUnitPlaceholder);

  function updateUnitPlaceholder() {
    const v = (mapVarCol.value || '').toLowerCase();
    if (v.includes('temp') || v.includes('t2m')) mapUnit.value = '°C';
    else if (v.includes('ch4') || v.includes('methane')) mapUnit.value = 'ppb';
    else if (v.includes('co2')) mapUnit.value = 'ppm';
    else if (v.includes('prec') || v.includes('rain')) mapUnit.value = 'mm/day';
    else if (v.includes('wind') || v.includes('speed')) mapUnit.value = 'm/s';
    else if (v.includes('rh') || v.includes('humidity')) mapUnit.value = '%';
    else mapUnit.value = 'units';
  }

  // Render Ingested Preview Table
  function renderPreviewTable(rows) {
    if (!rows || rows.length === 0) return;

    document.getElementById('preview-row-count').textContent = `${rows.length} sample rows`;
    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');

    const headers = Object.keys(rows[0]);
    thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;

    tbody.innerHTML = rows.map(r => {
      return `<tr>${headers.map(h => `<td>${r[h] !== null && r[h] !== undefined ? r[h] : '<span style="color:#64748b">null</span>'}</td>`).join('')}</tr>`;
    }).join('');
  }

  // Run Statistical Trend Analysis
  btnRunAnalysis.addEventListener('click', async () => {
    if (!currentDatasetId) return;

    const variable = mapVarCol.value;
    if (!variable) {
      alert('Please select a target environmental variable to analyze.');
      return;
    }

    btnRunAnalysis.disabled = true;
    btnRunAnalysis.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Computing Mann-Kendall & OLS...';

    try {
      const params = {
        variable: variable,
        unit: mapUnit.value || 'units',
        timeCol: mapTimeCol.value || undefined,
        latCol: mapLatCol.value || undefined,
        lonCol: mapLonCol.value || undefined
      };

      const res = await api.analyzeDataset(currentDatasetId, params);
      if (res && res.analysis) {
        renderAnalysisResults(res.analysis);
        analysisSection.style.display = 'block';
        analysisSection.scrollIntoView({ behavior: 'smooth' });

        if (window.showToast) {
          window.showToast('Scientific statistical investigation complete!', 'success');
        }
      }
    } catch (err) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      btnRunAnalysis.disabled = false;
      btnRunAnalysis.innerHTML = '<i class="fas fa-calculator"></i> Run Statistical Trend Analysis';
    }
  });

  // Render Analysis Results & Charts
  function renderAnalysisResults(analysis) {
    const ols = analysis.ols || {};
    const mk = analysis.mann_kendall || {};
    const sen = analysis.theil_sen || {};
    const summary = analysis.summary || {};
    const unit = analysis.unit || 'units';

    // 1. Verdict Banner
    const banner = document.getElementById('user-verdict-banner');
    const title = document.getElementById('user-verdict-title');
    const text = document.getElementById('user-verdict-text');

    text.textContent = analysis.verdict;
    if (mk.is_significant) {
      if ((sen.slope_per_year || 0) > 0) {
        banner.className = 'verdict-banner significant-warming';
        title.innerHTML = '<i class="fas fa-arrow-trend-up"></i> Statistically Significant Increasing Trend Detected';
      } else {
        banner.className = 'verdict-banner significant-cooling';
        title.innerHTML = '<i class="fas fa-arrow-trend-down"></i> Statistically Significant Decreasing Trend Detected';
      }
    } else {
      banner.className = 'verdict-banner no-trend';
      title.innerHTML = '<i class="fas fa-arrows-left-right"></i> No Statistically Significant Trend (Stationary)';
    }

    // 2. Scorecard
    const rateSign = (sen.slope_per_decade || 0) > 0 ? '+' : '';
    document.getElementById('user-rate-val').textContent = `${rateSign}${sen.slope_per_decade !== null ? sen.slope_per_decade : '--'} ${unit}`;
    document.getElementById('user-rate-sub').textContent = `Theil-Sen: ${rateSign}${sen.slope_per_year || 0} ${unit}/yr`;

    document.getElementById('user-p-val').textContent = `p = ${mk.p_value !== null ? mk.p_value.toFixed(4) : '--'}`;
    document.getElementById('user-sig-badge').textContent = mk.is_significant ? `Significant (p < 0.05, S = ${mk.S})` : `H₀ Accepted (p ≥ 0.05, S = ${mk.S})`;

    document.getElementById('user-r2-val').textContent = ols.r_squared !== null ? ols.r_squared.toFixed(4) : '--';
    document.getElementById('user-corr-val').textContent = `Pearson r = ${ols.correlation !== null ? ols.correlation.toFixed(3) : '--'}`;

    const netSign = (summary.net_change || 0) > 0 ? '+' : '';
    document.getElementById('user-net-val').textContent = `${netSign}${summary.net_change !== null ? summary.net_change : '--'} ${unit}`;
    document.getElementById('user-obs-val').textContent = `${summary.n_observations || 0} observations (${summary.pct_change || 0}%)`;

    // 3. Plotly Interactive Chart
    const ts = analysis.time_series || [];
    const dates = ts.map(p => p.date);
    const observed = ts.map(p => p.observed);
    const olsFit = ts.map(p => p.ols_fitted);
    const senFit = ts.map(p => p.sen_fitted);
    const ciLower = ts.map(p => p.ci_lower);
    const ciUpper = ts.map(p => p.ci_upper);

    const traces = [
      // 95% Confidence Band
      {
        x: dates.concat([...dates].reverse()),
        y: ciUpper.concat([...ciLower].reverse()),
        fill: 'toself',
        fillcolor: 'rgba(0, 240, 255, 0.12)',
        line: { color: 'transparent' },
        name: '95% Confidence Interval',
        showlegend: true,
        type: 'scatter',
        hoverinfo: 'skip'
      },
      // Observed Values
      {
        x: dates,
        y: observed,
        mode: 'lines+markers',
        name: `Observed ${analysis.variable}`,
        line: { color: '#00f0ff', width: 2 },
        marker: { size: 5, color: '#00f0ff', symbol: 'circle' },
        type: 'scatter'
      },
      // Theil-Sen Median Slope
      {
        x: dates,
        y: senFit,
        mode: 'lines',
        name: "Theil-Sen Median Fit",
        line: { color: '#00ff88', width: 2.5, dash: 'solid' },
        type: 'scatter'
      },
      // OLS Linear Regression
      {
        x: dates,
        y: olsFit,
        mode: 'lines',
        name: `OLS Fit (R²=${ols.r_squared})`,
        line: { color: '#ffb800', width: 2, dash: 'dash' },
        type: 'scatter'
      }
    ];

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'rgba(10, 25, 47, 0.4)',
      font: { color: '#cbd5e1', family: 'Inter, sans-serif' },
      margin: { l: 60, r: 30, t: 30, b: 50 },
      xaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.06)',
        zerolinecolor: 'rgba(255, 255, 255, 0.1)',
        title: 'Observation Timeline'
      },
      yaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.06)',
        zerolinecolor: 'rgba(255, 255, 255, 0.1)',
        title: `${analysis.variable} (${unit})`
      },
      legend: {
        orientation: 'h',
        y: 1.12,
        x: 0,
        font: { size: 11 }
      },
      hovermode: 'x unified'
    };

    Plotly.newPlot('user-trend-plot', traces, layout, { responsive: true, displayModeBar: true });
  }

  // Trigger Climatological Comparison
  btnTriggerCompare.addEventListener('click', async () => {
    if (!currentDatasetId) return;

    btnTriggerCompare.disabled = true;
    btnTriggerCompare.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Comparing...';

    try {
      const baselineVar = document.getElementById('compare-baseline-select').value;
      const res = await api.compareDataset(currentDatasetId, {
        variable: mapVarCol.value,
        baselineVar: baselineVar,
        timeCol: mapTimeCol.value || undefined
      });

      if (res && res.comparison) {
        renderComparisonResults(res.comparison);
      }
    } catch (err) {
      alert(`Comparison failed: ${err.message}`);
    } finally {
      btnTriggerCompare.disabled = false;
      btnTriggerCompare.innerHTML = '<i class="fas fa-arrows-rotate"></i> Compare';
    }
  });

  // Render Climatological Comparison Chart & Metrics
  function renderComparisonResults(cmpData) {
    const cmp = cmpData.comparison || {};
    document.getElementById('cmp-corr-val').textContent = cmp.pearson_correlation !== null ? cmp.pearson_correlation.toFixed(3) : 'N/A';
    document.getElementById('cmp-rmse-val').textContent = cmp.rmse !== null ? cmp.rmse.toFixed(3) : 'N/A';
    document.getElementById('cmp-mae-val').textContent = cmp.mae !== null ? cmp.mae.toFixed(3) : 'N/A';
    document.getElementById('cmp-bias-val').textContent = cmp.mean_bias !== null ? `${cmp.mean_bias > 0 ? '+' : ''}${cmp.mean_bias.toFixed(3)}` : 'N/A';

    const series = cmpData.aligned_series || [];
    if (series.length === 0) {
      alert("No overlapping time periods found between user dataset and NASA POWER baseline.");
      return;
    }

    const dates = series.map(p => p.date);
    const uVals = series.map(p => p.user_value);
    const bVals = series.map(p => p.baseline_value);

    const traces = [
      {
        x: dates,
        y: uVals,
        mode: 'lines+markers',
        name: `User: ${cmpData.variable}`,
        line: { color: '#00f0ff', width: 2 },
        marker: { size: 5, color: '#00f0ff' },
        type: 'scatter'
      },
      {
        x: dates,
        y: bVals,
        mode: 'lines',
        name: `NASA POWER: ${cmpData.baseline_variable}`,
        line: { color: '#ff4444', width: 2, dash: 'dot' },
        type: 'scatter'
      }
    ];

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'rgba(10, 25, 47, 0.4)',
      font: { color: '#cbd5e1', family: 'Inter, sans-serif' },
      margin: { l: 60, r: 30, t: 20, b: 50 },
      xaxis: { gridcolor: 'rgba(255, 255, 255, 0.06)', title: 'Aligned Monthly Timeline' },
      yaxis: { gridcolor: 'rgba(255, 255, 255, 0.06)', title: 'Magnitude' },
      legend: { orientation: 'h', y: 1.15, x: 0 },
      hovermode: 'x unified'
    };

    Plotly.newPlot('compare-plot', traces, layout, { responsive: true, displayModeBar: false });
  }

  // Load Ingested Datasets Library
  async function loadDatasetsLibrary() {
    try {
      const res = await api.getDatasets();
      const datasets = (res && res.datasets) ? res.datasets : [];

      if (datasets.length === 0) {
        datasetsTableBody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; color: #94a3b8; padding: 20px;">
              No datasets ingested yet. Upload a CSV/NetCDF dataset above.
            </td>
          </tr>
        `;
        return;
      }

      datasetsTableBody.innerHTML = datasets.map(d => {
        const id = d.datasetId || d.id;
        const uploadDate = new Date(d.uploadedAt).toLocaleDateString();
        return `
          <tr>
            <td style="font-weight: 600; color: #00f0ff;">${d.name}</td>
            <td style="font-family: monospace; font-size: 0.8rem; color: #cbd5e1;">${d.originalName}</td>
            <td>${d.totalRows} / ${d.totalColumns}</td>
            <td><span class="badge-quality ${(d.qualityStatus || 'good').toLowerCase()}">${d.qualityStatus || 'GOOD'}</span></td>
            <td>${d.completenessScore}%</td>
            <td style="color: #94a3b8;">${uploadDate}</td>
            <td style="text-align: right;">
              <button class="btn-action-sm btn-action-select" onclick="window.selectDataset('${id}')">
                <i class="fas fa-chart-line"></i> Select
              </button>
              <button class="btn-action-sm btn-action-delete" onclick="window.deleteDataset('${id}')">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.warn('Failed to load datasets library:', err);
    }
  }

  // Window-level helpers for action buttons in table
  window.selectDataset = async (id) => {
    try {
      const res = await api.getDataset(id);
      if (res && res.dataset) {
        currentDatasetId = id;
        currentDataset = res.dataset;
        displayValidationScorecard(res.dataset);
        populateMappingDropdowns(res.dataset);
        renderPreviewTable(res.preview || []);
        window.scrollTo({ top: 350, behavior: 'smooth' });
      }
    } catch (err) {
      alert(`Could not load dataset ${id}: ${err.message}`);
    }
  };

  window.deleteDataset = async (id) => {
    if (!confirm('Are you sure you want to remove this dataset from the repository?')) return;
    try {
      await api.deleteDataset(id);
      if (currentDatasetId === id) {
        currentDatasetId = null;
        mappingCard.style.display = 'none';
        previewCard.style.display = 'none';
        analysisSection.style.display = 'none';
      }
      loadDatasetsLibrary();
      if (window.showToast) {
        window.showToast('Dataset deleted from repository.', 'info');
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`);
    }
  };

  btnRefreshDatasets.addEventListener('click', loadDatasetsLibrary);

  // Initialize
  loadDatasetsLibrary();
});
