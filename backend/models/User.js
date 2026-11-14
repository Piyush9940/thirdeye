/**
 * NASA Earth Systems Trend Detective
 * User Mongoose Schema
 */

const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true
  },
  institution: {
    type: String,
    default: 'Independent Researcher'
  },
  savedAnalyses: [{
    title: String,
    period: String,
    region: String,
    notes: String,
    createdAt: {
      type: Date,
      default: Date.now
    }
  }],
  savedReports: [{
    title: String,
    type: String,
    params: Object,
    summary: String,
    createdAt: {
      type: Date,
      default: Date.now
    }
  }],
  chatHistory: [{
    role: String,
    content: String,
    timestamp: {
      type: Date,
      default: Date.now
    }
  }]
}, {
  timestamps: true
});

module.exports = mongoose.model('User', UserSchema);
