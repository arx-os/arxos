// Minimal JavaScript for HTMX-powered ARXOS
// Only handles what HTMX cannot do directly

(function() {
    'use strict';
    
    // Configuration for HTMX
    htmx.config.defaultSwapStyle = 'innerHTML';
    htmx.config.historyCacheSize = 10;
    htmx.config.refreshOnHistoryMiss = true;
    
    // Authentication token management
    const auth = {
        getToken() {
            return localStorage.getItem('arxos_token');
        },
        
        setToken(token) {
            localStorage.setItem('arxos_token', token);
        },
        
        clearToken() {
            localStorage.removeItem('arxos_token');
            localStorage.removeItem('arxos_user');
        },
        
        getUser() {
            const user = localStorage.getItem('arxos_user');
            return user ? JSON.parse(user) : null;
        },
        
        setUser(user) {
            localStorage.setItem('arxos_user', JSON.stringify(user));
        }
    };
    
    // HTMX Event Handlers
    document.body.addEventListener('htmx:configRequest', (evt) => {
        // Add auth token to all requests
        const token = auth.getToken();
        if (token) {
            evt.detail.headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add CSRF token if present
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrf) {
            evt.detail.headers['X-CSRF-Token'] = csrf;
        }
    });
    
    // Handle authentication responses
    document.body.addEventListener('htmx:beforeSwap', (evt) => {
        // Check for auth tokens in response headers
        const token = evt.detail.xhr.getResponseHeader('X-Auth-Token');
        if (token) {
            auth.setToken(token);
        }
        
        // Handle 401 responses
        if (evt.detail.xhr.status === 401) {
            auth.clearToken();
            // Let server redirect to login
            evt.detail.shouldSwap = true;
        }
    });
    
    // Handle server-sent auth events
    document.body.addEventListener('auth:login', (evt) => {
        auth.setToken(evt.detail.token);
        auth.setUser(evt.detail.user);
        // Trigger a refresh of user-dependent content
        htmx.trigger(document.body, 'auth:changed');
    });
    
    document.body.addEventListener('auth:logout', (evt) => {
        auth.clearToken();
        // Server will handle redirect
    });
    
    // WebSocket connection status
    let wsReconnectTimer = null;
    
    document.body.addEventListener('htmx:wsClose', (evt) => {
        // Auto-reconnect WebSocket after 5 seconds
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = setTimeout(() => {
            htmx.trigger(evt.detail.elt, 'htmx:wsReconnect');
        }, 5000);
    });
    
    document.body.addEventListener('htmx:wsOpen', (evt) => {
        clearTimeout(wsReconnectTimer);
        console.log('WebSocket connected');
    });
    
    // File upload progress (HTMX doesn't handle this well)
    document.body.addEventListener('htmx:xhr:progress', (evt) => {
        const progressBar = evt.detail.elt.querySelector('.upload-progress');
        if (progressBar && evt.detail.loaded && evt.detail.total) {
            const percentComplete = (evt.detail.loaded / evt.detail.total) * 100;
            progressBar.style.width = percentComplete + '%';
        }
    });
    
    // Handle file drag and drop (enhance HTMX basic support)
    const initFileDrop = () => {
        const dropZones = document.querySelectorAll('[data-file-drop]');
        
        dropZones.forEach(zone => {
            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });
            
            // Visual feedback
            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => {
                    zone.classList.add('drag-over');
                }, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => {
                    zone.classList.remove('drag-over');
                }, false);
            });
            
            // Handle dropped files
            zone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                const input = zone.querySelector('input[type="file"]');
                
                if (input && files.length > 0) {
                    // Trigger HTMX upload
                    input.files = files;
                    htmx.trigger(input, 'change');
                }
            }, false);
        });
    };
    
    // Initialize on HTMX load
    document.body.addEventListener('htmx:afterSwap', (evt) => {
        // Reinitialize file drops after content swap
        if (evt.detail.target.querySelector('[data-file-drop]')) {
            initFileDrop();
        }
    });
    
    // Initial setup
    document.addEventListener('DOMContentLoaded', () => {
        initFileDrop();
        
        // Check auth status
        const user = auth.getUser();
        if (user) {
            htmx.trigger(document.body, 'auth:restored', { user });
        }
    });
    
    // Expose minimal API for server-triggered events
    window.arxos = {
        auth,
        
        // Server can call this to show notifications
        notify(message, type = 'info') {
            const event = new CustomEvent('arxos:notification', {
                detail: { message, type }
            });
            document.body.dispatchEvent(event);
        },
        
        // Server can call this to update specific elements
        updateElement(selector, html) {
            const element = document.querySelector(selector);
            if (element) {
                element.innerHTML = html;
                htmx.process(element);
            }
        }
    };
})();