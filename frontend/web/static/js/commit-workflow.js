/**
 * Commit Workflow Module
 * GitHub-style as-built commit workflow for building repository
 * Handles file uploads, validation, and commit creation
 */

class CommitWorkflow {
    constructor() {
        this.uploadedFiles = [];
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.allowedExtensions = ['.dwg', '.dxf', '.rvt', '.ifc', '.pdf', '.png', '.jpg', '.jpeg'];
        this.isProcessing = false;
        
        this.initializeWorkflow();
        this.setupEventListeners();
        this.loadDraftData();
    }

    /**
     * Initialize commit workflow components
     */
    initializeWorkflow() {
        this.fileDropZone = document.getElementById('file-drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.commitButton = document.getElementById('commit-button');
        
        // Form elements
        this.buildingName = document.getElementById('building-name');
        this.buildingAddress = document.getElementById('building-address');
        this.buildingType = document.getElementById('building-type');
        this.yearBuilt = document.getElementById('year-built');
        this.leedCertified = document.getElementById('leed-certified');
        
        this.commitTitle = document.getElementById('commit-title');
        this.commitDescription = document.getElementById('commit-description');
        this.drawingDate = document.getElementById('drawing-date');
        this.drawingScale = document.getElementById('drawing-scale');
        this.accuracyVerified = document.getElementById('accuracy-verified');
        this.licenseAgreed = document.getElementById('license-agreed');
        
        // Summary elements
        this.filesAddedCount = document.getElementById('files-added-count');
        this.totalFileSize = document.getElementById('total-file-size');
        this.fileBreakdown = document.getElementById('file-breakdown');
        
        // Set default drawing date to today
        if (this.drawingDate) {
            this.drawingDate.valueAsDate = new Date();
        }
        
        console.log('Commit workflow initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // File drop zone events
        if (this.fileDropZone && this.fileInput) {
            this.fileDropZone.addEventListener('click', () => {
                this.fileInput.click();
            });
            
            this.fileDropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.fileDropZone.classList.add('drag-over');
            });
            
            this.fileDropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                this.fileDropZone.classList.remove('drag-over');
            });
            
            this.fileDropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.fileDropZone.classList.remove('drag-over');
                this.handleFileSelection(e.dataTransfer.files);
            });
            
            this.fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
        }

        // Form validation
        const formFields = [
            this.buildingName, this.buildingAddress, this.commitTitle,
            this.accuracyVerified, this.licenseAgreed
        ];
        
        formFields.forEach(field => {
            if (field) {
                field.addEventListener('input', () => this.validateForm());
                field.addEventListener('change', () => this.validateForm());
            }
        });

        // Commit button
        if (this.commitButton) {
            this.commitButton.addEventListener('click', () => this.processCommit());
        }

        // Auto-save draft
        this.setupAutoSave();

        // Building name suggestions
        if (this.buildingName) {
            this.setupBuildingNameSuggestions();
        }
    }

    /**
     * Handle file selection
     */
    async handleFileSelection(files) {
        const validFiles = [];
        const errors = [];

        for (let file of files) {
            const validation = this.validateFile(file);
            
            if (validation.isValid) {
                // Check for duplicates
                const isDuplicate = this.uploadedFiles.some(uploaded => 
                    uploaded.name === file.name && uploaded.size === file.size
                );
                
                if (!isDuplicate) {
                    validFiles.push(file);
                } else {
                    errors.push(`File "${file.name}" is already uploaded`);
                }
            } else {
                errors.push(validation.error);
            }
        }

        // Add valid files
        for (let file of validFiles) {
            const fileData = await this.processFile(file);
            this.uploadedFiles.push(fileData);
        }

        // Show errors if any
        if (errors.length > 0) {
            this.showFileErrors(errors);
        }

        // Update UI
        this.updateFileList();
        this.updateChangeSummary();
        this.validateForm();
    }

    /**
     * Validate individual file
     */
    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                isValid: false,
                error: `File "${file.name}" is too large (max ${this.maxFileSize / 1024 / 1024}MB)`
            };
        }

        // Check file extension
        const extension = this.getFileExtension(file.name);
        if (!this.allowedExtensions.includes(extension.toLowerCase())) {
            return {
                isValid: false,
                error: `File type "${extension}" is not supported for "${file.name}"`
            };
        }

        return { isValid: true };
    }

    /**
     * Process file and extract metadata
     */
    async processFile(file) {
        const fileData = {
            file: file,
            name: file.name,
            size: file.size,
            type: this.getFileType(file.name),
            extension: this.getFileExtension(file.name),
            uploadedAt: new Date(),
            preview: null,
            metadata: {}
        };

        // Generate preview for images
        if (file.type.startsWith('image/')) {
            fileData.preview = await this.generateImagePreview(file);
        }

        // Extract metadata based on file type
        fileData.metadata = await this.extractFileMetadata(file);

        return fileData;
    }

    /**
     * Generate image preview
     */
    generateImagePreview(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
        });
    }

    /**
     * Extract file metadata (simplified)
     */
    async extractFileMetadata(file) {
        const metadata = {
            lastModified: new Date(file.lastModified),
            size: file.size,
            type: file.type || 'application/octet-stream'
        };

        // For CAD files, we'd extract drawing info here
        // For now, return basic metadata
        return metadata;
    }

    /**
     * Update file list UI
     */
    updateFileList() {
        if (!this.fileList) return;

        this.fileList.innerHTML = '';

        this.uploadedFiles.forEach((fileData, index) => {
            const fileItem = this.createFileListItem(fileData, index);
            this.fileList.appendChild(fileItem);
        });
    }

    /**
     * Create file list item
     */
    createFileListItem(fileData, index) {
        const item = document.createElement('div');
        item.className = 'file-preview p-4 flex items-center space-x-4';
        
        const sizeInMB = (fileData.size / 1024 / 1024).toFixed(2);
        const fileTypeIcon = this.getFileTypeIcon(fileData.extension);
        
        item.innerHTML = `
            <div class="flex-shrink-0">
                ${fileData.preview ? 
                    `<img src="${fileData.preview}" alt="${fileData.name}" class="w-12 h-12 object-cover rounded">` :
                    `<div class="w-12 h-12 bg-gray-100 rounded flex items-center justify-center text-xl">${fileTypeIcon}</div>`
                }
            </div>
            
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                    <h4 class="text-sm font-medium text-gray-900 truncate">${fileData.name}</h4>
                    <button 
                        class="text-red-500 hover:text-red-700 text-sm"
                        onclick="commitWorkflow.removeFile(${index})"
                    >
                        Remove
                    </button>
                </div>
                <div class="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                    <span>${sizeInMB} MB</span>
                    <span>${fileData.type}</span>
                    <span>Added ${this.formatTimeAgo(fileData.uploadedAt)}</span>
                </div>
            </div>
            
            <div class="flex-shrink-0">
                <div class="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                    </svg>
                </div>
            </div>
        `;

        return item;
    }

    /**
     * Remove file from upload list
     */
    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.updateFileList();
        this.updateChangeSummary();
        this.validateForm();
    }

    /**
     * Update change summary
     */
    updateChangeSummary() {
        if (this.filesAddedCount) {
            this.filesAddedCount.textContent = this.uploadedFiles.length;
        }

        // Calculate total file size
        const totalSize = this.uploadedFiles.reduce((sum, file) => sum + file.size, 0);
        const totalSizeMB = (totalSize / 1024 / 1024).toFixed(2);
        
        if (this.totalFileSize) {
            this.totalFileSize.textContent = `${totalSizeMB} MB`;
        }

        // Update file breakdown
        this.updateFileBreakdown();
    }

    /**
     * Update file type breakdown
     */
    updateFileBreakdown() {
        if (!this.fileBreakdown) return;

        const typeCount = {};
        this.uploadedFiles.forEach(file => {
            typeCount[file.type] = (typeCount[file.type] || 0) + 1;
        });

        const breakdownContainer = this.fileBreakdown.querySelector('.space-y-1') || this.fileBreakdown;
        breakdownContainer.innerHTML = '';

        Object.entries(typeCount).forEach(([type, count]) => {
            const item = document.createElement('div');
            item.className = 'flex justify-between';
            item.innerHTML = `
                <span>${type}</span>
                <span class="font-medium">${count}</span>
            `;
            breakdownContainer.appendChild(item);
        });

        if (Object.keys(typeCount).length === 0) {
            breakdownContainer.innerHTML = '<div class="text-gray-400 text-sm">No files uploaded</div>';
        }
    }

    /**
     * Validate form
     */
    validateForm() {
        const isValid = this.isFormValid();
        
        if (this.commitButton) {
            this.commitButton.disabled = !isValid;
        }

        return isValid;
    }

    /**
     * Check if form is valid
     */
    isFormValid() {
        // Check required fields
        const requiredFields = [
            this.buildingName?.value.trim(),
            this.buildingAddress?.value.trim(),
            this.commitTitle?.value.trim()
        ];

        const hasRequiredFields = requiredFields.every(field => field && field.length > 0);

        // Check checkboxes
        const hasAgreements = this.accuracyVerified?.checked && this.licenseAgreed?.checked;

        // Check files
        const hasFiles = this.uploadedFiles.length > 0;

        return hasRequiredFields && hasAgreements && hasFiles;
    }

    /**
     * Process commit
     */
    async processCommit() {
        if (this.isProcessing || !this.isFormValid()) return;

        this.isProcessing = true;
        this.updateCommitButtonState(true);

        try {
            // Prepare commit data
            const commitData = this.prepareCommitData();
            
            // Upload files
            const uploadedFileIds = await this.uploadFiles();
            commitData.fileIds = uploadedFileIds;

            // Create commit
            const result = await this.createCommit(commitData);
            
            // Handle success
            this.handleCommitSuccess(result);

        } catch (error) {
            console.error('Commit failed:', error);
            this.handleCommitError(error);
        } finally {
            this.isProcessing = false;
            this.updateCommitButtonState(false);
        }
    }

    /**
     * Prepare commit data
     */
    prepareCommitData() {
        return {
            // Building info
            building: {
                name: this.buildingName?.value.trim(),
                address: this.buildingAddress?.value.trim(),
                type: this.buildingType?.value,
                yearBuilt: this.yearBuilt?.value ? parseInt(this.yearBuilt.value) : null,
                leedCertified: this.leedCertified?.checked || false
            },
            
            // Commit info
            commit: {
                title: this.commitTitle?.value.trim(),
                description: this.commitDescription?.value.trim(),
                drawingDate: this.drawingDate?.value,
                drawingScale: this.drawingScale?.value
            },
            
            // Files info
            files: this.uploadedFiles.map(file => ({
                name: file.name,
                size: file.size,
                type: file.type,
                extension: file.extension,
                metadata: file.metadata
            })),
            
            // Verification
            verification: {
                accuracyVerified: this.accuracyVerified?.checked || false,
                licenseAgreed: this.licenseAgreed?.checked || false
            },
            
            // Timestamps
            createdAt: new Date().toISOString()
        };
    }

    /**
     * Upload files to server
     */
    async uploadFiles() {
        const uploadPromises = this.uploadedFiles.map(async (fileData, index) => {
            const formData = new FormData();
            formData.append('file', fileData.file);
            formData.append('metadata', JSON.stringify(fileData.metadata));
            
            // In production, upload to actual API
            await this.delay(1000 + Math.random() * 2000); // Simulate upload time
            
            return `file_${Date.now()}_${index}`;
        });

        return Promise.all(uploadPromises);
    }

    /**
     * Create commit via API
     */
    async createCommit(commitData) {
        // In production, call actual API
        await this.delay(1500); // Simulate API call
        
        return {
            id: `commit_${Date.now()}`,
            buildingName: commitData.building.name,
            commitHash: this.generateCommitHash(),
            createdAt: new Date().toISOString(),
            fileCount: commitData.files.length,
            totalSize: commitData.files.reduce((sum, file) => sum + file.size, 0)
        };
    }

    /**
     * Handle commit success
     */
    handleCommitSuccess(result) {
        // Clear draft data
        this.clearDraftData();
        
        // Show success message
        this.showSuccessMessage(result);
        
        // Redirect to building page (after delay)
        setTimeout(() => {
            window.location.href = `building.html?name=${encodeURIComponent(result.buildingName)}`;
        }, 3000);
    }

    /**
     * Handle commit error
     */
    handleCommitError(error) {
        this.showErrorMessage(error.message || 'Commit failed. Please try again.');
    }

    /**
     * Update commit button state
     */
    updateCommitButtonState(isProcessing) {
        if (this.commitButton) {
            if (isProcessing) {
                this.commitButton.textContent = 'Committing...';
                this.commitButton.disabled = true;
                this.commitButton.innerHTML = `
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Committing...
                `;
            } else {
                this.commitButton.textContent = 'Commit As-Built';
                this.commitButton.disabled = !this.isFormValid();
            }
        }
    }

    /**
     * Setup auto-save functionality
     */
    setupAutoSave() {
        const autoSaveFields = [
            this.buildingName, this.buildingAddress, this.buildingType, this.yearBuilt,
            this.commitTitle, this.commitDescription, this.drawingDate, this.drawingScale
        ];

        autoSaveFields.forEach(field => {
            if (field) {
                field.addEventListener('input', () => this.saveDraft());
            }
        });

        // Auto-save every 30 seconds
        setInterval(() => this.saveDraft(), 30000);
    }

    /**
     * Save draft to localStorage
     */
    saveDraft() {
        const draftData = {
            building: {
                name: this.buildingName?.value || '',
                address: this.buildingAddress?.value || '',
                type: this.buildingType?.value || '',
                yearBuilt: this.yearBuilt?.value || '',
                leedCertified: this.leedCertified?.checked || false
            },
            commit: {
                title: this.commitTitle?.value || '',
                description: this.commitDescription?.value || '',
                drawingDate: this.drawingDate?.value || '',
                drawingScale: this.drawingScale?.value || ''
            },
            savedAt: new Date().toISOString()
        };

        localStorage.setItem('arxos_commit_draft', JSON.stringify(draftData));
    }

    /**
     * Load draft from localStorage
     */
    loadDraftData() {
        try {
            const draftData = localStorage.getItem('arxos_commit_draft');
            if (!draftData) return;

            const draft = JSON.parse(draftData);
            
            // Load building data
            if (this.buildingName) this.buildingName.value = draft.building?.name || '';
            if (this.buildingAddress) this.buildingAddress.value = draft.building?.address || '';
            if (this.buildingType) this.buildingType.value = draft.building?.type || '';
            if (this.yearBuilt) this.yearBuilt.value = draft.building?.yearBuilt || '';
            if (this.leedCertified) this.leedCertified.checked = draft.building?.leedCertified || false;
            
            // Load commit data
            if (this.commitTitle) this.commitTitle.value = draft.commit?.title || '';
            if (this.commitDescription) this.commitDescription.value = draft.commit?.description || '';
            if (this.drawingDate) this.drawingDate.value = draft.commit?.drawingDate || '';
            if (this.drawingScale) this.drawingScale.value = draft.commit?.drawingScale || '';

            console.log('Draft data loaded');
        } catch (error) {
            console.error('Failed to load draft data:', error);
        }
    }

    /**
     * Clear draft data
     */
    clearDraftData() {
        localStorage.removeItem('arxos_commit_draft');
    }

    /**
     * Setup building name suggestions
     */
    setupBuildingNameSuggestions() {
        // This would integrate with the building search API
        // For now, just basic functionality
    }

    /**
     * Show success message
     */
    showSuccessMessage(result) {
        const message = document.createElement('div');
        message.className = 'fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-6 py-4 rounded-lg shadow-lg z-50';
        message.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <div class="font-semibold">Commit successful!</div>
                    <div class="text-sm">Redirecting to building page...</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 5000);
    }

    /**
     * Show error message
     */
    showErrorMessage(errorMessage) {
        const message = document.createElement('div');
        message.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg shadow-lg z-50';
        message.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <div class="font-semibold">Commit failed</div>
                    <div class="text-sm">${errorMessage}</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 5000);
    }

    /**
     * Show file errors
     */
    showFileErrors(errors) {
        errors.forEach(error => {
            console.warn('File error:', error);
            // In production, show user-friendly error messages
        });
    }

    // Utility methods
    getFileExtension(filename) {
        return filename.substring(filename.lastIndexOf('.'));
    }

    getFileType(filename) {
        const ext = this.getFileExtension(filename).toLowerCase();
        const typeMap = {
            '.dwg': 'AutoCAD Drawing',
            '.dxf': 'AutoCAD Exchange',
            '.rvt': 'Revit Model',
            '.ifc': 'Industry Foundation Classes',
            '.pdf': 'PDF Document',
            '.png': 'PNG Image',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image'
        };
        return typeMap[ext] || 'Unknown';
    }

    getFileTypeIcon(extension) {
        const iconMap = {
            '.dwg': '📐',
            '.dxf': '📐',
            '.rvt': '🏗️',
            '.ifc': '🏢',
            '.pdf': '📄',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️'
        };
        return iconMap[extension.toLowerCase()] || '📄';
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    generateCommitHash() {
        return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize commit workflow when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.commitWorkflow = new CommitWorkflow();
    console.log('Commit workflow system initialized');
});