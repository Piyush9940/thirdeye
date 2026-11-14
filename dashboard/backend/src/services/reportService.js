const fs = require('fs');
const path = require('path');
const pythonExec = require('./pythonExecutionService');
const env = require('../config/environment');
const { localStore, isConnected } = require('../config/database');
const logger = require('../utils/logger');

class ReportService {
  async generateReport(analysisData, userId = 'anonymous') {
    const reportId = 'rep_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
    const fileName = `trend_dossier_${reportId}.pdf`;
    const outputPath = path.resolve(env.PATHS.REPORTS_DIR, fileName);

    // Ensure output directory exists
    if (!fs.existsSync(env.PATHS.REPORTS_DIR)) {
      fs.mkdirSync(env.PATHS.REPORTS_DIR, { recursive: true });
    }

    // Write temp input JSON file to avoid shell escaping issues
    const tempJsonPath = path.resolve(env.PATHS.REPORTS_DIR, `temp_${reportId}.json`);
    fs.writeFileSync(tempJsonPath, JSON.stringify(analysisData), 'utf-8');

    try {
      const res = await pythonExec.execute(env.PATHS.REPORT_GENERATOR, [
        '--input_json', tempJsonPath,
        '--output_pdf', outputPath
      ]);

      // Clean up temp json
      if (fs.existsSync(tempJsonPath)) {
        fs.unlinkSync(tempJsonPath);
      }

      const reportRecord = {
        reportId,
        fileName,
        title: `NASA Trend Detective Dossier - ${analysisData.variable_name || analysisData.variable} (${analysisData.region_name || analysisData.region})`,
        variable: analysisData.variable,
        region: analysisData.region,
        dateRange: analysisData.date_range,
        downloadUrl: `/reports/${fileName}`,
        filePath: outputPath,
        createdAt: new Date().toISOString(),
        userId
      };

      // Save to local store or DB
      localStore.insert('reports', reportRecord);

      return reportRecord;
    } catch (err) {
      if (fs.existsSync(tempJsonPath)) fs.unlinkSync(tempJsonPath);
      logger.error(`[ReportService] PDF Generation failed: ${err.message}`);
      throw err;
    }
  }

  getReportHistory(userId = null) {
    if (userId) {
      return localStore.find('reports', r => r.userId === userId);
    }
    return localStore.get('reports');
  }

  getReportById(reportId) {
    return localStore.findOne('reports', r => r.reportId === reportId);
  }
}

module.exports = new ReportService();
