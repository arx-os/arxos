/**
 * Import Module
 * Handles all import functionality including JSON, SVG, and backup imports
 */

export class Import {
    constructor(options = {}) {
        this.options = {
            enableJSONImport: true,
            enableSVGImport: true,
            enableBackupRestore: true,
            validateImports: true,
            maxFileSize: 50 * 1024 * 1024, // 50MB
            supportedFormats: ['json', 'svg', 'zip'],
            ...options
        };
        
        this.importQueue = [];
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
        // Listen for import requests
        document.addEventListener('importVersion', (event) => {
            this.handleImportRequest(event.detail);
        });
        
        // Listen for restore requests
        document.addEventListener('restoreFloor', (event) => {
            this.handleRestoreRequest(event.detail);
        });
        
        // Listen for file drops
        document.addEventListener('dragover', (event) => {
            event.preventDefault();
            this.handleDragOver(event);
        });
        
        document.addEventListener('drop', (event) => {
            event.preventDefault();
            this.handleFileDrop(event);
        });
    }

    // Import request handlers
    async handleImportRequest(details) {
        const { file, format, options = {} } = details;
        
        try {
            switch (format) {
                case 'json':
                    await this.importFromJSON(file, options);
                    break;
                case 'svg':
                    await this.importFromSVG(file, options);
                    break;
                default:
                    throw new Error(`Unsupported import format: ${format}`);
            }
        } catch (error) {
            console.error('Import failed:', error);
            this.triggerEvent('importFailed', { error, details });
        }
    }

    async handleRestoreRequest(details) {
        const { file, options = {} } = details;
        
        try {
            await this.restoreFromBackup(file, options);
        } catch (error) {
            console.error('Restore failed:', error);
            this.triggerEvent('restoreFailed', { error, details });
        }
    }

    // File drop handlers
    handleDragOver(event) {
        event.dataTransfer.dropEffect = 'copy';
    }

    handleFileDrop(event) {
        const files = Array.from(event.dataTransfer.files);
        
        files.forEach(file => {
            this.processDroppedFile(file);
        });
    }

    async processDroppedFile(file) {
        try {
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            switch (fileExtension) {
                case 'json':
                    await this.importFromJSON(file);
                    break;
                case 'svg':
                    await this.importFromSVG(file);
                    break;
                case 'zip':
                    await this.restoreFromBackup(file);
                    break;
                default:
                    throw new Error(`Unsupported file format: ${fileExtension}`);
            }
        } catch (error) {
            console.error('Error processing dropped file:', error);
            this.triggerEvent('fileProcessFailed', { file, error });
        }
    }

    // JSON Import
    async importFromJSON(file, options = {}) {
        this.startProgress('Importing JSON', 'Reading file...');
        
        try {
            // Validate file size
            if (file.size > this.options.maxFileSize) {
                throw new Error('File size exceeds maximum allowed size');
            }
            
            this.updateProgress(20, 'Parsing JSON data...');
            
            // Read and parse JSON
            const jsonContent = await this.readFileAsText(file);
            const importData = JSON.parse(jsonContent);
            
            this.updateProgress(40, 'Validating data...');
            
            // Validate import data
            if (this.options.validateImports) {
                this.validateImportData(importData);
            }
            
            this.updateProgress(60, 'Processing import...');
            
            // Process import data
            const result = await this.processImportData(importData, options);
            
            this.updateProgress(80, 'Applying changes...');
            
            // Apply changes to the system
            await this.applyImportChanges(result);
            
            this.completeProgress('Import completed successfully');
            this.triggerEvent('importCompleted', { 
                format: 'json', 
                file, 
                data: importData,
                result 
            });
            
        } catch (error) {
            this.failProgress('Import failed: ' + error.message);
            throw error;
        }
    }

    // SVG Import
    async importFromSVG(file, options = {}) {
        this.startProgress('Importing SVG', 'Reading file...');
        
        try {
            // Validate file size
            if (file.size > this.options.maxFileSize) {
                throw new Error('File size exceeds maximum allowed size');
            }
            
            this.updateProgress(20, 'Parsing SVG data...');
            
            // Read SVG content
            const svgContent = await this.readFileAsText(file);
            
            this.updateProgress(40, 'Extracting SVG data...');
            
            // Parse SVG data
            const svgData = this.parseSVGData(svgContent);
            
            this.updateProgress(60, 'Processing SVG...');
            
            // Process SVG data
            const result = await this.processSVGData(svgData, options);
            
            this.updateProgress(80, 'Applying changes...');
            
            // Apply changes to the system
            await this.applyImportChanges(result);
            
            this.completeProgress('SVG import completed successfully');
            this.triggerEvent('importCompleted', { 
                format: 'svg', 
                file, 
                data: svgData,
                result 
            });
            
        } catch (error) {
            this.failProgress('SVG import failed: ' + error.message);
            throw error;
        }
    }

    // Backup Restore
    async restoreFromBackup(file, options = {}) {
        this.startProgress('Restoring from Backup', 'Reading backup file...');
        
        try {
            // Validate file size
            if (file.size > this.options.maxFileSize) {
                throw new Error('File size exceeds maximum allowed size');
            }
            
            this.updateProgress(20, 'Reading backup data...');
            
            // Read backup file
            const backupData = await this.readBackupFile(file);
            
            this.updateProgress(40, 'Validating backup...');
            
            // Validate backup data
            if (this.options.validateImports) {
                this.validateBackup(backupData);
            }
            
            this.updateProgress(60, 'Preparing restore...');
            
            // Prepare restore data
            const restoreData = await this.prepareRestoreData(backupData, options);
            
            this.updateProgress(80, 'Performing restore...');
            
            // Perform restore
            const result = await this.performRestore(restoreData, options);
            
            this.completeProgress('Restore completed successfully');
            this.triggerEvent('restoreCompleted', { 
                file, 
                data: backupData,
                result 
            });
            
        } catch (error) {
            this.failProgress('Restore failed: ' + error.message);
            throw error;
        }
    }

    // File reading methods
    async readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (event) => resolve(event.target.result);
            reader.onerror = (error) => reject(error);
            reader.readAsText(file);
        });
    }

    async readBackupFile(file) {
        try {
            const content = await this.readFileAsText(file);
            return JSON.parse(content);
        } catch (error) {
            throw new Error('Invalid backup file format');
        }
    }

    // Data validation methods
    validateImportData(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid import data format');
        }
        
        if (!data.version && !data.floor) {
            throw new Error('Import data must contain version or floor information');
        }
        
        // Additional validation based on data type
        if (data.version) {
            this.validateVersionData(data.version);
        }
        
        if (data.floor) {
            this.validateFloorData(data.floor);
        }
    }

    validateVersionData(versionData) {
        if (!versionData.id) {
            throw new Error('Version data must contain an ID');
        }
        
        if (!versionData.objects && !Array.isArray(versionData.objects)) {
            throw new Error('Version data must contain objects array');
        }
    }

    validateFloorData(floorData) {
        if (!floorData.id) {
            throw new Error('Floor data must contain an ID');
        }
        
        if (!floorData.name) {
            throw new Error('Floor data must contain a name');
        }
    }

    validateBackup(backupData) {
        if (!backupData || typeof backupData !== 'object') {
            throw new Error('Invalid backup data format');
        }
        
        if (!backupData.type) {
            throw new Error('Backup data must specify type');
        }
        
        if (!['version_backup', 'floor_backup'].includes(backupData.type)) {
            throw new Error('Invalid backup type');
        }
        
        if (!backupData.backupInfo) {
            throw new Error('Backup data must contain backup information');
        }
    }

    // Data processing methods
    async processImportData(importData, options) {
        const { mergeMode = 'replace', conflictResolution = 'skip' } = options;
        
        // Process based on data type
        if (importData.version) {
            return await this.importVersion(importData.version, options);
        }
        
        if (importData.floor) {
            return await this.importFloor(importData.floor, options);
        }
        
        throw new Error('No valid import data found');
    }

    async processSVGData(svgData, options) {
        const { extractObjects = true, preserveStyles = true } = options;
        
        // Extract objects from SVG
        const objects = extractObjects ? this.extractObjectsFromSVG(svgData) : [];
        
        // Preserve styles if requested
        const styles = preserveStyles ? this.extractStylesFromSVG(svgData) : {};
        
        return {
            type: 'svg_import',
            objects: objects,
            styles: styles,
            svgData: svgData
        };
    }

    async prepareRestoreData(backupData, options) {
        const { restoreMode = 'full', conflictResolution = 'overwrite' } = options;
        
        // Prepare restore data based on backup type
        if (backupData.type === 'version_backup') {
            return await this.prepareVersionRestore(backupData, options);
        }
        
        if (backupData.type === 'floor_backup') {
            return await this.prepareFloorRestore(backupData, options);
        }
        
        throw new Error('Invalid backup type for restore');
    }

    async performRestore(restoreData, options) {
        const { restoreMode = 'full' } = options;
        
        try {
            // Perform the actual restore operation
            const result = await this.executeRestore(restoreData, options);
            
            // Update system state
            await this.updateSystemAfterRestore(result);
            
            return result;
        } catch (error) {
            throw new Error(`Restore failed: ${error.message}`);
        }
    }

    // Import execution methods
    async importVersion(data, options) {
        const { mergeMode = 'replace', conflictResolution = 'skip' } = options;
        
        try {
            // Send import request to backend
            const response = await fetch('/api/versions/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    versionData: data,
                    options: { mergeMode, conflictResolution }
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to import version');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error importing version:', error);
            throw error;
        }
    }

    async importFloor(data, options) {
        const { mergeMode = 'replace', conflictResolution = 'skip' } = options;
        
        try {
            // Send import request to backend
            const response = await fetch('/api/floors/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    floorData: data,
                    options: { mergeMode, conflictResolution }
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to import floor');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error importing floor:', error);
            throw error;
        }
    }

    // SVG processing methods
    parseSVGData(svgContent) {
        // Parse SVG content and extract relevant data
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
        
        // Extract SVG elements
        const svgElement = svgDoc.querySelector('svg');
        if (!svgElement) {
            throw new Error('No SVG element found in file');
        }
        
        // Extract objects and metadata
        const objects = this.extractObjectsFromSVG(svgElement);
        const metadata = this.extractMetadataFromSVG(svgElement);
        
        return {
            svgElement: svgElement,
            objects: objects,
            metadata: metadata,
            content: svgContent
        };
    }

    extractObjectsFromSVG(svgElement) {
        const objects = [];
        
        // Extract various SVG elements as objects
        const elements = svgElement.querySelectorAll('rect, circle, ellipse, line, polyline, polygon, path, text');
        
        elements.forEach((element, index) => {
            objects.push({
                id: element.id || `imported-object-${index}`,
                type: element.tagName.toLowerCase(),
                attributes: this.extractElementAttributes(element),
                content: element.outerHTML
            });
        });
        
        return objects;
    }

    extractStylesFromSVG(svgElement) {
        const styles = {};
        
        // Extract style definitions
        const styleElements = svgElement.querySelectorAll('style');
        styleElements.forEach(style => {
            styles[style.id || 'default'] = style.textContent;
        });
        
        return styles;
    }

    extractMetadataFromSVG(svgElement) {
        const metadata = {};
        
        // Extract data attributes
        for (let attr of svgElement.attributes) {
            if (attr.name.startsWith('data-')) {
                const key = attr.name.replace('data-', '');
                metadata[key] = attr.value;
            }
        }
        
        return metadata;
    }

    extractElementAttributes(element) {
        const attributes = {};
        
        for (let attr of element.attributes) {
            attributes[attr.name] = attr.value;
        }
        
        return attributes;
    }

    // Restore preparation methods
    async prepareVersionRestore(backupData, options) {
        const { restoreMode = 'full' } = options;
        
        return {
            type: 'version_restore',
            versionData: backupData.version,
            metadata: backupData.metadata,
            assets: backupData.assets,
            restoreMode: restoreMode
        };
    }

    async prepareFloorRestore(backupData, options) {
        const { restoreMode = 'full' } = options;
        
        return {
            type: 'floor_restore',
            floorData: backupData.floor,
            versions: backupData.versions,
            metadata: backupData.metadata,
            assets: backupData.assets,
            restoreMode: restoreMode
        };
    }

    // Restore execution methods
    async executeRestore(restoreData, options) {
        const { restoreMode = 'full' } = options;
        
        try {
            // Send restore request to backend
            const response = await fetch('/api/restore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    restoreData: restoreData,
                    options: { restoreMode }
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to execute restore');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error executing restore:', error);
            throw error;
        }
    }

    async updateSystemAfterRestore(result) {
        // Update UI and system state after restore
        this.triggerEvent('systemUpdated', { result });
    }

    async applyImportChanges(result) {
        // Apply changes to the current system state
        this.triggerEvent('changesApplied', { result });
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
                    handler({ ...data, import: this });
                } catch (error) {
                    console.error(`Error in import event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.importQueue = [];
        this.isProcessing = false;
        this.currentOperation = null;
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 