/**
 * NASA Earth Systems Trend Detective
 * Report Mongoose Model
 */

const mongoose = require('mongoose');

const ReportSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['summary', 'regional', 'ml_evaluation'],
    default: 'summary'
  },
  generatedBy: {
    type: String,
    default: 'System'
  },
  content: {
    type: Object,
    required: true
  },
  status: {
    type: String,
    enum: ['draft', 'published', 'archived'],
    default: 'published'
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('Report', ReportSchema);
