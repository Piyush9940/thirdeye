const reportService = require('../services/reportService');
const { success, error } = require('../utils/responseFormatter');

const postGenerate = async (req, res, next) => {
  try {
    const analysisData = req.body;
    if (!analysisData || !analysisData.variable) {
      return error(res, 'Valid analysis data is required to generate a report dossier.', 400);
    }

    const userId = req.user?.userId || 'anonymous';
    const report = await reportService.generateReport(analysisData, userId);
    return success(res, report, 'Research dossier PDF generated successfully', 201);
  } catch (err) {
    next(err);
  }
};

const getHistory = (req, res, next) => {
  try {
    const userId = req.user?.userId;
    const history = reportService.getReportHistory(userId);
    return success(res, history, 'Report generation history retrieved');
  } catch (err) {
    next(err);
  }
};

const getById = (req, res, next) => {
  try {
    const report = reportService.getReportById(req.params.id);
    if (!report) {
      return error(res, 'Report not found', 404);
    }
    return success(res, report, 'Report retrieved successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  postGenerate,
  getHistory,
  getById
};
