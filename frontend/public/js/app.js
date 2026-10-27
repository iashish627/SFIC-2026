/* Production API base for the deployed Render backend. */
window.CNG_API_BASE = 'https://cng-network-intelligence-api.onrender.com';
window.CNG_API_BASE_URL = window.CNG_API_BASE;
window.CNG_GIS_API_BASE = window.CNG_API_BASE;

/* Auth guard */
(function () {
  const path = window.location.pathname;
  const publicPages = ['login.html', 'signup.html', 'otp.html', 'index.html'];
  const isPublic = publicPages.some(p => path.endsWith(p));
  if (!isPublic && !localStorage.getItem('cng_auth_token')) {
    window.location.replace('login.html');
  }
})();

/* User display */
const _name = localStorage.getItem('cng_user_name') || 'Demo User';
const _email = localStorage.getItem('cng_user_email') || 'demo@cng.network';
document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = _name);
document.querySelectorAll('[data-user-email]').forEach(el => el.textContent = _email);
document.querySelectorAll('[data-user-avatar]').forEach(el => el.textContent = _name.charAt(0).toUpperCase());

function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('open');
  document.getElementById('overlay')?.classList.toggle('show');
}

/* Sample stations are illustrative UI fixtures, not verified live operating data. */
window.STATIONS = window.STATIONS || [];
window.DISTRICT_COUNTS = window.DISTRICT_COUNTS || {};

function animateValue(el, end, duration = 900) {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const p = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(start + (end - start) * ease).toLocaleString();
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
