/**
 * NASA Earth Systems Trend Detective
 * Additional Mongoose Domain Models
 */

const mongoose = require('mongoose');

// Forecast Schema
const ForecastSchema = new mongoose.Schema({
  model: { type: String, default: 'Original MLP Reference Model' },
  fold: { type: Number, required: true },
  seed: { type: Number, required: true },
  inputs: { type: [Number], required: true },
  prediction_ppb: { type: Number, required: true },
  status: { type: String, default: 'experimental_reference' }
}, { timestamps: true });

// Dataset Schema
const DatasetSchema = new mongoose.Schema({
  name: { type: String, required: true },
  sensor: { type: String, default: 'Sentinel-5P TROPOMI' },
  period: { type: String, required: true },
  recordsCount: { type: Number, required: true },
  metadata: { type: Object, default: {} }
}, { timestamps: true });

// ModelRun Schema
const ModelRunSchema = new mongoose.Schema({
  modelType: { type: String, required: true },
  fold: { type: Number, required: true },
  seed: { type: Number, required: true },
  mae: { type: Number },
  rmse: { type: Number },
  r2: { type: Number },
  bias: { type: Number }
}, { timestamps: true });

// Job Schema
const JobSchema = new mongoose.Schema({
  taskName: { type: String, required: true },
  status: { type: String, enum: ['queued', 'running', 'completed', 'failed'], default: 'completed' },
  payload: { type: Object, default: {} }
}, { timestamps: true });

module.exports = {
  Forecast: mongoose.models.Forecast || mongoose.model('Forecast', ForecastSchema),
  Dataset: mongoose.models.Dataset || mongoose.model('Dataset', DatasetSchema),
  ModelRun: mongoose.models.ModelRun || mongoose.model('ModelRun', ModelRunSchema),
  Job: mongoose.models.Job || mongoose.model('Job', JobSchema)
};
