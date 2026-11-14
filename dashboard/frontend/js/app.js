/**
 * NASA Earth Systems Trend Detective — Common Shell & Utility Code
 */

document.addEventListener('DOMContentLoaded', () => {
  highlightActiveNav();
  initSystemStatusBar();
});

function highlightActiveNav() {
  const currentPath = window.location.pathname;
  const links = document.querySelectorAll('.nav-link');
  links.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (currentPath === href || (currentPath.includes(href) && href !== '/')) {
      link.classList.add('active');
    }
  });
}

function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fas ${type === 'error' ? 'fa-triangle-exclamation text-rose' : 'fa-circle-check text-cyan'}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
window.showToast = showToast;

async function initSystemStatusBar() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.status === 'healthy') {
      const el = document.getElementById('status-server');
      if (el) el.innerHTML = '<span class="status-dot"></span> Node.js API: Healthy';
    }
  } catch (_) {
    const el = document.getElementById('status-server');
    if (el) el.innerHTML = '<span class="status-dot amber"></span> Node.js API: Standalone';
  }
}

// Utility formatters
window.formatNumber = (val, dec = 3) => {
  if (val === undefined || val === null || isNaN(val)) return '—';
  return Number(val).toFixed(dec);
};
