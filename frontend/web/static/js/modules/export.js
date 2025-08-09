/**
 * Export Module
 * Handles all export functionality including JSON, SVG, and backup exports
 */

export class Export {
    constructor(options = {}) {
        this.options = {
            enableJSONExport: true,
            enableSVGExport: true,
            enableBackupRestore: true,
            compressionEnabled: true,
            includeMetadata: true,
            includeHistory: true,
            maxFileSize: 50 * 1024 * 1024, // 50MB
            supportedFormats: ['json', 'svg', 'zip'],
            ...options
        };

        this.exportQueue = [];
        this.isProcessing = false;
        this.currentOperation = null;

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for export requests
        document.addEventListener('exportVersion', (event) => {
            this.handleExportRequest(event.detail);
        });

        // Listen for backup requests
        document.addEventListener('backupFloor', (event) => {
            this.handleBackupRequest(event.detail);
        });
    }

    // Export request handlers
    async handleExportRequest(details) {
        const { versionId, format, includeMetadata = true, includeHistory = true } = details;

        try {
            switch (format) {
                case 'json':
                    await this.exportVersionAsJSON(versionId, includeMetadata, includeHistory);
                    break;
                case 'svg':
                    await this.exportVersionAsSVG(versionId, includeMetadata);
                    break;
                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.triggerEvent('exportFailed', { error, details });
        }
    }

    async handleBackupRequest(details) {
        const { floorId, includeAllVersions = true, includeMetadata = true } = details;

        try {
            await this.createFloorBackup(floorId, includeAllVersions, includeMetadata);
        } catch (error) {
            console.error('Backup failed:', error);
            this.triggerEvent('backupFailed', { error, details });
        }
    }

    // JSON Export
    async exportVersionAsJSON(versionId, includeMetadata = true, includeHistory = true) {
        this.startProgress('Exporting JSON', 'Preparing version data...');

        try {
            // Get version data
            const versionData = await this.getVersionData(versionId);
            const exportData = {
                version: versionData,
                exportInfo: {
                    timestamp: new Date().toISOString(),
                    format: 'json',
                    version: '1.0'
                }
            };

            // Include metadata if requested
            if (includeMetadata) {
                exportData.metadata = await this.getVersionMetadata(versionId);
            }

            // Include history if requested
            if (includeHistory) {
                exportData.history = await this.getVersionHistory(versionId);
            }

            this.updateProgress(50, 'Compressing data...');

            // Compress data if enabled
            let finalData = exportData;
            if (this.options.compressionEnabled) {
                finalData = await this.compressData(exportData);
            }

            this.updateProgress(75, 'Creating download...');

            // Create and trigger download
            const blob = new Blob([JSON.stringify(finalData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `version_${versionId}_${Date.now()}.json`;
            a.click();

            URL.revokeObjectURL(url);

            this.completeProgress('Export completed successfully');
            this.triggerEvent('exportCompleted', {
                format: 'json',
                versionId,
                data: exportData
            });

        } catch (error) {
            this.failProgress('Export failed: ' + error.message);
            throw error;
        }
    }

    // SVG Export
    async exportVersionAsSVG(versionId, includeMetadata = true) {
        this.startProgress('Exporting SVG', 'Preparing SVG data...');

        try {
            // Get SVG data
            const svgData = await this.getVersionSVGData(versionId);

            this.updateProgress(30, 'Creating SVG document...');

            // Create SVG document
            const svgDocument = this.createSVGDocument(svgData, includeMetadata);

            this.updateProgress(60, 'Optimizing SVG...');

            // Optimize SVG
            const optimizedSVG = await this.optimizeSVG(svgDocument);

            this.updateProgress(80, 'Creating download...');

            // Create and trigger download
            const blob = new Blob([optimizedSVG], {
                type: 'image/svg+xml'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `version_${versionId}_${Date.now()}.svg`;
            a.click();

            URL.revokeObjectURL(url);

            this.completeProgress('SVG export completed successfully');
            this.triggerEvent('exportCompleted', {
                format: 'svg',
                versionId,
                data: svgData
            });

        } catch (error) {
            this.failProgress('SVG export failed: ' + error.message);
            throw error;
        }
    }

    // Backup Export
    async createVersionBackup(versionId) {
        this.startProgress('Creating Backup', 'Collecting version data...');

        try {
            const versionData = await this.getVersionData(versionId);
            const metadata = await this.getVersionMetadata(versionId);
            const assets = await this.collectVersionAssets(versionId);

            this.updateProgress(40, 'Preparing backup...');

            const backupData = {
                type: 'version_backup',
                version: versionData,
                metadata: metadata,
                assets: assets,
                backupInfo: {
                    timestamp: new Date().toISOString(),
                    versionId: versionId,
                    format: 'backup'
                }
            };

            this.updateProgress(70, 'Compressing backup...');

            // Compress backup
            const compressedBackup = await this.compressBackup(backupData);

            this.updateProgress(90, 'Creating download...');

            // Create and trigger download
            const blob = new Blob([compressedBackup], {
                type: 'application/zip'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backup_version_${versionId}_${Date.now()}.zip`;
            a.click();

            URL.revokeObjectURL(url);

            this.completeProgress('Backup created successfully');
            this.triggerEvent('backupCompleted', {
                type: 'version',
                versionId,
                data: backupData
            });

        } catch (error) {
            this.failProgress('Backup failed: ' + error.message);
            throw error;
        }
    }

    async createFloorBackup(floorId, includeAllVersions = true, includeMetadata = true) {
        this.startProgress('Creating Floor Backup', 'Collecting floor data...');

        try {
            const floorData = await this.getFloorData(floorId);
            const versions = includeAllVersions ? await this.getFloorVersions(floorId) : [];
            const metadata = includeMetadata ? await this.getFloorMetadata(floorId) : {};
            const assets = await this.collectFloorAssets(floorId);

            this.updateProgress(40, 'Preparing backup...');

            const backupData = {
                type: 'floor_backup',
                floor: floorData,
                versions: versions,
                metadata: metadata,
                assets: assets,
                backupInfo: {
                    timestamp: new Date().toISOString(),
                    floorId: floorId,
                    format: 'backup',
                    includeAllVersions: includeAllVersions
                }
            };

            this.updateProgress(70, 'Compressing backup...');

            // Compress backup
            const compressedBackup = await this.compressBackup(backupData);

            this.updateProgress(90, 'Creating download...');

            // Create and trigger download
            const blob = new Blob([compressedBackup], {
                type: 'application/zip'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backup_floor_${floorId}_${Date.now()}.zip`;
            a.click();

            URL.revokeObjectURL(url);

            this.completeProgress('Floor backup created successfully');
            this.triggerEvent('backupCompleted', {
                type: 'floor',
                floorId,
                data: backupData
            });

        } catch (error) {
            this.failProgress('Floor backup failed: ' + error.message);
            throw error;
        }
    }

    // Data retrieval methods
    async getVersionData(versionId) {
        try {
            const response = await fetch(`/api/versions/${versionId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch version data');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching version data:', error);
            throw error;
        }
    }

    async getVersionMetadata(versionId) {
        try {
            const response = await fetch(`/api/versions/${versionId}/metadata`);
            if (!response.ok) {
                throw new Error('Failed to fetch version metadata');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching version metadata:', error);
            throw error;
        }
    }

    async getVersionHistory(versionId) {
        try {
            const response = await fetch(`/api/versions/${versionId}/history`);
            if (!response.ok) {
                throw new Error('Failed to fetch version history');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching version history:', error);
            throw error;
        }
    }

    async getVersionSVGData(versionId) {
        try {
            const response = await fetch(`/api/versions/${versionId}/svg`);
            if (!response.ok) {
                throw new Error('Failed to fetch SVG data');
            }
            return await response.text();
        } catch (error) {
            console.error('Error fetching SVG data:', error);
            throw error;
        }
    }

    async getFloorData(floorId) {
        try {
            const response = await fetch(`/api/floors/${floorId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch floor data');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching floor data:', error);
            throw error;
        }
    }

    async getFloorVersions(floorId) {
        try {
            const response = await fetch(`/api/floors/${floorId}/versions`);
            if (!response.ok) {
                throw new Error('Failed to fetch floor versions');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching floor versions:', error);
            throw error;
        }
    }

    async getFloorMetadata(floorId) {
        try {
            const response = await fetch(`/api/floors/${floorId}/metadata`);
            if (!response.ok) {
                throw new Error('Failed to fetch floor metadata');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching floor metadata:', error);
            throw error;
        }
    }

    // Asset collection methods
    async collectVersionAssets(versionId) {
        try {
            const response = await fetch(`/api/versions/${versionId}/assets`);
            if (!response.ok) {
                throw new Error('Failed to fetch version assets');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching version assets:', error);
            return [];
        }
    }

    async collectFloorAssets(floorId) {
        try {
            const response = await fetch(`/api/floors/${floorId}/assets`);
            if (!response.ok) {
                throw new Error('Failed to fetch floor assets');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching floor assets:', error);
            return [];
        }
    }

    // Compression methods
    async compressData(data) {
        // Simple compression - in production, use a proper compression library
        return JSON.stringify(data);
    }

    async compressBackup(backupData) {
        // Simple compression - in production, use a proper compression library
        return JSON.stringify(backupData);
    }

    // SVG methods
    createSVGDocument(svgData, includeMetadata) {
        let svgContent = svgData;

        if (includeMetadata) {
            const metadata = this.createSVGMetadata({
                timestamp: new Date().toISOString(),
                creator: this.getCurrentUser(),
                version: '1.0'
            });

            // Insert metadata into SVG
            svgContent = svgContent.replace('<svg', `<svg ${metadata}`);
        }

        return svgContent;
    }

    createSVGMetadata(metadata) {
        const metadataStr = Object.entries(metadata)
            .map(([key, value]) => `data-${key}="${value}"`)
            .join(' ');

        return metadataStr;
    }

    async optimizeSVG(svgDocument) {
        // Simple SVG optimization - in production, use a proper SVG optimizer
        return svgDocument
            .replace(/\s+/g, ' ')
            .replace(/>\s+</g, '><')
            .trim();
    }

    // Utility methods
    getCurrentUser() {
        // Get current user from global state or session
        return window.currentUser || 'unknown';
    }

    // Progress tracking methods
    startProgress(title, description) {
        this.triggerEvent('progressStarted', { title, description });
    }

    updateProgress(progress, description = null) {
        this.triggerEvent('progressUpdated', { progress, description });
    }

    completeProgress(message) {
        this.triggerEvent('progressCompleted', { message });
    }

    failProgress(message) {
        this.triggerEvent('progressFailed', { message });
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, export: this });
                } catch (error) {
                    console.error(`Error in export event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.exportQueue = [];
        this.isProcessing = false;
        this.currentOperation = null;

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
