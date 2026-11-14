/**
 * NASA Earth Systems Trend Detective
 * Report Service
 */

const datasetService = require('./dataset.service');

class ReportService {
  buildSummaryDossier() {
    const kpis = datasetService.getKPIs();
    return {
      title: 'Earth Systems Trend Detective — Comprehensive Environmental Dataset Dossier',
      timestamp: new Date().toISOString(),
      kpis,
      warnings: kpis.scientificWarnings
    };
  }
}

module.exports = new ReportService();
