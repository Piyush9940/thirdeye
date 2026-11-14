/**
 * NASA Earth Systems Trend Detective
 * Scientific Dataset File Upload & Ingestion Middleware
 * 
 * Supports:
 * 1. multipart/form-data (browser HTML form / fetch FormData)
 * 2. application/json payload ({ filename, content, isBase64 })
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const env = require('../config/environment');

const ALLOWED_EXTENSIONS = ['.csv', '.tsv', '.txt', '.nc', '.netcdf', '.nc4', '.json'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

// Ensure upload directory exists
if (!fs.existsSync(env.PATHS.UPLOADS_DIR)) {
  fs.mkdirSync(env.PATHS.UPLOADS_DIR, { recursive: true });
}

function sanitizeFilename(originalName) {
  const safeName = path.basename(originalName).replace(/[^a-zA-Z0-9._-]/g, '_');
  const ext = path.extname(safeName).toLowerCase();
  const base = path.basename(safeName, ext);
  const randomSuffix = crypto.randomBytes(6).toString('hex');
  return `${base}_${Date.now()}_${randomSuffix}${ext}`;
}

const fileUploadMiddleware = (req, res, next) => {
  const contentType = req.headers['content-type'] || '';

  // 1. Handle JSON Body Upload ({ filename, content, isBase64 })
  if (contentType.includes('application/json')) {
    if (req.body && req.body.filename && req.body.content) {
      try {
        const originalName = req.body.filename;
        const ext = path.extname(originalName).toLowerCase();
        
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
          return res.status(400).json({
            success: false,
            message: `Unsupported file format '${ext}'. Allowed formats: ${ALLOWED_EXTENSIONS.join(', ')}`
          });
        }

        const savedName = sanitizeFilename(originalName);
        const savedPath = path.join(env.PATHS.UPLOADS_DIR, savedName);

        let buffer;
        if (req.body.isBase64) {
          buffer = Buffer.from(req.body.content, 'base64');
        } else {
          buffer = Buffer.from(req.body.content, 'utf-8');
        }

        if (buffer.length > MAX_FILE_SIZE) {
          return res.status(400).json({
            success: false,
            message: `File size exceeds the 50MB limit (${(buffer.length / (1024 * 1024)).toFixed(2)} MB)`
          });
        }

        fs.writeFileSync(savedPath, buffer);

        req.file = {
          originalname: originalName,
          filename: savedName,
          path: savedPath,
          size: buffer.length,
          mimetype: ext === '.csv' ? 'text/csv' : 'application/octet-stream'
        };

        return next();
      } catch (err) {
        return res.status(500).json({
          success: false,
          message: `Failed to process JSON file payload: ${err.message}`
        });
      }
    }
    // If no direct file in JSON, let next handler validate
    return next();
  }

  // 2. Handle Multipart Form Data
  if (contentType.includes('multipart/form-data')) {
    const boundaryMatch = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
    if (!boundaryMatch) {
      return res.status(400).json({ success: false, message: 'Invalid multipart boundary' });
    }

    const boundary = boundaryMatch[1] || boundaryMatch[2];
    const boundaryBuffer = Buffer.from(`--${boundary}`);
    const chunks = [];
    let totalSize = 0;

    req.on('data', (chunk) => {
      totalSize += chunk.length;
      if (totalSize > MAX_FILE_SIZE) {
        req.destroy(new Error('File exceeds maximum size limit of 50MB'));
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      try {
        const fullBuffer = Buffer.concat(chunks);
        const parts = [];
        let start = 0;

        while (true) {
          const idx = fullBuffer.indexOf(boundaryBuffer, start);
          if (idx === -1) break;
          if (start > 0) {
            // Include CRLF before boundary in previous part slice
            parts.push(fullBuffer.subarray(start, idx - 2));
          }
          start = idx + boundaryBuffer.length + 2; // skip boundary + \r\n
        }

        req.body = req.body || {};

        for (const part of parts) {
          const headerEnd = part.indexOf(Buffer.from('\r\n\r\n'));
          if (headerEnd === -1) continue;

          const headerStr = part.subarray(0, headerEnd).toString('utf-8');
          const bodyBuffer = part.subarray(headerEnd + 4);

          const dispositionMatch = headerStr.match(/Content-Disposition:\s*form-data;\s*name="([^"]+)"(?:;\s*filename="([^"]+)")?/i);
          if (!dispositionMatch) continue;

          const fieldName = dispositionMatch[1];
          const rawFilename = dispositionMatch[2];

          if (rawFilename) {
            // It's a file
            const ext = path.extname(rawFilename).toLowerCase();
            if (!ALLOWED_EXTENSIONS.includes(ext)) {
              return res.status(400).json({
                success: false,
                message: `Unsupported file format '${ext}'. Allowed formats: ${ALLOWED_EXTENSIONS.join(', ')}`
              });
            }

            const savedName = sanitizeFilename(rawFilename);
            const savedPath = path.join(env.PATHS.UPLOADS_DIR, savedName);
            fs.writeFileSync(savedPath, bodyBuffer);

            req.file = {
              originalname: rawFilename,
              filename: savedName,
              path: savedPath,
              size: bodyBuffer.length,
              mimetype: ext === '.csv' ? 'text/csv' : 'application/octet-stream'
            };
          } else {
            // It's a normal form text field
            req.body[fieldName] = bodyBuffer.toString('utf-8').trim();
          }
        }

        return next();
      } catch (err) {
        return res.status(500).json({
          success: false,
          message: `Error parsing multipart upload: ${err.message}`
        });
      }
    });

    req.on('error', (err) => {
      return res.status(400).json({
        success: false,
        message: err.message
      });
    });

    return;
  }

  // Fallthrough for other content types
  next();
};

module.exports = fileUploadMiddleware;
