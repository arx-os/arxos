/**
 * Export/Import Manager
 * Orchestrates export, import, formats, and validation modules
 */

import { Export } from './export.js';
import { Import } from './import.js';
import { Formats } from './formats.js';
import { Validation } from './validation.js';

export class ExportImportManager {
    constructor(options = {}) {
        this.options = options;
        
        // Initialize modules
        this.export = new Export(options);
        this.import = new Import(options);
        this.formats = new Formats(options);
        this.validation = new Validation(options);
        
        // Connect modules
        this.connectModules();
        
        // UI state
        this.ui = null;
        this.progressModal = null;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createUI();
        this.createProgressModal();
    }

    connectModules() {
        // Connect export events
        this.export.addEventListener('exportCompleted', (data) => {
            this.triggerEvent('exportCompleted', data);
        });
        
        this.export.addEventListener('exportFailed', (data) => {
            this.triggerEvent('exportFailed', data);
        });
        
        this.export.addEventListener('backupCompleted', (data) => {
            this.triggerEvent('backupCompleted', data);
        });
        
        this.export.addEventListener('backupFailed', (data) => {
            this.triggerEvent('backupFailed', data);
        });
        
        // Connect import events
        this.import.addEventListener('importCompleted', (data) => {
            this.triggerEvent('importCompleted', data);
        });
        
        this.import.addEventListener('importFailed', (data) => {
            this.triggerEvent('importFailed', data);
        });
        
        this.import.addEventListener('restoreCompleted', (data) => {
            this.triggerEvent('restoreCompleted', data);
        });
        
        this.import.addEventListener('restoreFailed', (data) => {
            this.triggerEvent('restoreFailed', data);
        });
        
        // Connect progress events
        this.export.addEventListener('progressStarted', (data) => {
            this.showProgress(data.title, data.description);
        });
        
        this.export.addEventListener('progressUpdated', (data) => {
            this.updateProgress(data.progress, data.description);
        });
        
        this.export.addEventListener('progressCompleted', (data) => {
            this.completeProgress(data.message);
        });
        
        this.export.addEventListener('progressFailed', (data) => {
            this.failProgress(data.message);
        });
        
        this.import.addEventListener('progressStarted', (data) => {
            this.showProgress(data.title, data.description);
        });
        
        this.import.addEventListener('progressUpdated', (data) => {
            this.updateProgress(data.progress, data.description);
        });
        
        this.import.addEventListener('progressCompleted', (data) => {
            this.completeProgress(data.message);
        });
        
        this.import.addEventListener('progressFailed', (data) => {
            this.failProgress(data.message);
        });
    }

    setupEventListeners() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // File drop events
        document.addEventListener('dragover', (e) => this.handleDragOver(e));
        document.addEventListener('drop', (e) => this.handleFileDrop(e));
    }

    handleKeyDown(event) {
        // Global keyboard shortcuts
        switch (event.key) {
            case 'e':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.showExportImportPanel();
                }
                break;
            case 'i':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.showFileImportDialog();
                }
                break;
            case 'Escape':
                this.hideExportImportPanel();
                this.hideProgressModal();
                break;
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    }

    handleFileDrop(event) {
        event.preventDefault();
        
        const files = Array.from(event.dataTransfer.files);
        files.forEach(file => {
            this.processDroppedFile(file);
        });
    }

    async processDroppedFile(file) {
        try {
            // Validate file
            this.validation.validateFile(file);
            
            // Detect format
            const format = this.formats.detectFormat(file);
            if (!format) {
                throw new Error('Unable to detect file format');
            }
            
            // Process based on format
            switch (format) {
                case 'json':
                    await this.import.importFromJSON(file);
                    break;
                case 'svg':
                    await this.import.importFromSVG(file);
                    break;
                case 'zip':
                    await this.import.restoreFromBackup(file);
                    break;
                default:
                    throw new Error(`Unsupported file format: ${format}`);
            }
        } catch (error) {
            console.error('Error processing dropped file:', error);
            this.triggerEvent('fileProcessFailed', { file, error });
        }
    }

    // UI methods
    createUI() {
        this.ui = document.createElement('div');
        this.ui.id = 'export-import-panel';
        this.ui.className = 'fixed top-4 left-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-50 max-w-sm';
        this.ui.style.display = 'none';
        
        this.ui.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-gray-900">Export/Import</h3>
                <button id="close-export-import-panel" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="space-y-4">
                <div>
                    <h4 class="font-medium text-gray-700 mb-2">Export</h4>
                    <div class="space-y-2">
                        <button id="export-json" class="w-full bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 text-sm">
                            <i class="fas fa-download mr-2"></i>Export as JSON
                        </button>
                        <button id="export-svg" class="w-full bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 text-sm">
                            <i class="fas fa-image mr-2"></i>Export as SVG
                        </button>
                        <button id="export-backup" class="w-full bg-purple-600 text-white px-3 py-2 rounded-md hover:bg-purple-700 text-sm">
                            <i class="fas fa-archive mr-2"></i>Create Backup
                        </button>
                    </div>
                </div>
                <div>
                    <h4 class="font-medium text-gray-700 mb-2">Import</h4>
                    <div class="space-y-2">
                        <button id="import-file" class="w-full bg-orange-600 text-white px-3 py-2 rounded-md hover:bg-orange-700 text-sm">
                            <i class="fas fa-upload mr-2"></i>Import File
                        </button>
                        <button id="restore-backup" class="w-full bg-red-600 text-white px-3 py-2 rounded-md hover:bg-red-700 text-sm">
                            <i class="fas fa-undo mr-2"></i>Restore Backup
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.ui);
        this.setupUIEventListeners();
    }

    setupUIEventListeners() {
        // Close button
        const closeButton = this.ui.querySelector('#close-export-import-panel');
        closeButton.addEventListener('click', () => {
            this.hideExportImportPanel();
        });
        
        // Export buttons
        const exportJsonButton = this.ui.querySelector('#export-json');
        exportJsonButton.addEventListener('click', () => {
            this.exportAsJSON();
        });
        
        const exportSvgButton = this.ui.querySelector('#export-svg');
        exportSvgButton.addEventListener('click', () => {
            this.exportAsSVG();
        });
        
        const exportBackupButton = this.ui.querySelector('#export-backup');
        exportBackupButton.addEventListener('click', () => {
            this.createBackup();
        });
        
        // Import buttons
        const importFileButton = this.ui.querySelector('#import-file');
        importFileButton.addEventListener('click', () => {
            this.showFileImportDialog();
        });
        
        const restoreBackupButton = this.ui.querySelector('#restore-backup');
        restoreBackupButton.addEventListener('click', () => {
            this.showBackupRestoreDialog();
        });
    }

    createProgressModal() {
        this.progressModal = document.createElement('div');
        this.progressModal.id = 'progress-modal';
        this.progressModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.progressModal.style.display = 'none';
        
        this.progressModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 id="progress-title" class="font-semibold text-gray-900">Processing...</h3>
                    <button id="cancel-progress" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="mb-4">
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div id="progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                </div>
                <p id="progress-description" class="text-sm text-gray-600">Initializing...</p>
            </div>
        `;
        
        document.body.appendChild(this.progressModal);
        
        // Cancel button
        const cancelButton = this.progressModal.querySelector('#cancel-progress');
        cancelButton.addEventListener('click', () => {
            this.cancelCurrentOperation();
        });
    }

    // UI control methods
    showExportImportPanel() {
        if (this.ui) {
            this.ui.style.display = 'block';
        }
    }

    hideExportImportPanel() {
        if (this.ui) {
            this.ui.style.display = 'none';
        }
    }

    showProgress(title, description) {
        if (this.progressModal) {
            this.progressModal.style.display = 'flex';
            
            const titleElement = this.progressModal.querySelector('#progress-title');
            const descriptionElement = this.progressModal.querySelector('#progress-description');
            
            if (titleElement) titleElement.textContent = title;
            if (descriptionElement) descriptionElement.textContent = description;
        }
    }

    updateProgress(progress, description = null) {
        if (this.progressModal) {
            const progressBar = this.progressModal.querySelector('#progress-bar');
            const descriptionElement = this.progressModal.querySelector('#progress-description');
            
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            
            if (descriptionElement && description) {
                descriptionElement.textContent = description;
            }
        }
    }

    completeProgress(message) {
        if (this.progressModal) {
            const descriptionElement = this.progressModal.querySelector('#progress-description');
            if (descriptionElement) {
                descriptionElement.textContent = message;
            }
            
            // Hide after delay
            setTimeout(() => {
                this.hideProgressModal();
            }, 2000);
        }
    }

    failProgress(message) {
        if (this.progressModal) {
            const descriptionElement = this.progressModal.querySelector('#progress-description');
            if (descriptionElement) {
                descriptionElement.textContent = `Error: ${message}`;
                descriptionElement.className = 'text-sm text-red-600';
            }
            
            // Hide after delay
            setTimeout(() => {
                this.hideProgressModal();
            }, 3000);
        }
    }

    hideProgressModal() {
        if (this.progressModal) {
            this.progressModal.style.display = 'none';
            
            // Reset progress bar
            const progressBar = this.progressModal.querySelector('#progress-bar');
            if (progressBar) {
                progressBar.style.width = '0%';
            }
            
            // Reset description
            const descriptionElement = this.progressModal.querySelector('#progress-description');
            if (descriptionElement) {
                descriptionElement.textContent = 'Initializing...';
                descriptionElement.className = 'text-sm text-gray-600';
            }
        }
    }

    // Operation methods
    async exportAsJSON() {
        try {
            const currentVersion = this.getCurrentVersion();
            if (!currentVersion) {
                throw new Error('No current version available');
            }
            
            await this.export.exportVersionAsJSON(currentVersion.id);
        } catch (error) {
            console.error('JSON export failed:', error);
            this.triggerEvent('exportFailed', { error, format: 'json' });
        }
    }

    async exportAsSVG() {
        try {
            const currentVersion = this.getCurrentVersion();
            if (!currentVersion) {
                throw new Error('No current version available');
            }
            
            await this.export.exportVersionAsSVG(currentVersion.id);
        } catch (error) {
            console.error('SVG export failed:', error);
            this.triggerEvent('exportFailed', { error, format: 'svg' });
        }
    }

    async createBackup() {
        try {
            const currentFloor = this.getCurrentFloor();
            if (!currentFloor) {
                throw new Error('No current floor available');
            }
            
            await this.export.createFloorBackup(currentFloor.id);
        } catch (error) {
            console.error('Backup creation failed:', error);
            this.triggerEvent('backupFailed', { error });
        }
    }

    showFileImportDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json,.svg,.zip';
        input.multiple = false;
        
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                this.processDroppedFile(file);
            }
        });
        
        input.click();
    }

    showBackupRestoreDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.zip';
        input.multiple = false;
        
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                this.import.restoreFromBackup(file);
            }
        });
        
        input.click();
    }

    cancelCurrentOperation() {
        // Cancel current operations
        this.export.cancelCurrentOperation();
        this.import.cancelCurrentOperation();
        
        this.hideProgressModal();
        this.triggerEvent('operationCancelled');
    }

    // Utility methods
    getCurrentVersion() {
        // Get current version from global state
        return window.currentVersion || null;
    }

    getCurrentFloor() {
        // Get current floor from global state
        return window.currentFloor || null;
    }

    // Module access methods
    getExport() {
        return this.export;
    }

    getImport() {
        return this.import;
    }

    getFormats() {
        return this.formats;
    }

    getValidation() {
        return this.validation;
    }

    // Public API methods
    async exportVersion(versionId, format, options = {}) {
        try {
            switch (format) {
                case 'json':
                    return await this.export.exportVersionAsJSON(versionId, options.includeMetadata, options.includeHistory);
                case 'svg':
                    return await this.export.exportVersionAsSVG(versionId, options.includeMetadata);
                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }
        } catch (error) {
            console.error('Export failed:', error);
            throw error;
        }
    }

    async importFile(file, options = {}) {
        try {
            // Validate file
            this.validation.validateFile(file);
            
            // Detect format
            const format = this.formats.detectFormat(file);
            if (!format) {
                throw new Error('Unable to detect file format');
            }
            
            // Import based on format
            switch (format) {
                case 'json':
                    return await this.import.importFromJSON(file, options);
                case 'svg':
                    return await this.import.importFromSVG(file, options);
                case 'zip':
                    return await this.import.restoreFromBackup(file, options);
                default:
                    throw new Error(`Unsupported import format: ${format}`);
            }
        } catch (error) {
            console.error('Import failed:', error);
            throw error;
        }
    }

    async convertFormat(fromFormat, toFormat, data, options = {}) {
        try {
            return await this.formats.convertFormat(fromFormat, toFormat, data, options);
        } catch (error) {
            console.error('Format conversion failed:', error);
            throw error;
        }
    }

    validateData(data, type, options = {}) {
        try {
            switch (type) {
                case 'import':
                    return this.validation.validateImportData(data, options);
                case 'export':
                    return this.validation.validateExportData(data, options);
                case 'backup':
                    return this.validation.validateBackup(data, options);
                default:
                    throw new Error(`Unknown validation type: ${type}`);
            }
        } catch (error) {
            console.error('Validation failed:', error);
            throw error;
        }
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
                    handler({ ...data, manager: this });
                } catch (error) {
                    console.error(`Error in export/import manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // Destroy modules
        if (this.export) {
            this.export.destroy();
        }
        if (this.import) {
            this.import.destroy();
        }
        if (this.formats) {
            this.formats.destroy();
        }
        if (this.validation) {
            this.validation.destroy();
        }
        
        // Remove UI elements
        if (this.ui) {
            this.ui.remove();
        }
        if (this.progressModal) {
            this.progressModal.remove();
        }
        
        // Clear event handlers
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 