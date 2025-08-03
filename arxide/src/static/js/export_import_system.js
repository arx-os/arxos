// Export/Import System for Floor Version Control
class ExportImportSystem {
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
        this.importQueue = [];
        this.isProcessing = false;
        this.currentOperation = null;
        
        // Use shared utilities
        this.utils = window.sharedUtilities || new SharedUtilities();
        
        this.initializeSystem();
    }

    // Initialize the export/import system
    initializeSystem() {
        this.setupEventListeners();
        this.initializeUI();
    }

    // Setup event listeners
    setupEventListeners() {
        // Listen for export requests
        document.addEventListener('exportVersion', (event) => {
            this.handleExportRequest(event.detail);
        });
        
        // Listen for import requests
        document.addEventListener('importVersion', (event) => {
            this.handleImportRequest(event.detail);
        });
        
        // Listen for backup requests
        document.addEventListener('backupFloor', (event) => {
            this.handleBackupRequest(event.detail);
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

    // Initialize UI elements
    initializeUI() {
        this.createExportImportUI();
    }

    // Create export/import UI
    createExportImportUI() {
        // Create export/import panel
        const panel = document.createElement('div');
        panel.id = 'export-import-panel';
        panel.className = 'fixed top-4 left-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-50 max-w-sm';
        panel.style.display = 'none';
        panel.innerHTML = `
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
                <div class="border-t pt-4">
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
                <div class="border-t pt-4">
                    <h4 class="font-medium text-gray-700 mb-2">Drop Zone</h4>
                    <div id="drop-zone" class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center text-gray-500 hover:border-blue-400 transition-colors">
                        <i class="fas fa-cloud-upload-alt text-2xl mb-2"></i>
                        <p>Drop files here to import</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // Create progress modal
        const progressModal = document.createElement('div');
        progressModal.id = 'export-import-progress-modal';
        progressModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        progressModal.style.display = 'none';
        progressModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="text-center">
                    <div id="progress-icon" class="text-3xl mb-4">
                        <i class="fas fa-spinner fa-spin text-blue-500"></i>
                    </div>
                    <h3 id="progress-title" class="text-lg font-semibold text-gray-900 mb-2">Processing...</h3>
                    <p id="progress-description" class="text-gray-600 mb-4">Please wait while we process your request.</p>
                    <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
                        <div id="progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <div id="progress-details" class="text-sm text-gray-500"></div>
                    <button id="cancel-operation" class="mt-4 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(progressModal);
        
        // Setup event listeners
        this.setupUIEventListeners();
    }

    // Setup UI event listeners
    setupUIEventListeners() {
        // Close panel
        document.getElementById('close-export-import-panel')?.addEventListener('click', () => {
            this.hideExportImportPanel();
        });
        
        // Export buttons
        document.getElementById('export-json')?.addEventListener('click', () => {
            this.exportAsJSON();
        });
        
        document.getElementById('export-svg')?.addEventListener('click', () => {
            this.exportAsSVG();
        });
        
        document.getElementById('export-backup')?.addEventListener('click', () => {
            this.createBackup();
        });
        
        // Import buttons
        document.getElementById('import-file')?.addEventListener('click', () => {
            this.showFileImportDialog();
        });
        
        document.getElementById('restore-backup')?.addEventListener('click', () => {
            this.showBackupRestoreDialog();
        });
        
        // Cancel operation
        document.getElementById('cancel-operation')?.addEventListener('click', () => {
            this.cancelCurrentOperation();
        });
        
        // Drop zone events
        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-blue-400', 'bg-blue-50');
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-blue-400', 'bg-blue-50');
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-blue-400', 'bg-blue-50');
                this.handleFileDrop(e);
            });
        }
    }

    // Handle export request
    async handleExportRequest(details) {
        const { format, versionId, includeMetadata, includeHistory } = details;
        
        try {
            switch (format) {
                case 'json':
                    await this.exportVersionAsJSON(versionId, includeMetadata, includeHistory);
                    break;
                case 'svg':
                    await this.exportVersionAsSVG(versionId, includeMetadata);
                    break;
                case 'backup':
                    await this.createVersionBackup(versionId);
                    break;
                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }
        } catch (error) {
            console.error('Export request failed:', error);
            this.showNotification('Export failed: ' + error.message, 'error');
        }
    }

    // Handle import request
    async handleImportRequest(details) {
        const { file, format, options } = details;
        
        try {
            switch (format) {
                case 'json':
                    await this.importFromJSON(file, options);
                    break;
                case 'svg':
                    await this.importFromSVG(file, options);
                    break;
                case 'backup':
                    await this.restoreFromBackup(file, options);
                    break;
                default:
                    throw new Error(`Unsupported import format: ${format}`);
            }
        } catch (error) {
            console.error('Import request failed:', error);
            this.showNotification('Import failed: ' + error.message, 'error');
        }
    }

    // Handle backup request
    async handleBackupRequest(details) {
        const { floorId, includeAllVersions, includeMetadata } = details;
        
        try {
            await this.createFloorBackup(floorId, includeAllVersions, includeMetadata);
        } catch (error) {
            console.error('Backup request failed:', error);
            this.showNotification('Backup failed: ' + error.message, 'error');
        }
    }

    // Handle restore request
    async handleRestoreRequest(details) {
        const { backupFile, options } = details;
        
        try {
            await this.restoreFloorFromBackup(backupFile, options);
        } catch (error) {
            console.error('Restore request failed:', error);
            this.showNotification('Restore failed: ' + error.message, 'error');
        }
    }

    // Handle drag over
    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    }

    // Handle file drop
    handleFileDrop(event) {
        const files = Array.from(event.dataTransfer.files);
        
        if (files.length === 0) return;
        
        // Process each file
        files.forEach(file => {
            this.processDroppedFile(file);
        });
    }

    // Process dropped file
    async processDroppedFile(file) {
        try {
            const fileExtension = this.utils.getFileExtension(file.name);
            
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
                    this.utils.showNotification(`Unsupported file type: ${fileExtension}`, 'warning');
            }
        } catch (error) {
            console.error('Error processing dropped file:', error);
            this.utils.showNotification('Failed to process file: ' + error.message, 'error');
        }
    }

    // Export version as JSON
    async exportVersionAsJSON(versionId, includeMetadata = true, includeHistory = true) {
        this.startProgress('Exporting as JSON', 'Preparing version data...');
        
        try {
            // Get version data
            const versionData = await this.getVersionData(versionId);
            
            this.updateProgress(25, 'Processing version data...');
            
            // Prepare export data
            const exportData = {
                format: 'json',
                version: '1.0',
                exported_at: new Date().toISOString(),
                exported_by: this.getCurrentUser(),
                version_data: versionData
            };
            
            if (includeMetadata) {
                exportData.metadata = await this.getVersionMetadata(versionId);
            }
            
            if (includeHistory) {
                exportData.history = await this.getVersionHistory(versionId);
            }
            
            this.updateProgress(50, 'Compressing data...');
            
            // Compress if enabled
            let finalData = exportData;
            if (this.options.compressionEnabled) {
                finalData = await this.compressData(exportData);
            }
            
            this.updateProgress(75, 'Generating file...');
            
            // Create and download file
            const fileName = `version_${versionId}_${new Date().toISOString().split('T')[0]}.json`;
            await this.utils.downloadJSON(finalData, fileName);
            
            this.completeProgress('Export completed successfully');
            this.utils.showNotification('Version exported as JSON successfully', 'success');
            
        } catch (error) {
            this.failProgress('Export failed: ' + error.message);
            throw error;
        }
    }

    // Export version as SVG
    async exportVersionAsSVG(versionId, includeMetadata = true) {
        this.startProgress('Exporting as SVG', 'Preparing SVG data...');
        
        try {
            // Get version SVG data
            const svgData = await this.getVersionSVGData(versionId);
            
            this.updateProgress(25, 'Processing SVG elements...');
            
            // Prepare SVG document
            const svgDocument = this.createSVGDocument(svgData, includeMetadata);
            
            this.updateProgress(50, 'Optimizing SVG...');
            
            // Optimize SVG
            const optimizedSVG = await this.optimizeSVG(svgDocument);
            
            this.updateProgress(75, 'Generating file...');
            
            // Create and download file
            const fileName = `version_${versionId}_${new Date().toISOString().split('T')[0]}.svg`;
            await this.utils.downloadSVG(optimizedSVG, fileName);
            
            this.completeProgress('Export completed successfully');
            this.utils.showNotification('Version exported as SVG successfully', 'success');
            
        } catch (error) {
            this.failProgress('Export failed: ' + error.message);
            throw error;
        }
    }

    // Create version backup
    async createVersionBackup(versionId) {
        this.startProgress('Creating Backup', 'Preparing backup data...');
        
        try {
            // Get complete version data
            const versionData = await this.getVersionData(versionId);
            const metadata = await this.getVersionMetadata(versionId);
            const history = await this.getVersionHistory(versionId);
            
            this.updateProgress(25, 'Collecting assets...');
            
            // Collect all assets
            const assets = await this.collectVersionAssets(versionId);
            
            this.updateProgress(50, 'Creating backup package...');
            
            // Create backup package
            const backupPackage = {
                type: 'version_backup',
                version: '1.0',
                created_at: new Date().toISOString(),
                created_by: this.getCurrentUser(),
                version_data: versionData,
                metadata: metadata,
                history: history,
                assets: assets
            };
            
            this.updateProgress(75, 'Compressing backup...');
            
            // Compress backup
            const compressedBackup = await this.compressBackup(backupPackage);
            
            this.updateProgress(90, 'Generating backup file...');
            
            // Create and download backup file
            const fileName = `backup_version_${versionId}_${new Date().toISOString().split('T')[0]}.zip`;
            await this.utils.downloadZIP(compressedBackup, fileName);
            
            this.completeProgress('Backup created successfully');
            this.utils.showNotification('Version backup created successfully', 'success');
            
        } catch (error) {
            this.failProgress('Backup failed: ' + error.message);
            throw error;
        }
    }

    // Create floor backup
    async createFloorBackup(floorId, includeAllVersions = true, includeMetadata = true) {
        this.startProgress('Creating Floor Backup', 'Preparing floor data...');
        
        try {
            // Get floor data
            const floorData = await this.getFloorData(floorId);
            
            this.updateProgress(20, 'Collecting versions...');
            
            // Get all versions if requested
            let versions = [];
            if (includeAllVersions) {
                versions = await this.getFloorVersions(floorId);
            }
            
            this.updateProgress(40, 'Collecting assets...');
            
            // Collect all floor assets
            const assets = await this.collectFloorAssets(floorId);
            
            this.updateProgress(60, 'Creating backup package...');
            
            // Create backup package
            const backupPackage = {
                type: 'floor_backup',
                version: '1.0',
                created_at: new Date().toISOString(),
                created_by: this.getCurrentUser(),
                floor_data: floorData,
                versions: versions,
                assets: assets
            };
            
            if (includeMetadata) {
                backupPackage.metadata = await this.getFloorMetadata(floorId);
            }
            
            this.updateProgress(80, 'Compressing backup...');
            
            // Compress backup
            const compressedBackup = await this.compressBackup(backupPackage);
            
            this.updateProgress(90, 'Generating backup file...');
            
            // Create and download backup file
            const fileName = `backup_floor_${floorId}_${new Date().toISOString().split('T')[0]}.zip`;
            await this.utils.downloadZIP(compressedBackup, fileName);
            
            this.completeProgress('Floor backup created successfully');
            this.utils.showNotification('Floor backup created successfully', 'success');
            
        } catch (error) {
            this.failProgress('Backup failed: ' + error.message);
            throw error;
        }
    }

    // Import from JSON
    async importFromJSON(file, options = {}) {
        this.startProgress('Importing JSON', 'Reading file...');
        
        try {
            // Read file
            const fileContent = await this.utils.readFileAsText(file);
            
            this.updateProgress(25, 'Parsing JSON data...');
            
            // Parse JSON
            const importData = JSON.parse(fileContent);
            
            // Validate import data
            this.validateImportData(importData);
            
            this.updateProgress(50, 'Processing version data...');
            
            // Process version data
            const processedData = await this.processImportData(importData, options);
            
            this.updateProgress(75, 'Importing version...');
            
            // Import version
            const result = await this.importVersion(processedData, options);
            
            this.completeProgress('Import completed successfully');
            this.utils.showNotification('Version imported successfully', 'success');
            
            // Emit import completed event
            this.emitEvent('versionImported', result);
            
            return result;
            
        } catch (error) {
            this.failProgress('Import failed: ' + error.message);
            throw error;
        }
    }

    // Import from SVG
    async importFromSVG(file, options = {}) {
        this.startProgress('Importing SVG', 'Reading file...');
        
        try {
            // Read file
            const fileContent = await this.readFileAsText(file);
            
            this.updateProgress(25, 'Parsing SVG data...');
            
            // Parse SVG
            const svgData = this.parseSVGData(fileContent);
            
            this.updateProgress(50, 'Processing SVG elements...');
            
            // Process SVG data
            const processedData = await this.processSVGData(svgData, options);
            
            this.updateProgress(75, 'Importing SVG...');
            
            // Import SVG
            const result = await this.importSVG(processedData, options);
            
            this.completeProgress('Import completed successfully');
            this.showNotification('SVG imported successfully', 'success');
            
            // Emit import completed event
            this.emitEvent('svgImported', result);
            
            return result;
            
        } catch (error) {
            this.failProgress('Import failed: ' + error.message);
            throw error;
        }
    }

    // Restore from backup
    async restoreFromBackup(file, options = {}) {
        this.startProgress('Restoring from Backup', 'Reading backup file...');
        
        try {
            // Read backup file
            const backupData = await this.readBackupFile(file);
            
            this.updateProgress(25, 'Validating backup...');
            
            // Validate backup
            this.validateBackup(backupData);
            
            this.updateProgress(50, 'Preparing restore data...');
            
            // Prepare restore data
            const restoreData = await this.prepareRestoreData(backupData, options);
            
            this.updateProgress(75, 'Restoring data...');
            
            // Perform restore
            const result = await this.performRestore(restoreData, options);
            
            this.completeProgress('Restore completed successfully');
            this.showNotification('Backup restored successfully', 'success');
            
            // Emit restore completed event
            this.emitEvent('backupRestored', result);
            
            return result;
            
        } catch (error) {
            this.failProgress('Restore failed: ' + error.message);
            throw error;
        }
    }

    // Show file import dialog
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

    // Show backup restore dialog
    showBackupRestoreDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.zip';
        input.multiple = false;
        
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                this.restoreFromBackup(file);
            }
        });
        
        input.click();
    }

    // Start progress
    startProgress(title, description) {
        this.currentOperation = { title, description, progress: 0 };
        
        const modal = document.getElementById('export-import-progress-modal');
        const titleElement = document.getElementById('progress-title');
        const descriptionElement = document.getElementById('progress-description');
        const iconElement = document.getElementById('progress-icon');
        
        if (modal && titleElement && descriptionElement && iconElement) {
            titleElement.textContent = title;
            descriptionElement.textContent = description;
            iconElement.innerHTML = '<i class="fas fa-spinner fa-spin text-blue-500"></i>';
            modal.style.display = 'flex';
        }
        
        this.updateProgress(0);
    }

    // Update progress
    updateProgress(progress, description = null) {
        if (this.currentOperation) {
            this.currentOperation.progress = progress;
            if (description) {
                this.currentOperation.description = description;
            }
        }
        
        const barElement = document.getElementById('progress-bar');
        const descriptionElement = document.getElementById('progress-description');
        
        if (barElement) {
            barElement.style.width = `${progress}%`;
        }
        
        if (descriptionElement && description) {
            descriptionElement.textContent = description;
        }
    }

    // Complete progress
    completeProgress(message) {
        const iconElement = document.getElementById('progress-icon');
        const titleElement = document.getElementById('progress-title');
        
        if (iconElement) {
            iconElement.innerHTML = '<i class="fas fa-check-circle text-green-500"></i>';
        }
        
        if (titleElement) {
            titleElement.textContent = message;
        }
        
        setTimeout(() => {
            this.hideProgressModal();
        }, 2000);
    }

    // Fail progress
    failProgress(message) {
        const iconElement = document.getElementById('progress-icon');
        const titleElement = document.getElementById('progress-title');
        
        if (iconElement) {
            iconElement.innerHTML = '<i class="fas fa-times-circle text-red-500"></i>';
        }
        
        if (titleElement) {
            titleElement.textContent = message;
        }
        
        setTimeout(() => {
            this.hideProgressModal();
        }, 3000);
    }

    // Hide progress modal
    hideProgressModal() {
        const modal = document.getElementById('export-import-progress-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentOperation = null;
    }

    // Cancel current operation
    cancelCurrentOperation() {
        if (this.currentOperation) {
            this.currentOperation.cancelled = true;
            this.hideProgressModal();
            this.showNotification('Operation cancelled', 'info');
        }
    }

    // Show export/import panel
    showExportImportPanel() {
        const panel = document.getElementById('export-import-panel');
        if (panel) {
            panel.style.display = 'block';
        }
    }

    // Hide export/import panel
    hideExportImportPanel() {
        const panel = document.getElementById('export-import-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    // Export as JSON (convenience method)
    async exportAsJSON() {
        const currentVersion = this.getCurrentVersion();
        if (currentVersion) {
            await this.exportVersionAsJSON(currentVersion.id);
        } else {
            this.showNotification('No version selected for export', 'warning');
        }
    }

    // Export as SVG (convenience method)
    async exportAsSVG() {
        const currentVersion = this.getCurrentVersion();
        if (currentVersion) {
            await this.exportVersionAsSVG(currentVersion.id);
        } else {
            this.showNotification('No version selected for export', 'warning');
        }
    }

    // Create backup (convenience method)
    async createBackup() {
        const currentFloor = this.getCurrentFloor();
        if (currentFloor) {
            await this.createFloorBackup(currentFloor.id);
        } else {
            this.showNotification('No floor selected for backup', 'warning');
        }
    }

    // Utility methods
    getCurrentUser() {
        return {
            id: localStorage.getItem('user_id') || 'unknown',
            name: localStorage.getItem('user_name') || 'Unknown User'
        };
    }

    getCurrentVersion() {
        // This would typically come from your version control system
        return window.floorVersionControl?.getCurrentVersion();
    }

    getCurrentFloor() {
        // This would typically come from your floor selection system
        return {
            id: localStorage.getItem('current_floor_id'),
            name: localStorage.getItem('current_floor_name')
        };
    }

    // API methods (these would be implemented to call your backend)
    async getVersionData(versionId) {
        const response = await fetch(`/api/versions/${versionId}/data`);
        if (!response.ok) throw new Error('Failed to get version data');
        return response.json();
    }

    async getVersionMetadata(versionId) {
        const response = await fetch(`/api/versions/${versionId}/metadata`);
        if (!response.ok) throw new Error('Failed to get version metadata');
        return response.json();
    }

    async getVersionHistory(versionId) {
        const response = await fetch(`/api/versions/${versionId}/history`);
        if (!response.ok) throw new Error('Failed to get version history');
        return response.json();
    }

    async getVersionSVGData(versionId) {
        const response = await fetch(`/api/versions/${versionId}/svg`);
        if (!response.ok) throw new Error('Failed to get version SVG data');
        return response.json();
    }

    async getFloorData(floorId) {
        const response = await fetch(`/api/floors/${floorId}/data`);
        if (!response.ok) throw new Error('Failed to get floor data');
        return response.json();
    }

    async getFloorVersions(floorId) {
        const response = await fetch(`/api/floors/${floorId}/versions`);
        if (!response.ok) throw new Error('Failed to get floor versions');
        return response.json();
    }

    async getFloorMetadata(floorId) {
        const response = await fetch(`/api/floors/${floorId}/metadata`);
        if (!response.ok) throw new Error('Failed to get floor metadata');
        return response.json();
    }

    // File handling methods - now using shared utilities

    // Data processing methods
    async compressData(data) {
        // Simple compression - in production, you might use a library like pako
        return JSON.stringify(data);
    }

    async compressBackup(backupData) {
        // For ZIP compression, you'd use a library like JSZip
        return JSON.stringify(backupData);
    }

    createSVGDocument(svgData, includeMetadata) {
        // Create SVG document with metadata
        const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="${svgData.width}" height="${svgData.height}">
    ${includeMetadata ? this.createSVGMetadata(svgData.metadata) : ''}
    ${svgData.content}
</svg>`;
        return svg;
    }

    createSVGMetadata(metadata) {
        return `<metadata>
    <title>${metadata.title || 'Floor Plan'}</title>
    <description>${metadata.description || ''}</description>
    <created>${metadata.created_at || new Date().toISOString()}</created>
    <version>${metadata.version || '1.0'}</version>
</metadata>`;
    }

    async optimizeSVG(svgDocument) {
        // Basic SVG optimization - in production, you might use a library
        return svgDocument.replace(/\s+/g, ' ').trim();
    }

    parseSVGData(svgContent) {
        // Parse SVG content and extract relevant data
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgContent, 'image/svg+xml');
        
        return {
            width: doc.documentElement.getAttribute('width'),
            height: doc.documentElement.getAttribute('height'),
            content: svgContent,
            elements: Array.from(doc.documentElement.children)
        };
    }

    validateImportData(data) {
        if (!data.format || !data.version_data) {
            throw new Error('Invalid import data format');
        }
    }

    validateBackup(backupData) {
        if (!backupData.type || !backupData.version) {
            throw new Error('Invalid backup format');
        }
    }

    async processImportData(importData, options) {
        // Process and validate import data
        return importData.version_data;
    }

    async processSVGData(svgData, options) {
        // Process SVG data for import
        return svgData;
    }

    async prepareRestoreData(backupData, options) {
        // Prepare backup data for restore
        return backupData;
    }

    async collectVersionAssets(versionId) {
        // Collect all assets for a version
        return [];
    }

    async collectFloorAssets(floorId) {
        // Collect all assets for a floor
        return [];
    }

    async importVersion(data, options) {
        // Import version data
        const response = await fetch('/api/versions/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data, options })
        });
        
        if (!response.ok) throw new Error('Failed to import version');
        return response.json();
    }

    async importSVG(data, options) {
        // Import SVG data
        const response = await fetch('/api/svg/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data, options })
        });
        
        if (!response.ok) throw new Error('Failed to import SVG');
        return response.json();
    }

    async performRestore(data, options) {
        // Perform restore operation
        const response = await fetch('/api/backup/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data, options })
        });
        
        if (!response.ok) throw new Error('Failed to restore backup');
        return response.json();
    }

    async readBackupFile(file) {
        // Read and parse backup file
        const content = await this.utils.readFileAsText(file);
        return JSON.parse(content);
    }

    // Emit custom event
    emitEvent(eventName, data) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    // Get export/import statistics
    getExportImportStatistics() {
        return {
            exportQueue: this.exportQueue,
            importQueue: this.importQueue,
            currentOperation: this.currentOperation,
            options: this.options
        };
    }

    // Destroy the export/import system
    destroy() {
        // Clear queues
        this.exportQueue = [];
        this.importQueue = [];
        
        // Cancel current operation
        this.cancelCurrentOperation();
        
        // Remove UI elements
        const elements = [
            'export-import-panel',
            'export-import-progress-modal'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        });
    }
}

// Initialize global export/import system
const exportImportSystem = new ExportImportSystem();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExportImportSystem;
} 