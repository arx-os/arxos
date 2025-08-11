/**
 * Arxos API Client
 * Real-time backend integration for arxos.io
 * Pure JavaScript implementation with WebSocket support
 */

class ArxosAPIClient {
    constructor(options = {}) {
        this.baseURL = options.baseURL || 'http://localhost:8000/api/v1';
        this.wsURL = options.wsURL || 'ws://localhost:8000/ws';
        this.token = null;
        this.websocket = null;
        this.isConnected = false;
        this.retryAttempts = 0;
        this.maxRetries = 5;
        
        this.eventListeners = new Map();
        this.requestQueue = [];
        this.isOffline = false;
        
        this.initializeClient();
    }

    /**
     * Initialize API client
     */
    initializeClient() {
        this.setupOfflineDetection();
        this.loadStoredToken();
        
        // Initialize WebSocket connection
        if (this.token) {
            this.connectWebSocket();
        }
    }

    /**
     * Setup offline/online detection
     */
    setupOfflineDetection() {
        window.addEventListener('online', () => {
            this.isOffline = false;
            this.processQueuedRequests();
            this.emit('connection:restored');
        });
        
        window.addEventListener('offline', () => {
            this.isOffline = true;
            this.emit('connection:lost');
        });
    }

    /**
     * Load stored authentication token
     */
    loadStoredToken() {
        try {
            const stored = localStorage.getItem('arxos_auth_token');
            if (stored) {
                const tokenData = JSON.parse(stored);
                if (tokenData.expires_at > Date.now()) {
                    this.token = tokenData.token;
                } else {
                    localStorage.removeItem('arxos_auth_token');
                }
            }
        } catch (error) {
            console.error('Error loading stored token:', error);
        }
    }

    /**
     * Store authentication token
     */
    storeToken(token, expiresIn) {
        const tokenData = {
            token: token,
            expires_at: Date.now() + (expiresIn * 1000)
        };
        
        try {
            localStorage.setItem('arxos_auth_token', JSON.stringify(tokenData));
            this.token = token;
        } catch (error) {
            console.error('Error storing token:', error);
        }
    }

    /**
     * Authenticate with username/password
     */
    async authenticate(username, password) {
        try {
            const response = await this.request('POST', '/auth/login', {
                username: username,
                password: password,
                client_info: {
                    user_agent: navigator.userAgent,
                    timestamp: new Date().toISOString()
                }
            }, false);

            if (response.success) {
                this.storeToken(response.data.access_token, response.data.expires_in);
                this.connectWebSocket();
                this.emit('auth:success', response.data.user);
                return response;
            } else {
                this.emit('auth:error', response.error);
                throw new Error(response.error.message);
            }
        } catch (error) {
            this.emit('auth:error', error);
            throw error;
        }
    }

    /**
     * Logout and clear authentication
     */
    async logout() {
        try {
            if (this.token) {
                await this.request('POST', '/auth/logout', {
                    token: this.token
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.token = null;
            localStorage.removeItem('arxos_auth_token');
            
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            
            this.isConnected = false;
            this.emit('auth:logout');
        }
    }

    /**
     * Make HTTP request to API
     */
    async request(method, endpoint, data = null, requireAuth = true) {
        if (requireAuth && !this.token) {
            throw new Error('Authentication required');
        }

        if (this.isOffline) {
            return this.queueRequest(method, endpoint, data, requireAuth);
        }

        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
        };

        if (requireAuth && this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const options = {
            method: method,
            headers: headers,
            body: data ? JSON.stringify(data) : null
        };

        try {
            const response = await fetch(url, options);
            const result = await response.json();
            
            // Handle authentication errors
            if (response.status === 401) {
                this.emit('auth:expired');
                this.token = null;
                localStorage.removeItem('arxos_auth_token');
                throw new Error('Authentication expired');
            }

            return result;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                // Network error - queue request if authenticated
                if (requireAuth) {
                    return this.queueRequest(method, endpoint, data, requireAuth);
                }
            }
            throw error;
        }
    }

    /**
     * Queue request for later processing
     */
    queueRequest(method, endpoint, data, requireAuth) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({
                method, endpoint, data, requireAuth, resolve, reject
            });
            
            this.emit('request:queued', { endpoint, method });
        });
    }

    /**
     * Process queued requests
     */
    async processQueuedRequests() {
        const queue = [...this.requestQueue];
        this.requestQueue = [];

        for (const request of queue) {
            try {
                const result = await this.request(
                    request.method,
                    request.endpoint,
                    request.data,
                    request.requireAuth
                );
                request.resolve(result);
            } catch (error) {
                request.reject(error);
            }
        }

        if (queue.length > 0) {
            this.emit('requests:processed', queue.length);
        }
    }

    /**
     * Connect WebSocket for real-time updates
     */
    connectWebSocket() {
        if (!this.token || this.websocket) {
            return;
        }

        try {
            const wsUrl = `${this.wsURL}?token=${this.token}`;
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                this.isConnected = true;
                this.retryAttempts = 0;
                this.emit('websocket:connected');
                console.log('WebSocket connected to Arxos backend');
            };

            this.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('WebSocket message parsing error:', error);
                }
            };

            this.websocket.onclose = (event) => {
                this.isConnected = false;
                this.websocket = null;
                this.emit('websocket:disconnected', event);

                // Attempt to reconnect if not a normal closure
                if (event.code !== 1000 && this.retryAttempts < this.maxRetries) {
                    setTimeout(() => {
                        this.retryAttempts++;
                        this.connectWebSocket();
                    }, Math.pow(2, this.retryAttempts) * 1000);
                }
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('websocket:error', error);
            };

        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.emit('websocket:error', error);
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'optimization_update':
                this.emit('optimization:update', message.data);
                break;
                
            case 'building_changed':
                this.emit('building:changed', message.data);
                break;
                
            case 'constraint_violation':
                this.emit('constraint:violation', message.data);
                break;
                
            case 'system_metrics':
                this.emit('metrics:update', message.data);
                break;
                
            case 'user_notification':
                this.emit('notification', message.data);
                break;
                
            default:
                this.emit('message', message);
                break;
        }
    }

    /**
     * Send message via WebSocket
     */
    sendWebSocketMessage(type, data) {
        if (this.websocket && this.isConnected) {
            const message = {
                type: type,
                data: data,
                timestamp: new Date().toISOString()
            };
            
            this.websocket.send(JSON.stringify(message));
            return true;
        }
        
        return false;
    }

    // API Methods

    /**
     * Get system health and metrics
     */
    async getSystemHealth() {
        return this.request('GET', '/health');
    }

    /**
     * Get real-time metrics
     */
    async getMetrics() {
        return this.request('GET', '/metrics');
    }

    /**
     * Get buildings list
     */
    async getBuildings(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/buildings${queryString ? `?${queryString}` : ''}`;
        return this.request('GET', endpoint);
    }

    /**
     * Get specific building
     */
    async getBuilding(buildingId, options = {}) {
        const queryString = new URLSearchParams(options).toString();
        const endpoint = `/buildings/${buildingId}${queryString ? `?${queryString}` : ''}`;
        return this.request('GET', endpoint);
    }

    /**
     * Create new building
     */
    async createBuilding(buildingData) {
        return this.request('POST', '/buildings', buildingData);
    }

    /**
     * Update building
     */
    async updateBuilding(buildingId, buildingData) {
        return this.request('PUT', `/buildings/${buildingId}`, buildingData);
    }

    /**
     * Delete building
     */
    async deleteBuilding(buildingId, options = {}) {
        const queryString = new URLSearchParams(options).toString();
        const endpoint = `/buildings/${buildingId}${queryString ? `?${queryString}` : ''}`;
        return this.request('DELETE', endpoint);
    }

    /**
     * Run optimization
     */
    async runOptimization(optimizationConfig) {
        return this.request('POST', '/optimization/run', optimizationConfig);
    }

    /**
     * Get optimization results
     */
    async getOptimizationResults(optimizationId) {
        return this.request('GET', `/optimization/${optimizationId}/results`);
    }

    /**
     * Validate building constraints
     */
    async validateConstraints(buildingId, constraints) {
        return this.request('POST', `/buildings/${buildingId}/validate`, { constraints });
    }

    /**
     * Search across entities
     */
    async search(query, options = {}) {
        const params = { q: query, ...options };
        const queryString = new URLSearchParams(params).toString();
        return this.request('GET', `/search?${queryString}`);
    }

    /**
     * Get analytics dashboard data
     */
    async getAnalytics() {
        return this.request('GET', '/analytics/dashboard');
    }

    // Event System

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * Emit event
     */
    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isAuthenticated: !!this.token,
            isConnected: this.isConnected,
            isOffline: this.isOffline,
            queuedRequests: this.requestQueue.length
        };
    }
}

// Real-time data manager
class RealTimeDataManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.subscriptions = new Map();
        this.dataCache = new Map();
        
        this.setupEventListeners();
    }

    /**
     * Setup API client event listeners
     */
    setupEventListeners() {
        this.apiClient.on('optimization:update', (data) => {
            this.updateData('optimization', data);
        });

        this.apiClient.on('metrics:update', (data) => {
            this.updateData('metrics', data);
        });

        this.apiClient.on('building:changed', (data) => {
            this.updateData(`building:${data.id}`, data);
        });
    }

    /**
     * Subscribe to real-time updates
     */
    subscribe(dataType, callback) {
        if (!this.subscriptions.has(dataType)) {
            this.subscriptions.set(dataType, new Set());
        }
        
        this.subscriptions.get(dataType).add(callback);
        
        // Send cached data if available
        if (this.dataCache.has(dataType)) {
            callback(this.dataCache.get(dataType));
        }
    }

    /**
     * Unsubscribe from updates
     */
    unsubscribe(dataType, callback) {
        const subscribers = this.subscriptions.get(dataType);
        if (subscribers) {
            subscribers.delete(callback);
        }
    }

    /**
     * Update data and notify subscribers
     */
    updateData(dataType, data) {
        this.dataCache.set(dataType, data);
        
        const subscribers = this.subscriptions.get(dataType);
        if (subscribers) {
            subscribers.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in subscriber callback for ${dataType}:`, error);
                }
            });
        }
    }

    /**
     * Get cached data
     */
    getData(dataType) {
        return this.dataCache.get(dataType);
    }
}

// Initialize global API client
document.addEventListener('DOMContentLoaded', () => {
    // Determine API URLs based on environment
    const isProduction = window.location.hostname !== 'localhost';
    const baseURL = isProduction ? 'https://api.arxos.com/v1' : 'http://localhost:8000/api/v1';
    const wsURL = isProduction ? 'wss://api.arxos.com/ws' : 'ws://localhost:8000/ws';
    
    window.arxosAPI = new ArxosAPIClient({
        baseURL: baseURL,
        wsURL: wsURL
    });
    
    window.realTimeData = new RealTimeDataManager(window.arxosAPI);
    
    console.log('Arxos API Client initialized');
});

// Export for external use
window.ArxosAPIClient = ArxosAPIClient;
window.RealTimeDataManager = RealTimeDataManager;