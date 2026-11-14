/**
 * NASA Earth Systems Trend Detective
 * Storage & User Authentication Service
 * Dual-Mode: Uses Mongoose when connected, falls back to local JSON store when offline.
 */

const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const env = require('../config/environment');
const db = require('../config/database');
const User = require('../models/User');

class StorageService {
  constructor() {
    this.fallbackFile = path.resolve(__dirname, '../../data/users_store.json');
    this.localUsers = new Map();
    this.initFallback();
  }

  initFallback() {
    try {
      const dir = path.dirname(this.fallbackFile);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      if (fs.existsSync(this.fallbackFile)) {
        const raw = fs.readFileSync(this.fallbackFile, 'utf8');
        const list = JSON.parse(raw);
        list.forEach(u => this.localUsers.set(u.email, u));
      }
    } catch (e) {
      console.warn('[StorageService] Fallback store init warning:', e.message);
    }
  }

  saveFallback() {
    try {
      const list = Array.from(this.localUsers.values());
      fs.writeFileSync(this.fallbackFile, JSON.stringify(list, null, 2), 'utf8');
    } catch (e) {
      console.error('[StorageService] Could not persist local fallback user store:', e.message);
    }
  }

  generateToken(user) {
    return jwt.sign(
      { id: user._id || user.id, email: user.email, name: user.name },
      env.JWT_SECRET,
      { expiresIn: '7d' }
    );
  }

  async register({ name, email, password, institution }) {
    if (!name || !email || !password) {
      throw new Error('Name, email, and password are required.');
    }

    const normalizedEmail = email.toLowerCase().trim();
    const hashedPassword = await bcrypt.hash(password, 10);

    if (db.isConnected) {
      const existing = await User.findOne({ email: normalizedEmail });
      if (existing) {
        throw new Error('User already exists with this email.');
      }
      const user = await User.create({
        name: name.trim(),
        email: normalizedEmail,
        password: hashedPassword,
        institution: institution || 'Independent Researcher'
      });
      const token = this.generateToken(user);
      return {
        user: { id: user._id, name: user.name, email: user.email, institution: user.institution },
        token
      };
    } else {
      if (this.localUsers.has(normalizedEmail)) {
        throw new Error('User already exists with this email.');
      }
      const id = 'local_' + Date.now();
      const newUser = {
        id,
        _id: id,
        name: name.trim(),
        email: normalizedEmail,
        password: hashedPassword,
        institution: institution || 'Independent Researcher',
        savedAnalyses: [],
        savedReports: [],
        chatHistory: [],
        createdAt: new Date().toISOString()
      };
      this.localUsers.set(normalizedEmail, newUser);
      this.saveFallback();
      const token = this.generateToken(newUser);
      return {
        user: { id: newUser.id, name: newUser.name, email: newUser.email, institution: newUser.institution },
        token
      };
    }
  }

  async login({ email, password }) {
    if (!email || !password) {
      throw new Error('Email and password are required.');
    }

    const normalizedEmail = email.toLowerCase().trim();

    if (db.isConnected) {
      const user = await User.findOne({ email: normalizedEmail });
      if (!user) {
        throw new Error('Invalid email or password.');
      }
      const isMatch = await bcrypt.compare(password, user.password);
      if (!isMatch) {
        throw new Error('Invalid email or password.');
      }
      const token = this.generateToken(user);
      return {
        user: { id: user._id, name: user.name, email: user.email, institution: user.institution },
        token
      };
    } else {
      const user = this.localUsers.get(normalizedEmail);
      if (!user) {
        throw new Error('Invalid email or password.');
      }
      const isMatch = await bcrypt.compare(password, user.password);
      if (!isMatch) {
        throw new Error('Invalid email or password.');
      }
      const token = this.generateToken(user);
      return {
        user: { id: user.id, name: user.name, email: user.email, institution: user.institution },
        token
      };
    }
  }

  async getUserById(id) {
    if (db.isConnected) {
      return await User.findById(id).select('-password');
    } else {
      for (const u of this.localUsers.values()) {
        if (u.id === id || u._id === id) {
          const { password, ...safeUser } = u;
          return safeUser;
        }
      }
      return null;
    }
  }

  async saveAnalysis(userId, analysis) {
    if (db.isConnected) {
      const user = await User.findById(userId);
      if (!user) throw new Error('User not found.');
      user.savedAnalyses.push(analysis);
      await user.save();
      return user.savedAnalyses;
    } else {
      for (const u of this.localUsers.values()) {
        if (u.id === userId || u._id === userId) {
          u.savedAnalyses = u.savedAnalyses || [];
          u.savedAnalyses.push({ ...analysis, id: 'analysis_' + Date.now(), createdAt: new Date().toISOString() });
          this.saveFallback();
          return u.savedAnalyses;
        }
      }
      throw new Error('User not found.');
    }
  }

  async getSavedAnalyses(userId) {
    const user = await this.getUserById(userId);
    return user ? user.savedAnalyses || [] : [];
  }
}

module.exports = new StorageService();
