const path = require('path');

/**
 * Validates that a target file path is safely contained within an allowed base directory.
 * Prevents directory traversal attacks.
 */
const isSafePath = (baseDir, targetPath) => {
  const resolvedBase = path.resolve(baseDir);
  const resolvedTarget = path.resolve(targetPath);
  return resolvedTarget.startsWith(resolvedBase);
};

module.exports = {
  isSafePath
};
