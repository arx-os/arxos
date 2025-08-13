/**
 * ArxLogger - Production-grade logging for Arxos frontend
 * Provides structured logging with correlation tracking and remote logging capability
 */
class ArxLogger {
    constructor(options = {}) {
        this.service = options.service || 'arx-web-frontend';
        this.version = options.version || '1.0.0';
        this.environment = options.environment || 'development';
        this.logLevel = options.logLevel || 'info';
        this.enableRemoteLogging = options.enableRemoteLogging || false;
        this.remoteEndpoint = options.remoteEndpoint || '/api/logs/aggregate';
        this.batchSize = options.batchSize || 10;
        this.batchTimeout = options.batchTimeout || 5000; // 5 seconds

        // Log levels
        this.levels = {
            debug: 0,
            info: 1,
            warning: 2,
            error: 3,
            critical: 4
        };

        // Context tracking
        this.correlationId = null;
        this.requestId = null;
        this.userId = null;
        this.sessionId = null;
        this.buildingId = null;
        this.floorId = null;

        // Log batching for remote logging
        this.logBatch = [];
        this.batchTimer = null;

        // Performance tracking
        this.performanceStats = {};

        // Initialize
        this._generateSessionId();
        this._setupErrorHandling();
        this._startBatchTimer();
    }

    /**
     * Generate a unique session ID
     */
    _generateSessionId() {
        this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Generate a correlation ID
     */
    generateCorrelationId() {
        this.correlationId = 'corr_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        return this.correlationId;
    }

    /**
     * Generate a request ID
     */
    generateRequestId() {
        this.requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        return this.requestId;
    }

    /**
     * Set context for logging
     */
    setContext(context) {
        if (context.correlationId) this.correlationId = context.correlationId;
        if (context.requestId) this.requestId = context.requestId;
        if (context.userId) this.userId = context.userId;
        if (context.buildingId) this.buildingId = context.buildingId;
        if (context.floorId) this.floorId = context.floorId;
    }

    /**
     * Clear context
     */
    clearContext() {
        this.correlationId = null;
        this.requestId = null;
        this.userId = null;
        this.buildingId = null;
        this.floorId = null;
    }

    /**
     * Check if log level should be output
     */
    _shouldLog(level) {
        return this.levels[level] >= this.levels[this.logLevel];
    }

    /**
     * Create structured log entry
     */
    _createLogEntry(level, message, metadata = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            level: level,
            message: message,
            service: this.service,
            version: this.version,
            environment: this.environment,
            correlation_id: this.correlationId,
            request_id: this.requestId,
            user_id: this.userId,
            session_id: this.sessionId,
            building_id: this.buildingId,
            floor_id: this.floorId,
            url: window.location.href,
            user_agent: navigator.userAgent,
            metadata: metadata
        };

        // Add performance data if available
        if (metadata.performance) {
            entry.performance = metadata.performance;
        }

        return entry;
    }

    /**
     * Log to console and remote endpoint
     */
    _log(level, message, metadata = {}) {
        if (!this._shouldLog(level)) return;

        const entry = this._createLogEntry(level, message, metadata);

        // Console logging
        const consoleMethod = level === 'error' ? 'error' :
                             level === 'warning' ? 'warn' :
                             level === 'debug' ? 'debug' : 'log';

        console[consoleMethod](`[${level.toUpperCase()}] ${message}`, entry);

        // Remote logging
        if (this.enableRemoteLogging) {
            this._addToBatch(entry);
        }
    }

    /**
     * Add log entry to batch for remote logging
     */
    _addToBatch(entry) {
        this.logBatch.push(entry);

        if (this.logBatch.length >= this.batchSize) {
            this._sendBatch();
        }
    }

    /**
     * Send log batch to remote endpoint
     */
    async _sendBatch() {
        if (this.logBatch.length === 0) return;

        const batch = [...this.logBatch];
        this.logBatch = [];

        try {
            const response = await fetch(this.remoteEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': localStorage.getItem('arx_jwt') ?
                        'Bearer ' + localStorage.getItem('arx_jwt') : ''
                },
                body: JSON.stringify(batch)
            });

            if (!response.ok) {
                console.warn('Failed to send logs to remote endpoint:', response.status);
            }
        } catch (error) {
            console.warn('Error sending logs to remote endpoint:', error);
        }
    }

    /**
     * Start batch timer for periodic log sending
     */
    _startBatchTimer() {
        this.batchTimer = setInterval(() => {
            if (this.logBatch.length > 0) {
                this._sendBatch();
            }
        }, this.batchTimeout);
    }

    /**
     * Setup global error handling
     */
    _setupErrorHandling() {
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.error('Unhandled promise rejection', {
                reason: event.reason,
                stack: event.reason?.stack
            });
        });

        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            this.error('JavaScript error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error?.stack
            });
        });

        // Handle resource loading errors
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.error('Resource loading error', {
                    type: event.target.tagName,
                    src: event.target.src || event.target.href,
                    message: event.message
                });
            }
        }, true);
    }

    /**
     * Log methods
     */
    debug(message, metadata = {}) {
        this._log('debug', message, metadata);
    }

    info(message, metadata = {}) {
        this._log('info', message, metadata);
    }

    warning(message, metadata = {}) {
        this._log('warning', message, metadata);
    }

    error(message, metadata = {}) {
        this._log('error', message, metadata);
    }

    critical(message, metadata = {}) {
        this._log('critical', message, metadata);
    }

    /**
     * Log API request
     */
    logApiRequest(method, url, statusCode, duration, responseSize = 0, metadata = {}) {
        this.info(`API Request: ${method} ${url} - ${statusCode} (${duration.toFixed(3)}s)`, {
            method,
            url,
            status_code: statusCode,
            duration,
            response_size: responseSize,
            ...metadata
        });
    }

    /**
     * Log API error
     */
    logApiError(method, url, statusCode, error, duration = 0, metadata = {}) {
        this.error(`API Error: ${method} ${url} - ${statusCode}`, {
            method,
            url,
            status_code: statusCode,
            duration,
            error_message: error.message,
            error_stack: error.stack,
            ...metadata
        });
    }

    /**
     * Log business event
     */
    logBusinessEvent(eventType, eventName, metrics = {}, metadata = {}) {
        this.info(`Business Event: ${eventType} - ${eventName}`, {
            event_type: eventType,
            event_name: eventName,
            metrics,
            ...metadata
        });
    }

    /**
     * Log performance metrics
     */
    logPerformance(operation, duration, metadata = {}) {
        this.info(`Performance: ${operation} - ${duration.toFixed(3)}s`, {
            operation,
            duration,
            ...metadata
        });

        // Track performance statistics
        if (!this.performanceStats[operation]) {
            this.performanceStats[operation] = {
                count: 0,
                totalTime: 0,
                minTime: Infinity,
                maxTime: 0,
                avgTime: 0
            };
        }

        const stats = this.performanceStats[operation];
        stats.count++;
        stats.totalTime += duration;
        stats.minTime = Math.min(stats.minTime, duration);
        stats.maxTime = Math.max(stats.maxTime, duration);
        stats.avgTime = stats.totalTime / stats.count;
    }

    /**
     * Get performance statistics
     */
    getPerformanceStats() {
        return this.performanceStats;
    }

    /**
     * Log user interaction
     */
    logUserInteraction(action, element, metadata = {}) {
        this.info(`User Interaction: ${action}`, {
            action,
            element: element.tagName || element,
            element_id: element.id,
            element_class: element.className,
            ...metadata
        });
    }

    /**
     * Log page navigation
     */
    logPageNavigation(fromPage, toPage, metadata = {}) {
        this.info(`Page Navigation: ${fromPage} -> ${toPage}`, {
            from_page: fromPage,
            to_page: toPage,
            ...metadata
        });
    }

    /**
     * Log form submission
     */
    logFormSubmission(formName, success, metadata = {}) {
        this.info(`Form Submission: ${formName} - ${success ? 'SUCCESS' : 'FAILED'}`, {
            form_name: formName,
            success,
            ...metadata
        });
    }

    /**
     * Log asset operation
     */
    logAssetOperation(operation, assetId, assetType, metadata = {}) {
        this.info(`Asset Operation: ${operation}`, {
            operation,
            asset_id: assetId,
            asset_type: assetType,
            ...metadata
        });
    }

    /**
     * Performance tracker decorator
     */
    performanceTracker(operationName = null) {
        return (target, propertyKey, descriptor) => {
            const method = descriptor.value;
            const opName = operationName || `${target.constructor.name}.${propertyKey}`;

            descriptor.value = async function(...args) {
                const startTime = performance.now();

                try {
                    const result = await method.apply(this, args);
                    const duration = performance.now() - startTime;

                    if (window.arxLogger) {
                        window.arxLogger.logPerformance(opName, duration);
                    }

                    return result;
                } catch (error) {
                    const duration = performance.now() - startTime;

                    if (window.arxLogger) {
                        window.arxLogger.logPerformance(opName, duration, { error: error.message });
                    }

                    throw error;
                }
            };

            return descriptor;
        };
    }

    /**
     * Cleanup and send remaining logs
     */
    async cleanup() {
        if (this.batchTimer) {
            clearInterval(this.batchTimer);
        }

        if (this.logBatch.length > 0) {
            await this._sendBatch();
        }
    }
}

// Create global logger instance
window.arxLogger = new ArxLogger({
    service: 'arx-web-frontend',
    version: '1.0.0',
    environment: window.location.hostname === 'localhost' ? 'development' : 'production',
    logLevel: 'info',
    enableRemoteLogging: true,
    remoteEndpoint: '/api/logs/aggregate'
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxLogger;
}
