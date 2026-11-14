const { spawn } = require('child_process');
const env = require('../config/environment');
const logger = require('../utils/logger');

class PythonExecutionService {
  /**
   * Executes a python script with given arguments and parses JSON output.
   * @param {string} scriptPath Absolute path to python script
   * @param {Array<string>} args CLI arguments
   * @param {number} timeoutMs Max time before timeout (default 60s)
   */
  async execute(scriptPath, args = [], timeoutMs = 60000) {
    return new Promise((resolve, reject) => {
      const pythonBin = env.PYTHON_PATH;
      const cmdArgs = [scriptPath, ...args];

      logger.debug(`[PythonExec] Spawning: ${pythonBin} ${cmdArgs.join(' ')}`);

      const child = spawn(pythonBin, cmdArgs, {
        windowsHide: true,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
      });

      let stdoutData = '';
      let stderrData = '';
      let isTimedOut = false;

      const timer = setTimeout(() => {
        isTimedOut = true;
        child.kill();
        reject(new Error(`Python process timed out after ${timeoutMs}ms: ${scriptPath}`));
      }, timeoutMs);

      child.stdout.on('data', (chunk) => {
        stdoutData += chunk.toString('utf-8');
      });

      child.stderr.on('data', (chunk) => {
        stderrData += chunk.toString('utf-8');
      });

      child.on('error', (err) => {
        clearTimeout(timer);
        logger.error(`[PythonExec] Failed to start python process: ${err.message}`);
        reject(err);
      });

      child.on('close', (code) => {
        clearTimeout(timer);
        if (isTimedOut) return;

        if (code !== 0) {
          logger.warn(`[PythonExec] Process exited with code ${code}. Stderr: ${stderrData.slice(0, 300)}`);
          // Try to see if stdout contains a JSON error
          try {
            const parsed = JSON.parse(stdoutData.trim());
            if (parsed.error) {
              return reject(new Error(parsed.error));
            }
          } catch (_) {
            // Not json
          }
          return reject(new Error(`Python execution failed (code ${code}): ${stderrData.trim() || 'Unknown error'}`));
        }

        try {
          const trimmed = stdoutData.trim();
          const parsed = JSON.parse(trimmed);
          resolve(parsed);
        } catch (jsonErr) {
          logger.error(`[PythonExec] JSON parse error on stdout: ${stdoutData.slice(0, 300)}`);
          reject(new Error(`Failed to parse Python JSON output: ${jsonErr.message}`));
        }
      });
    });
  }
}

module.exports = new PythonExecutionService();
