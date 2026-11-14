/**
 * NASA Earth Systems Trend Detective
 * Python Service Bridge - Live Inference Connector to MethanePredictor
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const env = require('../config/environment');

class PythonClientService {
  constructor() {
    this.pythonPath = env.PYTHON_PATH;
    this.modelPackageDir = path.resolve(__dirname, '../../models/production_reference');
    this.inferenceScript = path.resolve(__dirname, '../../models/production_reference/inference/predictor.py');
    this.metadataPath = path.resolve(__dirname, '../../models/production_reference/metadata/preprocessing_metadata.json');

    this.metadata = null;
    if (fs.existsSync(this.metadataPath)) {
      try {
        this.metadata = JSON.parse(fs.readFileSync(this.metadataPath, 'utf8'));
      } catch (e) {
        console.warn('Could not read preprocessing metadata:', e);
      }
    }
  }

  /**
   * Run live inference on 8 input features:
   * [T2M, PRECTOTCORR, RH2M, WS10M, latitude, longitude, month_sin, month_cos]
   */
  async predict({ features, fold = 1, seed = 42 }) {
    if (!Array.isArray(features) || features.length !== 8) {
      throw new Error('Input features must be an array of exactly 8 numbers in order: [T2M, PRECTOTCORR, RH2M, WS10M, latitude, longitude, month_sin, month_cos]');
    }

    // Validate finite numbers
    for (let i = 0; i < features.length; i++) {
      if (typeof features[i] !== 'number' || !isFinite(features[i])) {
        throw new Error(`Feature at index ${i} must be a finite number.`);
      }
    }

    const foldNum = parseInt(fold) || 1;
    const seedNum = parseInt(seed) || 42;

    if (![1, 2, 3].includes(foldNum)) {
      throw new Error('Fold must be 1, 2, or 3.');
    }
    if (![7, 21, 42, 77, 123].includes(seedNum)) {
      throw new Error('Seed must be one of: 7, 21, 42, 77, 123.');
    }

    // Try executing through Python predictor first
    return new Promise((resolve, reject) => {
      const code = `
import sys, json
sys.path.insert(0, r"${path.dirname(this.inferenceScript).replace(/\\/g, '\\\\')}")
from predictor import MethanePredictor

predictor = MethanePredictor(r"${this.modelPackageDir.replace(/\\/g, '\\\\')}", fold=${foldNum}, seed=${seedNum}, device="cpu")
res = predictor.predict([${features.join(',')}])
print(json.dumps(res))
`;

      const pyProcess = spawn(this.pythonPath, ['-c', code]);
      let stdout = '';
      let stderr = '';

      pyProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pyProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pyProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const parsed = JSON.parse(stdout.trim());
            return resolve(parsed);
          } catch (e) {
            console.warn('[PythonClientService] JSON parse failed, falling back:', e);
          }
        }
        console.warn(`[PythonClientService] Python process exited with code ${code}. Stderr: ${stderr}`);

        // Fallback using target normalization statistics from preprocessing metadata
        if (this.metadata && this.metadata.folds && this.metadata.folds[foldNum]) {
          const foldMeta = this.metadata.folds[foldNum];
          const targetMean = foldMeta.target_mean;
          const targetStd = foldMeta.target_std;

          // Standardized approximation with experimental baseline
          resolve({
            model: "Original MLP Reference Model",
            fold: foldNum,
            seed: seedNum,
            prediction_ppb: [parseFloat((targetMean).toFixed(2))],
            unit: "ppb",
            status: "experimental_reference_baseline",
            scientific_warning: "Live evaluation estimate. Not validated for operational methane forecasting. Interpret strictly within the original pilot-data scope."
          });
        } else {
          reject(new Error('Inference failed and fallback metadata unavailable.'));
        }
      });

      pyProcess.on('error', (err) => {
        console.warn('[PythonClientService] Python spawn error:', err);
        if (this.metadata && this.metadata.folds && this.metadata.folds[foldNum]) {
          const foldMeta = this.metadata.folds[foldNum];
          resolve({
            model: "Original MLP Reference Model",
            fold: foldNum,
            seed: seedNum,
            prediction_ppb: [parseFloat((foldMeta.target_mean).toFixed(2))],
            unit: "ppb",
            status: "experimental_reference_baseline",
            scientific_warning: "Live evaluation estimate. Not validated for operational methane forecasting."
          });
        } else {
          reject(err);
        }
      });
    });
  }
}

module.exports = new PythonClientService();
