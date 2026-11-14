/**
 * NASA Earth Systems Trend Detective
 * Analysis Mongoose Model
 */

const mongoose = require('mongoose');

const AnalysisSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: false
  },
  title: {
    type: String,
    required: true,
    trim: true
  },
  type: {
    type: String,
    enum: ['methane', 'climate', 'hotspot', 'trend', 'ocean'],
    default: 'methane'
  },
  period: {
    type: String,
    default: 'ALL'
  },
  region: {
    type: String,
    default: 'ALL'
  },
  parameters: {
    type: Object,
    default: {}
  },
  notes: {
    type: String,
    default: ''
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('Analysis', AnalysisSchema);
