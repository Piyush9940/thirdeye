/**
 * NASA Earth Systems Trend Detective — AI Research Assistant
 */

class AIAssistant {
  constructor() {
    this.chatContainer = document.getElementById('chat-messages');
    this.input = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('btn-chat-send');
    this.context = {
      variable_name: 'Air Temperature at 2m',
      region_name: 'All India',
      units: '°C',
      ols: { slope_per_year: 0.012, p_value: 0.35 },
      mann_kendall: { p_value: 0.42, is_significant: false },
      sen_slope: { slope_per_year: 0.010 }
    };

    this.init();
  }

  init() {
    // Quick suggestion pills
    document.querySelectorAll('.suggestion-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const text = e.currentTarget.textContent.trim().replace(/^['"]|['"]$/g, '');
        if (this.input) {
          this.input.value = text;
          this.sendMessage();
        }
      });
    });

    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.sendMessage());
    }

    if (this.input) {
      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    // Try to grab latest context from window if available
    if (window.trendWorkspace && window.trendWorkspace.currentData) {
      this.context = window.trendWorkspace.currentData;
    }
  }

  appendMessage(text, sender = 'assistant') {
    if (!this.chatContainer) return;

    const msg = document.createElement('div');
    msg.className = `chat-bubble chat-${sender}`;
    msg.style.cssText = `
      margin-bottom: 1rem;
      padding: 1rem 1.25rem;
      border-radius: var(--radius-sm);
      max-width: 85%;
      line-height: 1.6;
      font-size: 0.92rem;
      ${sender === 'user' 
        ? 'margin-left: auto; background: linear-gradient(135deg, #2563eb, #00f2fe); color: #fff;' 
        : 'background: rgba(14, 21, 38, 0.85); border: 1px solid var(--border-glow); color: #f8fafc;'}
    `;

    // Format newlines and markdown-like bold
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/\*(.*?)\*/g, '<i>$1</i>')
      .replace(/\n/g, '<br>');

    msg.innerHTML = formatted;
    this.chatContainer.appendChild(msg);
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    return msg;
  }

  async sendMessage() {
    const query = this.input.value.trim();
    if (!query) return;

    this.appendMessage(query, 'user');
    this.input.value = '';

    const thinkingMsg = this.appendMessage('<span class="spinner"></span> Analyzing environmental records...', 'assistant');

    try {
      const res = await window.api.askAssistant(query, this.context);
      thinkingMsg.remove();
      this.appendMessage(res.answer, 'assistant');
    } catch (err) {
      thinkingMsg.remove();
      this.appendMessage(`I encountered an error querying the intelligence engine: ${err.message}`, 'assistant');
    }
  }
}

window.AIAssistant = AIAssistant;
