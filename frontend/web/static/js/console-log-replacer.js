/**
 * Console.log Replacement Utility
 *
 * This script provides a simple way to replace console.log calls with ArxLogger calls
 * in specific files. It's designed to be used as a reference for manual replacements.
 *
 * Usage:
 * 1. Open the target file
 * 2. Use the patterns below to replace console.log calls
 * 3. Test the changes
 */

const ConsoleLogReplacer = {
    /**
     * Replace patterns for different types of console.log calls
     */
    patterns: {
        // Simple string messages
        simpleString: {
            from: /console\.log\('([^']+)'\)/g,
            to: (match, message) => `window.arxLogger.info('${message}')`
        },

        // Template literal messages
        templateLiteral: {
            from: /console\.log\(`([^`]+)`\)/g,
            to: (match, message) => `window.arxLogger.info(\`${message}\`)`
        },

        // Variable/expression logging
        variable: {
            from: /console\.log\(([^)]+)\)/g,
            to: (match, expression) => `window.arxLogger.info(${expression})`
        },

        // Multi-argument console.log
        multiArg: {
            from: /console\.log\(([^)]+(?:,\s*[^)]+)*)\)/g,
            to: (match, args) => `window.arxLogger.info(${args})`
        }
    },

    /**
     * Smart replacement based on message content
     */
    smartReplace: function(content, fileName) {
        let modifiedContent = content;
        let replacements = 0;

        // Replace simple string messages
        modifiedContent = modifiedContent.replace(
            this.patterns.simpleString.from,
            (match, message) => {
                replacements++;
                const level = this.determineLogLevel(message);
                return `window.arxLogger.${level}('${message}', { file: '${fileName}' })`;
            }
        );

        // Replace template literal messages
        modifiedContent = modifiedContent.replace(
            this.patterns.templateLiteral.from,
            (match, message) => {
                replacements++;
                const level = this.determineLogLevel(message);
                return `window.arxLogger.${level}(\`${message}\`, { file: '${fileName}' })`;
            }
        );

        // Replace variable/expression logging
        modifiedContent = modifiedContent.replace(
            this.patterns.variable.from,
            (match, expression) => {
                replacements++;
                const level = this.determineLogLevel(expression);
                return `window.arxLogger.${level}(${expression}, { file: '${fileName}' })`;
            }
        );

        return { content: modifiedContent, replacements };
    },

    /**
     * Determine log level based on message content
     */
    determineLogLevel: function(message) {
        const lowerMessage = message.toLowerCase();

        // Error patterns
        if (/error|failed|failure|exception|crash|broken|invalid|missing|not found|unauthorized|forbidden|timeout|connection failed|network error/i.test(lowerMessage)) {
            return 'error';
        }

        // Warning patterns
        if (/warn|warning|deprecated|obsolete|slow|performance|retry|fallback|degraded|partial|incomplete/i.test(lowerMessage)) {
            return 'warning';
        }

        // Debug patterns
        if (/debug|test|testing|tester|performance|benchmark|profile|trace|verbose|detailed|step|phase/i.test(lowerMessage)) {
            return 'debug';
        }

        // Info patterns
        if (/info|connected|disconnected|initialized|started|completed|finished|loaded|saved|updated|created|deleted|moved|resized|selected|deselected/i.test(lowerMessage)) {
            return 'info';
        }

        return 'info'; // Default
    },

    /**
     * Get replacement examples for specific files
     */
    getFileExamples: function() {
        return {
            'realtime_manager.js': [
                {
                    from: "console.log('RealTimeManager initialized for user:', this.username);",
                    to: "window.arxLogger.info('RealTimeManager initialized for user:', this.username, { file: 'realtime_manager.js' });"
                },
                {
                    from: "console.log('WebSocket connected');",
                    to: "window.arxLogger.info('WebSocket connected', { file: 'realtime_manager.js' });"
                },
                {
                    from: "console.log('WebSocket disconnected');",
                    to: "window.arxLogger.warning('WebSocket disconnected', { file: 'realtime_manager.js' });"
                },
                {
                    from: "console.log('Received message:', message);",
                    to: "window.arxLogger.debug('Received message:', message, { file: 'realtime_manager.js' });"
                }
            ],

            'object_interaction.js': [
                {
                    from: "console.log('SVGObjectInteraction connected to ViewportManager');",
                    to: "window.arxLogger.info('SVGObjectInteraction connected to ViewportManager', { file: 'object_interaction.js' });"
                },
                {
                    from: "console.log('Object deleted successfully:', id);",
                    to: "window.arxLogger.info('Object deleted successfully:', id, { file: 'object_interaction.js' });"
                },
                {
                    from: "console.log('=== Testing Multi-Object Selection with Zoom ===');",
                    to: "window.arxLogger.debug('=== Testing Multi-Object Selection with Zoom ===', { file: 'object_interaction.js' });"
                }
            ],

            'viewport_manager.js': [
                {
                    from: "console.log(`ViewportCulling: ${visibleCount}/${this.totalObjects} objects visible (${culledCount} culled) in ${cullingTime.toFixed(2)}ms`);",
                    to: "window.arxLogger.debug(`ViewportCulling: ${visibleCount}/${this.totalObjects} objects visible (${culledCount} culled) in ${cullingTime.toFixed(2)}ms`, { file: 'viewport_manager.js' });"
                },
                {
                    from: "console.log('ViewportCulling: Enabled');",
                    to: "window.arxLogger.info('ViewportCulling: Enabled', { file: 'viewport_manager.js' });"
                }
            ],

            'lod_manager.js': [
                {
                    from: "console.log('LODManager initialized');",
                    to: "window.arxLogger.info('LODManager initialized', { file: 'lod_manager.js' });"
                },
                {
                    from: "console.log(`LODManager: Switching from ${this.currentLODLevel} to ${newLevel} at zoom ${zoomLevel}`);",
                    to: "window.arxLogger.info(`LODManager: Switching from ${this.currentLODLevel} to ${newLevel} at zoom ${zoomLevel}`, { file: 'lod_manager.js' });"
                }
            ],

            'throttled_update_manager.js': [
                {
                    from: "console.log('ThrottledUpdateManager initialized');",
                    to: "window.arxLogger.info('ThrottledUpdateManager initialized', { file: 'throttled_update_manager.js' });"
                }
            ],

            'bim_editing_integration.js': [
                {
                    from: "console.log('BIMEditingIntegration connected to ViewportManager');",
                    to: "window.arxLogger.info('BIMEditingIntegration connected to ViewportManager', { file: 'bim_editing_integration.js' });"
                },
                {
                    from: "console.log('Major edit detected:', edit);",
                    to: "window.arxLogger.info('Major edit detected:', edit, { file: 'bim_editing_integration.js' });"
                }
            ],

            'collaboration_system.js': [
                {
                    from: "console.log('CollaborationSystem initialized');",
                    to: "window.arxLogger.info('CollaborationSystem initialized', { file: 'collaboration_system.js' });"
                }
            ],

            'data_partitioning_manager.js': [
                {
                    from: "console.log('DataPartitioningManager initialized');",
                    to: "window.arxLogger.info('DataPartitioningManager initialized', { file: 'data_partitioning_manager.js' });"
                }
            ],

            'symbol_library.js': [
                {
                    from: "console.log('SymbolLibrary connected to ViewportManager');",
                    to: "window.arxLogger.info('SymbolLibrary connected to ViewportManager', { file: 'symbol_library.js' });"
                },
                {
                    from: "console.log(`Symbol placed at real-world coordinates: (${realWorldCoords.x.toFixed(2)}, ${realWorldCoords.y.toFixed(2)}) ${this.viewportManager.currentUnit}`);",
                    to: "window.arxLogger.info(`Symbol placed at real-world coordinates: (${realWorldCoords.x.toFixed(2)}, ${realWorldCoords.y.toFixed(2)}) ${this.viewportManager.currentUnit}`, { file: 'symbol_library.js' });"
                }
            ]
        };
    },

    /**
     * Generate a summary of replacements needed
     */
    getReplacementSummary: function() {
        const files = {
            'realtime_manager.js': 15,
            'object_interaction.js': 15,
            'viewport_manager.js': 12,
            'lod_manager.js': 8,
            'throttled_update_manager.js': 8,
            'bim_editing_integration.js': 4,
            'collaboration_system.js': 4,
            'data_partitioning_manager.js': 2,
            'symbol_library.js': 3
        };

        const total = Object.values(files).reduce((sum, count) => sum + count, 0);

        return {
            files,
            total,
            summary: `Total console.log calls to replace: ${total} across ${Object.keys(files).length} files`
        };
    }
};

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConsoleLogReplacer;
}

// Make available globally
window.ConsoleLogReplacer = ConsoleLogReplacer;

// Log summary on load
console.log('ConsoleLogReplacer loaded. Use ConsoleLogReplacer.getReplacementSummary() to see what needs to be replaced.');
