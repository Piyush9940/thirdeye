/**
 * NASA Earth Systems Trend Detective
 * Scientific Dataset Controller
 * 
 * Handles:
 * - Dataset file upload & dynamic ingestion (CSV, TSV, NetCDF)
 * - Validation of columns, data types, coordinates, and missing values
 * - Variable mapping & quality assurance scoring
 * - Statistical trend analysis on user data (OLS, Mann-Kendall, Theil-Sen)
 * - Climatological comparison against NASA POWER baselines
 */

const fs = require('fs');
const path = require('path');
const env = require('../config/environment');
const { localStore } = require('../config/database');
const pythonExecutionService = require('../services/pythonExecutionService');
const logger = require('../utils/logger');

class DatasetController {
  /**
   * Upload and register a new scientific dataset
   * POST /api/datasets/upload
   */
  async uploadDataset(req, res, next) {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          message: 'No file uploaded. Please attach a valid scientific dataset file (CSV, TSV, NetCDF).'
        });
      }

      logger.info(`[DatasetController] Uploading dataset: ${req.file.originalname} (${req.file.size} bytes)`);

      // Run Python dataset validation
      const validation = await pythonExecutionService.execute(
        env.PATHS.DATASET_PROCESSOR,
        ['--action', 'validate', '--file', req.file.path]
      );

      if (!validation.success) {
        // Remove invalid file
        if (fs.existsSync(req.file.path)) {
          fs.unlinkSync(req.file.path);
        }
        return res.status(400).json({
          success: false,
          message: validation.error || 'Dataset validation failed'
        });
      }

      const datasetId = 'ds_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
      const datasetRecord = {
        datasetId,
        name: req.body.name || path.basename(req.file.originalname, path.extname(req.file.originalname)),
        description: req.body.description || 'User-uploaded scientific observation dataset.',
        fileName: req.file.filename,
        originalName: req.file.originalname,
        filePath: req.file.path,
        fileSize: req.file.size,
        totalRows: validation.total_rows,
        totalColumns: validation.total_columns,
        completenessScore: validation.completeness_score,
        qualityStatus: validation.quality_status,
        auditNotes: validation.audit_notes,
        columns: validation.columns,
        candidateMappings: validation.candidate_mappings,
        suggestedMapping: validation.suggested_mapping,
        temporalRange: validation.temporal_range,
        spatialBounds: validation.spatial_bounds,
        uploadedAt: new Date().toISOString()
      };

      // Persist in local store
      localStore.insert('datasets', datasetRecord);

      return res.status(201).json({
        success: true,
        message: 'Dataset uploaded and validated successfully',
        dataset: datasetRecord,
        preview: validation.preview
      });
    } catch (err) {
      logger.error(`[DatasetController] Upload error: ${err.message}`);
      next(err);
    }
  }

  /**
   * Validate an uploaded file or existing dataset schema
   * POST /api/datasets/validate
   */
  async validateDataset(req, res, next) {
    try {
      let targetFilePath = null;

      if (req.file && req.file.path) {
        targetFilePath = req.file.path;
      } else if (req.body && req.body.datasetId) {
        const ds = localStore.findOne('datasets', d => d.datasetId === req.body.datasetId || d._id === req.body.datasetId);
        if (!ds) {
          return res.status(404).json({ success: false, message: 'Dataset not found.' });
        }
        targetFilePath = ds.filePath;
      } else if (req.body && req.body.filePath) {
        targetFilePath = req.body.filePath;
      }

      if (!targetFilePath || !fs.existsSync(targetFilePath)) {
        return res.status(400).json({
          success: false,
          message: 'Valid dataset file or datasetId required for validation.'
        });
      }

      const validation = await pythonExecutionService.execute(
        env.PATHS.DATASET_PROCESSOR,
        ['--action', 'validate', '--file', targetFilePath]
      );

      return res.json({
        success: true,
        validation
      });
    } catch (err) {
      logger.error(`[DatasetController] Validation error: ${err.message}`);
      next(err);
    }
  }

  /**
   * List all registered datasets
   * GET /api/datasets
   */
  async getDatasets(req, res, next) {
    try {
      const datasets = localStore.get('datasets') || [];
      // Sanitize internal absolute paths from public listing
      const sanitized = datasets.map(d => ({
        id: d.datasetId || d._id,
        _id: d._id,
        datasetId: d.datasetId,
        name: d.name,
        description: d.description,
        originalName: d.originalName,
        fileSize: d.fileSize,
        totalRows: d.totalRows,
        totalColumns: d.totalColumns,
        completenessScore: d.completenessScore,
        qualityStatus: d.qualityStatus,
        temporalRange: d.temporalRange,
        spatialBounds: d.spatialBounds,
        suggestedMapping: d.suggestedMapping,
        uploadedAt: d.uploadedAt
      }));

      return res.json({
        success: true,
        count: sanitized.length,
        datasets: sanitized
      });
    } catch (err) {
      next(err);
    }
  }

  /**
   * Get dataset details and preview
   * GET /api/datasets/:id
   */
  async getDatasetById(req, res, next) {
    try {
      const id = req.params.id;
      const ds = localStore.findOne('datasets', d => d.datasetId === id || d._id === id);

      if (!ds) {
        return res.status(404).json({ success: false, message: 'Dataset not found.' });
      }

      // Re-run lightweight validation to get fresh preview rows if file exists
      let preview = [];
      if (fs.existsSync(ds.filePath)) {
        try {
          const val = await pythonExecutionService.execute(
            env.PATHS.DATASET_PROCESSOR,
            ['--action', 'validate', '--file', ds.filePath]
          );
          preview = val.preview || [];
        } catch (_) {}
      }

      return res.json({
        success: true,
        dataset: ds,
        preview
      });
    } catch (err) {
      next(err);
    }
  }

  /**
   * Get dataset scientific metadata
   * GET /api/datasets/:id/metadata
   */
  async getDatasetMetadata(req, res, next) {
    try {
      const id = req.params.id;
      const ds = localStore.findOne('datasets', d => d.datasetId === id || d._id === id);

      if (!ds) {
        return res.status(404).json({ success: false, message: 'Dataset not found.' });
      }

      return res.json({
        success: true,
        metadata: {
          id: ds.datasetId,
          name: ds.name,
          originalName: ds.originalName,
          totalRows: ds.totalRows,
          totalColumns: ds.totalColumns,
          completenessScore: ds.completenessScore,
          qualityStatus: ds.qualityStatus,
          auditNotes: ds.auditNotes,
          columns: ds.columns,
          candidateMappings: ds.candidateMappings,
          suggestedMapping: ds.suggestedMapping,
          temporalRange: ds.temporalRange,
          spatialBounds: ds.spatialBounds,
          uploadedAt: ds.uploadedAt
        }
      });
    } catch (err) {
      next(err);
    }
  }

  /**
   * Delete uploaded dataset
   * DELETE /api/datasets/:id
   */
  async deleteDataset(req, res, next) {
    try {
      const id = req.params.id;
      const ds = localStore.findOne('datasets', d => d.datasetId === id || d._id === id);

      if (!ds) {
        return res.status(404).json({ success: false, message: 'Dataset not found.' });
      }

      // Remove physical file
      if (fs.existsSync(ds.filePath)) {
        try {
          fs.unlinkSync(ds.filePath);
        } catch (fErr) {
          logger.warn(`[DatasetController] File deletion warning: ${fErr.message}`);
        }
      }

      localStore.remove('datasets', d => d.datasetId === id || d._id === id);

      return res.json({
        success: true,
        message: `Dataset '${ds.name}' successfully deleted.`
      });
    } catch (err) {
      next(err);
    }
  }

  /**
   * Run scientific trend analysis on uploaded dataset
   * POST /api/datasets/:id/analyze
   */
  async analyzeDataset(req, res, next) {
    try {
      const id = req.params.id;
      const ds = localStore.findOne('datasets', d => d.datasetId === id || d._id === id);

      if (!ds) {
        return res.status(404).json({ success: false, message: 'Dataset not found.' });
      }

      if (!fs.existsSync(ds.filePath)) {
        return res.status(404).json({ success: false, message: 'Dataset file not found on disk.' });
      }

      const {
        variable,
        timeCol,
        latCol,
        lonCol,
        unit = 'units',
        startDate,
        endDate
      } = req.body;

      if (!variable) {
        return res.status(400).json({
          success: false,
          message: "Field 'variable' is required for trend analysis."
        });
      }

      const cliArgs = [
        '--action', 'analyze',
        '--file', ds.filePath,
        '--variable', variable,
        '--unit', unit
      ];

      if (timeCol) cliArgs.push('--time-col', timeCol);
      if (latCol) cliArgs.push('--lat-col', latCol);
      if (lonCol) cliArgs.push('--lon-col', lonCol);
      if (startDate) cliArgs.push('--start-date', startDate);
      if (endDate) cliArgs.push('--end-date', endDate);

      logger.info(`[DatasetController] Analyzing dataset ${id} variable: ${variable}`);

      const analysis = await pythonExecutionService.execute(
        env.PATHS.DATASET_PROCESSOR,
        cliArgs
      );

      return res.json({
        success: true,
        datasetId: ds.datasetId,
        datasetName: ds.name,
        analysis
      });
    } catch (err) {
      logger.error(`[DatasetController] Analysis error: ${err.message}`);
      next(err);
    }
  }

  /**
   * Compare uploaded dataset against NASA POWER climatology
   * POST /api/datasets/:id/compare
   */
  async compareDataset(req, res, next) {
    try {
      const id = req.params.id;
      const ds = localStore.findOne('datasets', d => d.datasetId === id || d._id === id);

      if (!ds) {
        return res.status(404).json({ success: false, message: 'Dataset not found.' });
      }

      if (!fs.existsSync(ds.filePath)) {
        return res.status(404).json({ success: false, message: 'Dataset file not found on disk.' });
      }

      const {
        variable,
        baselineVar = 'T2M',
        timeCol
      } = req.body;

      if (!variable) {
        return res.status(400).json({
          success: false,
          message: "Field 'variable' is required for baseline comparison."
        });
      }

      const cliArgs = [
        '--action', 'compare',
        '--file', ds.filePath,
        '--variable', variable,
        '--baseline-var', baselineVar
      ];

      if (timeCol) cliArgs.push('--time-col', timeCol);

      logger.info(`[DatasetController] Comparing dataset ${id} (${variable}) against baseline (${baselineVar})`);

      const comparison = await pythonExecutionService.execute(
        env.PATHS.DATASET_PROCESSOR,
        cliArgs
      );

      return res.json({
        success: true,
        datasetId: ds.datasetId,
        datasetName: ds.name,
        comparison
      });
    } catch (err) {
      logger.error(`[DatasetController] Comparison error: ${err.message}`);
      next(err);
    }
  }
}

module.exports = new DatasetController();
