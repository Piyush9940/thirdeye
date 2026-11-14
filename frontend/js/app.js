/**
 * NASA Earth Systems Trend Detective
 * Core Application Initialization & Shared UI Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const toggleBtn = document.querySelector('.nav-mobile-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }

  // 2. Active Page Highlighting
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // 3. Navbar scroll effect
  const nav = document.querySelector('.nasa-nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    });
  }
});

// Global UI Toast / Alert Notification
window.showToast = function(message, type = 'info') {
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const colors = {
    info: 'border-left: 3px solid #00d2ff; background: rgba(13,23,48,0.95);',
    success: 'border-left: 3px solid #10b981; background: rgba(13,23,48,0.95);',
    warning: 'border-left: 3px solid #f59e0b; background: rgba(13,23,48,0.95);',
    error: 'border-left: 3px solid #ef4444; background: rgba(13,23,48,0.95);'
  };

  toast.style.cssText = `
    padding: 0.75rem 1.25rem;
    border-radius: 6px;
    color: #fff;
    font-size: 0.85rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.5);
    backdrop-filter: blur(10px);
    ${colors[type] || colors.info}
    transition: opacity 0.3s ease, transform 0.3s ease;
  `;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};
