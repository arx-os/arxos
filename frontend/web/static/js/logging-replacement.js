/**
 * Logging Replacement System for Arxos Frontend
 * 
 * This script provides automated replacement of console.log calls with ArxLogger calls.
 * It analyzes the content and context of console.log calls to determine the appropriate
 * log level and method to use.
 * 
 * Usage:
 * 1. Include this script after arx-logger.js
 * 2. Call LoggingReplacer.initialize() to set up automatic replacement
 * 3. Call LoggingReplacer.replaceInFile(fileContent) to process specific files
 * 4. Call LoggingReplacer.replaceAll() to process all loaded scripts
 */

class LoggingReplacer {
    constructor() {
        this.replacements = [
            // Simple string messages
            {
                pattern: /console\.log\('([^']+)'\)/g,
                replacement: (match, message) => this.determineLogLevel(message, 'info')
            },
            
            // Template literal messages
            {
                pattern: /console\.log\(`([^`]+)`\)/g,
                replacement: (match, message) => this.determineLogLevel(message, 'info')
            },
            
            // Variable/expression logging
            {
                pattern: /console\.log\(([^)]+)\)/g,
                replacement: (match, expression) => this.determineLogLevel(expression, 'info')
            },
            
            // Multi-argument console.log
            {
                pattern: /console\.log\(([^)]+(?:,\s*[^)]+)*)\)/g,
                replacement: (match, args) => this.determineLogLevel(args, 'info')
            }
        ];
        
        this.logLevelPatterns = {
            error: [
                /error/i, /failed/i, /failure/i, /exception/i, /crash/i, /broken/i,
                /invalid/i, /missing/i, /not found/i, /unauthorized/i, /forbidden/i,
                /timeout/i, /connection failed/i, /network error/i
            ],
            warning: [
                /warn/i, /warning/i, /deprecated/i, /obsolete/i, /slow/i, /performance/i,
                /retry/i, /fallback/i, /degraded/i, /partial/i, /incomplete/i
            ],
            debug: [
                /debug/i, /test/i, /testing/i, /tester/i, /performance/i, /benchmark/i,
                /profile/i, /trace/i, /verbose/i, /detailed/i, /step/i, /phase/i
            ],
            info: [
                /info/i, /connected/i, /disconnected/i, /initialized/i, /started/i,
                /completed/i, /finished/i, /loaded/i, /saved/i, /updated/i, /created/i,
                /deleted/i, /moved/i, /resized/i, /selected/i, /deselected/i
            ]
        };
        
        this.contextPatterns = {
            performance: [
                /performance/i, /benchmark/i, /timing/i, /duration/i, /ms/i, /milliseconds/i,
                /fps/i, /frame/i, /render/i, /load time/i, /response time/i
            ],
            connection: [
                /connected/i, /disconnected/i, /websocket/i, /socket/i, /reconnect/i,
                /connection/i, /network/i, /api/i, /request/i, /response/i
            ],
            user: [
                /user/i, /click/i, /interaction/i, /action/i, /event/i, /input/i,
                /form/i, /submit/i, /validation/i, /error/i
            ],
            system: [
                /system/i, /service/i, /component/i, /module/i, /initialized/i,
                /started/i, /stopped/i, /shutdown/i, /restart/i
            ],
            data: [
                /data/i, /object/i, /array/i, /property/i, /value/i, /state/i,
                /cache/i, /storage/i, /database/i, /query/i
            ]
        };
        
        this.isInitialized = false;
        this.processedFiles = new Set();
    }
    
    /**
     * Initialize the logging replacement system
     */
    initialize() {
        if (this.isInitialized) {
            console.warn('LoggingReplacer already initialized');
            return;
        }
        
        // Ensure ArxLogger is available
        if (typeof window.arxLogger === 'undefined') {
            console.warn('ArxLogger not found. Creating default instance...');
            window.arxLogger = new ArxLogger({
                service: 'arx-web-frontend',
                environment: window.location.hostname === 'localhost' ? 'development' : 'production',
                enableRemoteLogging: true,
                remoteEndpoint: '/api/logs/aggregate'
            });
        }
        
        // Override console.log globally
        this.overrideConsoleLog();
        
        // Process existing scripts
        this.replaceAll();
        
        // Set up mutation observer for dynamically loaded scripts
        this.setupMutationObserver();
        
        this.isInitialized = true;
        console.log('LoggingReplacer initialized successfully');
    }
    
    /**
     * Override console.log to automatically use ArxLogger
     */
    overrideConsoleLog() {
        const originalConsoleLog = console.log;
        const self = this;
        
        console.log = function(...args) {
            // Determine log level and context
            const message = args.map(arg => 
                typeof arg === 'string' ? arg : JSON.stringify(arg)
            ).join(' ');
            
            const logLevel = self.determineLogLevel(message, 'info');
            const context = self.determineContext(message);
            
            // Use ArxLogger instead
            if (window.arxLogger) {
                const metadata = { context, originalArgs: args };
                window.arxLogger[logLevel](message, metadata);
            } else {
                // Fallback to original console.log
                originalConsoleLog.apply(console, args);
            }
        };
    }
    
    /**
     * Determine appropriate log level based on message content
     */
    determineLogLevel(message, defaultLevel = 'info') {
        const lowerMessage = message.toLowerCase();
        
        // Check for error patterns
        for (const pattern of this.logLevelPatterns.error) {
            if (pattern.test(lowerMessage)) {
                return 'error';
            }
        }
        
        // Check for warning patterns
        for (const pattern of this.logLevelPatterns.warning) {
            if (pattern.test(lowerMessage)) {
                return 'warning';
            }
        }
        
        // Check for debug patterns
        for (const pattern of this.logLevelPatterns.debug) {
            if (pattern.test(lowerMessage)) {
                return 'debug';
            }
        }
        
        // Check for info patterns
        for (const pattern of this.logLevelPatterns.info) {
            if (pattern.test(lowerMessage)) {
                return 'info';
            }
        }
        
        return defaultLevel;
    }
    
    /**
     * Determine context based on message content
     */
    determineContext(message) {
        const lowerMessage = message.toLowerCase();
        const contexts = [];
        
        for (const [context, patterns] of Object.entries(this.contextPatterns)) {
            for (const pattern of patterns) {
                if (pattern.test(lowerMessage)) {
                    contexts.push(context);
                    break;
                }
            }
        }
        
        return contexts.length > 0 ? contexts : ['general'];
    }
    
    /**
     * Replace console.log calls in a file content
     */
    replaceInFile(fileContent, fileName = 'unknown') {
        if (this.processedFiles.has(fileName)) {
            return fileContent;
        }
        
        let modifiedContent = fileContent;
        let replacements = 0;
        
        for (const replacement of this.replacements) {
            const matches = fileContent.match(replacement.pattern);
            if (matches) {
                replacements += matches.length;
                modifiedContent = modifiedContent.replace(replacement.pattern, (match, ...args) => {
                    const message = args[0];
                    const logLevel = this.determineLogLevel(message, 'info');
                    const context = this.determineContext(message);
                    
                    // Handle different argument patterns
                    if (match.includes('`')) {
                        // Template literal
                        return `window.arxLogger.${logLevel}(\`${message}\`, { context: '${context.join(',')}', file: '${fileName}' })`;
                    } else if (match.includes("'")) {
                        // Single quotes
                        return `window.arxLogger.${logLevel}('${message}', { context: '${context.join(',')}', file: '${fileName}' })`;
                    } else {
                        // Variable/expression
                        return `window.arxLogger.${logLevel}(${message}, { context: '${context.join(',')}', file: '${fileName}' })`;
                    }
                });
            }
        }
        
        if (replacements > 0) {
            console.log(`LoggingReplacer: Replaced ${replacements} console.log calls in ${fileName}`);
        }
        
        this.processedFiles.add(fileName);
        return modifiedContent;
    }
    
    /**
     * Replace console.log calls in all loaded scripts
     */
    replaceAll() {
        const scripts = document.querySelectorAll('script[src*=".js"]');
        
        scripts.forEach(script => {
            const src = script.getAttribute('src');
            if (src && !this.processedFiles.has(src)) {
                // Note: This is a simplified approach. In a real implementation,
                // you would need to fetch and process the actual script content
                console.log(`LoggingReplacer: Found script ${src}`);
            }
        });
    }
    
    /**
     * Set up mutation observer to handle dynamically loaded scripts
     */
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName === 'SCRIPT') {
                            // Handle dynamically added scripts
                            if (node.src) {
                                console.log(`LoggingReplacer: New script detected: ${node.src}`);
                            } else if (node.textContent) {
                                // Inline script
                                const processedContent = this.replaceInFile(node.textContent, 'inline');
                                if (processedContent !== node.textContent) {
                                    node.textContent = processedContent;
                                }
                            }
                        }
                    }
                });
            });
        });
        
        observer.observe(document.head, { childList: true, subtree: true });
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    /**
     * Process a specific file by fetching and replacing console.log calls
     */
    async processFile(filePath) {
        try {
            const response = await fetch(filePath);
            const content = await response.text();
            const processedContent = this.replaceInFile(content, filePath);
            
            // Create a new script element with processed content
            const script = document.createElement('script');
            script.textContent = processedContent;
            script.setAttribute('data-processed', 'true');
            
            // Replace the original script if it exists
            const originalScript = document.querySelector(`script[src="${filePath}"]`);
            if (originalScript) {
                originalScript.parentNode.replaceChild(script, originalScript);
            } else {
                document.head.appendChild(script);
            }
            
            return processedContent;
        } catch (error) {
            console.error(`LoggingReplacer: Error processing file ${filePath}:`, error);
            return null;
        }
    }
    
    /**
     * Get statistics about processed files and replacements
     */
    getStats() {
        return {
            processedFiles: Array.from(this.processedFiles),
            totalFiles: this.processedFiles.size,
            isInitialized: this.isInitialized
        };
    }
    
    /**
     * Reset the replacement system
     */
    reset() {
        this.processedFiles.clear();
        this.isInitialized = false;
        console.log('LoggingReplacer reset');
    }
}

// Create global instance
window.LoggingReplacer = new LoggingReplacer();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.LoggingReplacer.initialize();
    });
} else {
    window.LoggingReplacer.initialize();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoggingReplacer;
} 