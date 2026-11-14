const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
const env = require('./environment');

let isConnected = false;

// Simple JSON file-based local fallback store
class LocalStore {
  constructor(filePath) {
    this.filePath = filePath;
    this.data = { users: [], savedAnalyses: [], reports: [], preferences: [] };
    this._init();
  }

  _init() {
    try {
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      if (fs.existsSync(this.filePath)) {
        const raw = fs.readFileSync(this.filePath, 'utf-8');
        this.data = JSON.parse(raw);
      } else {
        this.save();
      }
    } catch (err) {
      console.warn('[Database] LocalStore init notice:', err.message);
    }
  }

  save() {
    try {
      fs.writeFileSync(this.filePath, JSON.stringify(this.data, null, 2), 'utf-8');
    } catch (err) {
      console.warn('[Database] LocalStore save error:', err.message);
    }
  }

  get(collection) {
    return this.data[collection] || [];
  }

  insert(collection, item) {
    if (!this.data[collection]) this.data[collection] = [];
    const record = { ...item, _id: item._id || 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6), createdAt: new Date().toISOString() };
    this.data[collection].push(record);
    this.save();
    return record;
  }

  findOne(collection, filterFn) {
    return (this.data[collection] || []).find(filterFn) || null;
  }

  find(collection, filterFn) {
    if (!filterFn) return this.data[collection] || [];
    return (this.data[collection] || []).filter(filterFn);
  }

  update(collection, filterFn, updateData) {
    const item = this.findOne(collection, filterFn);
    if (item) {
      Object.assign(item, updateData, { updatedAt: new Date().toISOString() });
      this.save();
    }
    return item;
  }

  remove(collection, filterFn) {
    if (!this.data[collection]) return false;
    const initialLen = this.data[collection].length;
    this.data[collection] = this.data[collection].filter(item => !filterFn(item));
    if (this.data[collection].length !== initialLen) {
      this.save();
      return true;
    }
    return false;
  }
}

const localStore = new LocalStore(env.PATHS.STORE_FILE);

const connectDB = async () => {
  try {
    mongoose.set('strictQuery', false);
    // Timeout quickly so the server boots in <1 second even without local MongoDB
    const conn = await mongoose.connect(env.MONGODB_URI, {
      serverSelectionTimeoutMS: 1500
    });
    isConnected = true;
    console.log(`[Database] MongoDB connected: ${conn.connection.host}`);
  } catch (err) {
    isConnected = false;
    console.log('[Database] MongoDB not detected. Activating seamless local persistent storage fallback.');
  }
};

module.exports = {
  connectDB,
  isConnected: () => isConnected,
  localStore
};
