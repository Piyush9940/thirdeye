/**
 * NASA Earth Systems Trend Detective
 * Scientific Reports Controller
 */

const datasetService = require('../services/dataset.service');

exports.generateReport = (req, res) => {
  try {
    const { type = 'summary', params = {} } = req.body;
    const now = new Date().toISOString();
    const kpis = datasetService.getKPIs();

    let report = null;

    if (type === 'regional') {
      const region = params.region || 'North_West';
      const obs = datasetService.getMethaneObservations({ region, limit: 1000 }).records;
      const values = obs.map(o => o.methane_median_ppb);
      const mean = values.length ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : 0;
      const min = values.length ? Math.min(...values).toFixed(2) : 0;
      const max = values.length ? Math.max(...values).toFixed(2) : 0;

      report = {
        title: `Regional Atmospheric Methane Intelligence Dossier: ${region.replace('_', ' ')}`,
        generatedAt: now,
        type: 'regional',
        region,
        observationCount: obs.length,
        metrics: {
          mean_ppb: mean,
          min_ppb: min,
          max_ppb: max,
          unit: 'ppb'
        },
        methodology: 'Aggregated Sentinel-5P TROPOMI Level-3 observations filtered by QA >= 0.50 and matched to 2° spatial grid nodes.',
        scientificLimitations: 'Atmospheric concentration measurements reflect column mixing and regional advection. They do NOT establish local emission points or identify specific source facilities.',
        observations: obs.slice(0, 50)
      };
    } else if (type === 'ml_evaluation') {
      const metrics = datasetService.getFoldMetrics();
      report = {
        title: 'Machine Learning Experiment & Model Evaluation Audit',
        generatedAt: now,
        type: 'ml_evaluation',
        model: 'Original MLP Reference Model (8 inputs, 32 hidden units, ReLU, Dropout 0.2)',
        modelStatus: 'Experimental Reference Model — Not Production Approved',
        folds: metrics.foldSummary,
        seedMetrics: metrics.seedMetrics,
        benchmarkComparison: metrics.comparisons,
        conclusions: [
          'Negative R2 across chronological evaluation folds indicates predictions do not beat the mean baseline.',
          'Negative bias shows consistent underprediction of atmospheric methane concentrations.',
          'Graph Neural Networks (distance-weighted and unweighted GCN) demonstrated no performance advantage over the simple MLP architecture.',
          'The month-only seasonal diagnostic achieved the lowest mean fold MAE (49.04 ppb).'
        ],
        scientificLimitations: 'Experimental reference only. This model must not be deployed for operational environmental forecasting.'
      };
    } else {
      // Default: Comprehensive Summary Dossier
      report = {
        title: 'Earth Systems Trend Detective — Comprehensive Environmental Dataset Dossier',
        generatedAt: now,
        type: 'summary',
        coverage: {
          studyArea: kpis.studyArea,
          spatialNodes: kpis.spatialNodesCount,
          observedNodes: kpis.observedNodesCount,
          observations: kpis.observationRecordsCount,
          evaluationPredictions: kpis.evaluationPredictionsCount,
          periods: kpis.observationPeriods
        },
        satelliteTelemetry: 'Sentinel-5P TROPOMI Level-3 Methane (CH4) Column Concentration',
        climateContext: 'NASA POWER Surface Meteorological Parameters (T2M, PRECTOTCORR, RH2M, WS10M)',
        keyFindings: [
          'Atmospheric methane concentrations over India varied between 1788.8 ppb and 2021.8 ppb across the 4 snapshot periods.',
          'Pre-monsoon (2019-05) mean concentration was 1861.16 ppb, rising to 1954.15 ppb in post-monsoon (2023-11).',
          'Monsoon period (2021-08) is characterized by high data sparsity (only 11 valid nodes) due to persistent cloud cover and rigorous QA filtering.'
        ],
        scientificLimitations: kpis.scientificWarnings
      };
    }

    res.json({ success: true, data: report });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
};
