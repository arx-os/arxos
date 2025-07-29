/**
 * Authentication Manager for Arxos Platform
 * Handles user authentication, token management, and session state
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        this.apiClient = this.createApiClient();
        this.init();
    }

    createApiClient() {
        const baseURL = window.location.origin;
        return {
            async request(endpoint, options = {}) {
                const token = localStorage.getItem('access_token');
                const config = {
                    method: options.method || 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token && { 'Authorization': `Bearer ${token}` }),
                        ...options.headers
                    },
                    ...options
                };

                try {
                    const response = await fetch(`${baseURL}${endpoint}`, config);
                    
                    if (response.status === 401) {
                        // Try token refresh
                        const refreshed = await this.refreshToken();
                        if (!refreshed) {
                            window.location.href = '/login';
                            return;
                        }
                        // Retry original request
                        return this.request(endpoint, options);
                    }

                    return response;
                } catch (error) {
                    console.error('API request failed:', error);
                    throw error;
                }
            },

            async refreshToken() {
                const refreshToken = localStorage.getItem('refresh_token');
                if (!refreshToken) return false;

                try {
                    const response = await fetch('/auth/refresh', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh_token: refreshToken })
                    });

                    if (response.ok) {
                        const { access_token } = await response.json();
                        localStorage.setItem('access_token', access_token);
                        return true;
                    }
                } catch (error) {
                    console.error('Token refresh failed:', error);
                }

                // Clear tokens and redirect to login
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                return false;
            }
        };
    }

    async init() {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const response = await this.apiClient.request('/auth/me');
                if (response.ok) {
                    this.user = await response.json();
                    this.isAuthenticated = true;
                    this.updateUI();
                } else {
                    this.logout();
                }
            } catch (error) {
                this.logout();
            }
        } else {
            this.showLogin();
        }
    }

    async login(credentials) {
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials)
            });

            if (response.ok) {
                const { access_token, refresh_token, user } = await response.json();
                localStorage.setItem('access_token', access_token);
                localStorage.setItem('refresh_token', refresh_token);
                this.user = user;
                this.isAuthenticated = true;
                this.updateUI();
                window.toastManager.show('Login successful', 'success');
                return true;
            } else {
                const error = await response.json();
                window.toastManager.show(error.message, 'error');
                return false;
            }
        } catch (error) {
            window.toastManager.show('Login failed', 'error');
            return false;
        }
    }

    async logout() {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
        } catch (error) {
            console.error('Logout request failed:', error);
        }

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.user = null;
        this.isAuthenticated = false;
        this.showLogin();
    }

    updateUI() {
        if (this.isAuthenticated) {
            htmx.ajax('GET', '/dashboard', { target: '#main-content' });
        } else {
            this.showLogin();
        }
    }

    showLogin() {
        htmx.ajax('GET', '/login', { target: '#main-content' });
    }

    hasPermission(permission) {
        return this.user?.permissions?.includes(permission) || false;
    }

    hasRole(role) {
        return this.user?.role === role;
    }

    // HTMX request interceptor
    setupHTMXInterceptor() {
        document.body.addEventListener('htmx:configRequest', (event) => {
            const token = localStorage.getItem('access_token');
            if (token) {
                event.detail.headers['Authorization'] = `Bearer ${token}`;
            }
        });

        document.body.addEventListener('htmx:responseError', (event) => {
            if (event.detail.xhr.status === 401 || event.detail.xhr.status === 403) {
                this.logout();
            }
        });
    }
}

// Export for global use
window.AuthManager = AuthManager; 