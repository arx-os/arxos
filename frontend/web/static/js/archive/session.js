// Shared session management for Arx UI

// Get current token
const token = localStorage.getItem('arx_jwt');

// Check if user is authenticated
function isAuthenticated() {
    return !!localStorage.getItem('arx_jwt');
}

// Logout function
function logout() {
    localStorage.removeItem('arx_jwt');
    window.location.href = 'login.html';
}

// Get authorization headers for API requests
function getAuthHeaders() {
    const token = localStorage.getItem('arx_jwt');
    return token ? { 'Authorization': 'Bearer ' + token } : {};
}

// Handle authentication errors
function handleAuthError() {
    localStorage.removeItem('arx_jwt');
    window.location.href = 'login.html';
}

// Check authentication on page load
if (!isAuthenticated()) {
    window.location.href = 'login.html';
}

// Attach JWT to all HTMX requests
if (window.htmx) {
  document.body.addEventListener('htmx:configRequest', function(evt) {
    const token = localStorage.getItem('arx_jwt');
    if (token) {
      evt.detail.headers['Authorization'] = 'Bearer ' + token;
    }
  });
}

// (Optional) Decode JWT to get user info
function parseJwt (token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) { return {}; }
}

// Show user info if available
(function() {
  const token = localStorage.getItem('arx_jwt');
  if (token && document.getElementById('user-info')) {
    const payload = parseJwt(token);
    if (payload.username) {
      document.getElementById('user-info').textContent = payload.username;
    } else if (payload.email) {
      document.getElementById('user-info').textContent = payload.email;
    }
  }
})();
