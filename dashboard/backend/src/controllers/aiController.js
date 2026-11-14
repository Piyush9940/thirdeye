const aiService = require('../services/aiService');
const { success, error } = require('../utils/responseFormatter');

const postChat = async (req, res, next) => {
  try {
    const { prompt, context, provider } = req.body;
    if (!prompt || typeof prompt !== 'string') {
      return error(res, 'Prompt string is required.', 400);
    }

    const aiResult = await aiService.generateResponse(prompt, context || {}, { provider });
    return success(res, aiResult, 'AI response generated successfully');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  postChat
};
