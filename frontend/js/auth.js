/**
 * NASA Earth Systems Trend Detective
 * Client Authentication Handler
 */

const Auth = {
  getToken() {
    return localStorage.getItem('nasa_token');
  },

  getUser() {
    const raw = localStorage.getItem('nasa_user');
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  setSession(token, user) {
    localStorage.setItem('nasa_token', token);
    localStorage.setItem('nasa_user', JSON.stringify(user));
    this.updateNavUI();
  },

  logout() {
    localStorage.removeItem('nasa_token');
    localStorage.removeItem('nasa_user');
    window.location.href = 'login.html';
  },

  updateNavUI() {
    const authContainer = document.getElementById('navAuthContainer');
    if (!authContainer) return;

    const user = this.getUser();
    if (user && this.isAuthenticated()) {
      authContainer.innerHTML = `
        <div class="nav-dropdown">
          <button class="btn-nasa btn-nasa-outline btn-sm">
            <span class="live-indicator"></span> ${user.name || user.email || 'Researcher'}
          </button>
          <ul class="nav-dropdown-menu">
            <li class="nav-dropdown-item"><a href="reports.html">My Saved Reports</a></li>
            <li class="nav-dropdown-item"><a href="#" onclick="Auth.logout(); return false;">Log Out</a></li>
          </ul>
        </div>
      `;
    } else {
      authContainer.innerHTML = `
        <a href="login.html" class="btn-nasa btn-nasa-outline btn-sm">Sign In</a>
        <a href="register.html" class="btn-nasa btn-nasa-primary btn-sm">Register</a>
      `;
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Auth.updateNavUI();
});

window.Auth = Auth;
