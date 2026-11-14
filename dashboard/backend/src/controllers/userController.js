const { localStore } = require('../config/database');
const { success } = require('../utils/responseFormatter');

const getPreferences = (req, res, next) => {
  try {
    const userId = req.user?.userId || 'guest_user';
    let pref = localStore.findOne('preferences', p => p.userId === userId);
    if (!pref) {
      pref = {
        userId,
        preferredVariables: ['T2M', 'PRECTOTCORR'],
        preferredRegion: 'ALL',
        theme: 'space-dark',
        autoAnalyze: true
      };
    }
    return success(res, pref, 'User preferences retrieved');
  } catch (err) {
    next(err);
  }
};

const updatePreferences = (req, res, next) => {
  try {
    const userId = req.user?.userId || 'guest_user';
    const updateData = req.body;
    let existing = localStore.findOne('preferences', p => p.userId === userId);

    if (existing) {
      existing = localStore.update('preferences', p => p.userId === userId, updateData);
    } else {
      existing = localStore.insert('preferences', { userId, ...updateData });
    }

    return success(res, existing, 'User preferences updated successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getPreferences,
  updatePreferences
};
