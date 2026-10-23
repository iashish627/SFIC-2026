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

/* Sample stations drawn from the real Gujarat directory context */
window.STATIONS = [
  { id:'GGL-0001', name:'GGL Sanskruti Energy CNG Station', district:'Anand', type:'Daughter Booster', pincode:'388307', capacity:1800, peak:1650, util:0.92 },
  { id:'GGL-0008', name:'GGL Siddhi Vinayak Petroleum', district:'Anand', type:'Mother/Online', pincode:'388550', capacity:4200, peak:3800, util:0.90 },
  { id:'GGL-0014', name:'Sai Petroleum (Dahod)', district:'Dahod', type:'Online', pincode:'389151', capacity:2100, peak:1950, util:0.93 },
  { id:'GGL-0036', name:'Gujarat Gas (Halol)', district:'Panchmahal', type:'Mother/Online', pincode:'389350', capacity:3500, peak:2900, util:0.83 },
  { id:'GGL-0048', name:'Gujarat Gas (Kandari)', district:'Vadodara', type:'Mother/Online', pincode:'391210', capacity:4800, peak:5100, util:1.06 },
  { id:'GGL-0078', name:'Gujarat Gas (Dabhan)', district:'Kheda', type:'Mother/Online', pincode:'387320', capacity:3200, peak:2800, util:0.88 },
  { id:'GGL-0116', name:'GGL Ganesh CNG Point', district:'Bharuch', type:'Mother/Online', pincode:'393001', capacity:3900, peak:4100, util:1.05 },
  { id:'GGL-0148', name:'Gujarat Gas (Icchapore Hazira)', district:'Surat', type:'Mother/Online', pincode:'394510', capacity:5500, peak:6200, util:1.13 },
  { id:'GGL-0235', name:'Gujarat Gas (Adajan Gam)', district:'Surat', type:'Online', pincode:'395009', capacity:2800, peak:2650, util:0.95 },
  { id:'GGL-0289', name:'Gujarat Gas (Vapi GIDC)', district:'Valsad', type:'Mother/Online', pincode:'396195', capacity:4100, peak:3800, util:0.93 },
  { id:'GGL-NEW-025', name:'Gujarat Gas (Sector 5)', district:'Gandhinagar', type:'Mother/Online', pincode:'382006', capacity:3000, peak:2700, util:0.90 },
  { id:'GGL-NEW-031', name:'Gujarat Gas (Kalol)', district:'Gandhinagar', type:'Mother/Online', pincode:'382725', capacity:3400, peak:3600, util:1.06 },
  { id:'GGL-AHM-008', name:'Ahmedabad Central Hub', district:'Ahmedabad', type:'Mother/Online', pincode:'380001', capacity:2600, peak:3072, util:1.18 },
  { id:'GGL-SUR-004', name:'Surat Ring Road', district:'Surat', type:'Online', pincode:'395003', capacity:1980, peak:2397, util:1.21 },
  { id:'GGL-VAD-002', name:'Vadodara Bypass', district:'Vadodara', type:'Mother/Online', pincode:'390001', capacity:2380, peak:2742, util:1.15 },
];

window.DISTRICT_COUNTS = {
  'Surat': 78, 'Ahmedabad': 42, 'Bharuch': 41, 'Panchmahal': 28,
  'Anand': 27, 'Kheda': 24, 'Dahod': 22, 'Valsad': 21,
  'Navsari': 19, 'Vadodara': 18, 'Gandhinagar': 12, 'Others': 12
};

/* Animated number */
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
