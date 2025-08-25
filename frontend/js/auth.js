// ARXOS Authentication Module

function checkAuth() {
    const token = localStorage.getItem('arxos_token');
    const user = localStorage.getItem('arxos_user');
    
    if (token && user) {
        // Update UI with user info
        updateUserUI(JSON.parse(user));
        
        // Verify token is still valid
        verifyToken(token);
    } else if (window.location.pathname !== '/' && !window.location.pathname.startsWith('/login')) {
        // Redirect to login if not on public pages
        window.location.href = '/login';
    }
}

function updateUserUI(user) {
    // Update user avatar
    const avatar = document.getElementById('user-avatar');
    if (avatar) {
        avatar.textContent = (user.name || user.email || 'U').charAt(0).toUpperCase();
    }
    
    // Update user info in dropdown
    const userName = document.getElementById('user-name');
    const userEmail = document.getElementById('user-email');
    
    if (userName) userName.textContent = user.name || 'User';
    if (userEmail) userEmail.textContent = user.email || '';
    
    // Update notification count if available
    if (user.notifications) {
        const notificationCount = document.getElementById('notification-count');
        if (notificationCount) {
            notificationCount.textContent = user.notifications;
            notificationCount.style.display = user.notifications > 0 ? 'block' : 'none';
        }
    }
}

function verifyToken(token) {
    fetch('/api/auth/verify', {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Token invalid');
        }
        return response.json();
    })
    .catch(error => {
        console.error('Token verification failed:', error);
        logout();
    });
}

function login(username, password) {
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Login failed');
        }
        return response.json();
    })
    .then(data => {
        // Store token and user info
        localStorage.setItem('arxos_token', data.token);
        localStorage.setItem('arxos_user', JSON.stringify(data.user));
        
        // Update UI
        updateUserUI(data.user);
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
    })
    .catch(error => {
        console.error('Login error:', error);
        showLoginError('Invalid username or password');
    });
}

function logout() {
    // Clear local storage
    localStorage.removeItem('arxos_token');
    localStorage.removeItem('arxos_user');
    
    // Call logout endpoint
    fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        }
    }).finally(() => {
        // Redirect to landing page
        window.location.href = '/';
    });
}

function showLoginError(message) {
    const loginMessage = document.getElementById('login-message');
    if (loginMessage) {
        loginMessage.innerHTML = `
            <div class="alert alert-error">
                ${message}
            </div>
        `;
    }
}

// Handle login form submission
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            login(username, password);
        });
    }
    
    // Handle login button on landing page
    const loginButtons = document.querySelectorAll('[onclick*="login"]');
    loginButtons.forEach(button => {
        if (button.getAttribute('onclick') === "window.location.href='/login'") {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                showLoginModal();
            });
        }
    });
});

function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Focus username field
        document.getElementById('username').focus();
    }
}

// Export auth functions
window.auth = {
    checkAuth,
    login,
    logout,
    showLoginModal
};