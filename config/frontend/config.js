/**
 * Arxos Configuration System
 * Centralized configuration with environment-based overrides
 */

// Default configuration
const defaultConfig = {
    // Application metadata
    app: {
        name: 'Arxos',
        version: '1.0.0',
        environment: 'development' // 'development', 'staging', 'production'
    },

    // Ingestion configuration
    ingestion: {
        // Feature flags
        useAI: true,                    // Enable AI-based ingestion
        fallbackToManual: false,         // Fall back to manual extraction if AI fails
        cacheResults: true,              // Cache processed files
        
        // AI Provider settings
        aiProvider: 'openai',           // 'openai', 'google', 'azure'
        aiModel: 'gpt-4-vision-preview', // Specific model to use
        maxRetries: 3,                   // Number of retries on failure
        timeout: 30000,                   // Timeout in milliseconds
        
        // File size limits (in bytes)
        maxFileSize: {
            pdf: 50 * 1024 * 1024,      // 50MB
            image: 25 * 1024 * 1024,     // 25MB
            ifc: 100 * 1024 * 1024,      // 100MB
            lidar: 500 * 1024 * 1024     // 500MB
        },
        
        // Supported formats
        supportedFormats: {
            pdf: ['.pdf'],
            image: ['.jpg', '.jpeg', '.png', '.heic', '.heif'],
            ifc: ['.ifc', '.ifczip'],
            lidar: ['.ply', '.las', '.laz', '.e57', '.usdz']
        }
    },

    // API endpoints
    api: {
        baseUrl: process.env.ARXOS_API_URL || 'http://localhost:8080/api/v1',
        endpoints: {
            aiIngestion: '/ai/ingest',
            ifcParse: '/ifc/parse',
            lidarProcess: '/lidar/process',
            arxobjects: '/arxobjects',
            health: '/health'
        },
        headers: {
            'Content-Type': 'application/json',
            'X-Client-Version': '1.0.0'
        }
    },

    // Rendering configuration
    rendering: {
        defaultScale: 0.5,
        minScale: 0.1,
        maxScale: 10,
        gridSize: 1,                    // 1 meter grid
        wallThickness: 0.2,              // 20cm default wall thickness
        ceilingHeight: 3.0,              // 3m default ceiling height
        
        // Colors (hex values)
        colors: {
            wall: '#4CAF50',
            grid: '#1a1a1a',
            background: '#0a0a0a',
            selection: '#2196F3',
            hover: '#FFC107'
        },
        
        // Performance settings
        maxObjectsPerTile: 1000,
        tileSize: 256,
        enableWebGL: true,
        antialiasing: true
    },

    // Logging configuration
    logging: {
        level: 'info',                   // 'debug', 'info', 'warn', 'error'
        enableConsole: true,
        enableRemote: false,             // Send logs to remote service
        remoteEndpoint: '/api/logs',
        
        // What to log
        logRequests: true,
        logPerformance: true,
        logErrors: true,
        
        // Performance thresholds (ms)
        performanceThresholds: {
            slow: 1000,
            verySlow: 3000
        }
    },

    // Cache configuration
    cache: {
        enabled: true,
        storage: 'localStorage',        // 'localStorage', 'sessionStorage', 'indexedDB'
        ttl: 86400000,                  // 24 hours in milliseconds
        maxSize: 50 * 1024 * 1024,      // 50MB max cache size
        
        // What to cache
        cacheProcessedFiles: true,
        cacheAPIResponses: true,
        cacheTiles: true
    },

    // Error handling
    errorHandling: {
        showUserErrors: true,
        reportToService: false,
        errorReportEndpoint: '/api/errors',
        
        // Retry configuration
        retry: {
            enabled: true,
            maxAttempts: 3,
            backoffMultiplier: 2,
            initialDelay: 1000
        }
    },

    // Feature flags for progressive rollout
    features: {
        enablePDFIngestion: true,
        enableIFCIngestion: true,
        enablePhotoIngestion: true,
        enableLiDARIngestion: false,     // Not yet implemented
        enableCollaboration: false,      // Future feature
        enableCloudSync: false,          // Future feature
        enableOfflineMode: true
    },

    // Development tools
    dev: {
        enableDebugPanel: true,
        enablePerformanceMonitor: true,
        logAPIRequests: true,
        mockAPIResponses: false,
        bypassAuth: true                // Only in development
    }
};

/**
 * Environment-specific overrides
 */
const environmentOverrides = {
    production: {
        app: {
            environment: 'production'
        },
        api: {
            baseUrl: 'https://api.arxos.io/v1'
        },
        logging: {
            level: 'error',
            enableRemote: true
        },
        errorHandling: {
            reportToService: true
        },
        dev: {
            enableDebugPanel: false,
            enablePerformanceMonitor: false,
            logAPIRequests: false,
            mockAPIResponses: false,
            bypassAuth: false
        }
    },
    
    staging: {
        app: {
            environment: 'staging'
        },
        api: {
            baseUrl: 'https://staging-api.arxos.io/v1'
        },
        logging: {
            level: 'info'
        }
    }
};

/**
 * Configuration class with validation and runtime updates
 */
class Configuration {
    constructor() {
        this.config = this.buildConfig();
        this.listeners = new Map();
        this.validateConfig();
    }

    /**
     * Build configuration with environment overrides
     */
    buildConfig() {
        const env = this.detectEnvironment();
        const overrides = environmentOverrides[env] || {};
        
        // Deep merge configuration
        return this.deepMerge(defaultConfig, overrides);
    }

    /**
     * Detect current environment
     */
    detectEnvironment() {
        // Check various sources for environment
        if (typeof process !== 'undefined' && process.env.NODE_ENV) {
            return process.env.NODE_ENV;
        }
        if (typeof window !== 'undefined') {
            if (window.location.hostname === 'localhost') {
                return 'development';
            }
            if (window.location.hostname.includes('staging')) {
                return 'staging';
            }
            if (window.location.hostname.includes('arxos.io')) {
                return 'production';
            }
        }
        return 'development';
    }

    /**
     * Deep merge objects
     */
    deepMerge(target, source) {
        const output = Object.assign({}, target);
        
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        
        return output;
    }

    /**
     * Check if value is an object
     */
    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    /**
     * Validate configuration
     */
    validateConfig() {
        const required = [
            'app.name',
            'app.version',
            'api.baseUrl',
            'ingestion.aiProvider'
        ];

        required.forEach(path => {
            const value = this.get(path);
            if (value === undefined || value === null || value === '') {
                console.error(`Configuration error: ${path} is required`);
            }
        });

        // Validate file size limits
        Object.values(this.config.ingestion.maxFileSize).forEach(size => {
            if (size <= 0) {
                console.error('Configuration error: Invalid file size limit');
            }
        });

        return true;
    }

    /**
     * Get configuration value by path
     */
    get(path, defaultValue = undefined) {
        const keys = path.split('.');
        let value = this.config;
        
        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return defaultValue;
            }
        }
        
        return value;
    }

    /**
     * Set configuration value at runtime
     */
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        let target = this.config;
        
        for (const key of keys) {
            if (!(key in target) || typeof target[key] !== 'object') {
                target[key] = {};
            }
            target = target[key];
        }
        
        const oldValue = target[lastKey];
        target[lastKey] = value;
        
        // Notify listeners
        this.notifyListeners(path, value, oldValue);
        
        return this;
    }

    /**
     * Watch for configuration changes
     */
    watch(path, callback) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        this.listeners.get(path).add(callback);
        
        // Return unwatch function
        return () => {
            const callbacks = this.listeners.get(path);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    /**
     * Notify listeners of changes
     */
    notifyListeners(path, newValue, oldValue) {
        // Exact path listeners
        const exactListeners = this.listeners.get(path);
        if (exactListeners) {
            exactListeners.forEach(callback => {
                callback(newValue, oldValue, path);
            });
        }
        
        // Parent path listeners (watch entire sections)
        const pathParts = path.split('.');
        for (let i = pathParts.length - 1; i > 0; i--) {
            const parentPath = pathParts.slice(0, i).join('.');
            const parentListeners = this.listeners.get(parentPath);
            if (parentListeners) {
                parentListeners.forEach(callback => {
                    callback(this.get(parentPath), undefined, parentPath);
                });
            }
        }
    }

    /**
     * Check if a feature is enabled
     */
    isFeatureEnabled(feature) {
        return this.get(`features.${feature}`, false);
    }

    /**
     * Get all configuration as JSON
     */
    toJSON() {
        return JSON.parse(JSON.stringify(this.config));
    }

    /**
     * Reset to defaults
     */
    reset() {
        this.config = this.buildConfig();
        this.notifyListeners('*', this.config, null);
    }
}

// Create singleton instance
const ARXOS_CONFIG = new Configuration();

// No module exports - pure vanilla JS

// Make available globally in browser
if (typeof window !== 'undefined') {
    window.ARXOS_CONFIG = ARXOS_CONFIG;
}