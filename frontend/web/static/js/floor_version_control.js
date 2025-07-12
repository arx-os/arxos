// Floor Version Control JavaScript
class FloorVersionControl {
    constructor() {
        this.currentFloor = null;
        this.versions = [];
        this.selectedVersion = null;
        this.undoStack = [];
        this.redoStack = [];
        this.isProcessing = false;
        this.apiBaseUrl = 'http://localhost:8080/api';
        
        this.initializeEventListeners();
        this.loadFloors();
        this.setupKeyboardShortcuts();
    }

    // Initialize all event listeners
    initializeEventListeners() {
        // Floor selection
        document.getElementById('floor-select').addEventListener('change', (e) => {
            this.currentFloor = e.target.value;
            if (this.currentFloor) {
                this.loadVersions();
            }
        });

        // Create snapshot
        document.getElementById('create-snapshot-btn').addEventListener('click', () => {
            this.showSnapshotModal();
        });

        // Undo/Redo buttons
        document.getElementById('undo-btn').addEventListener('click', () => this.undo());
        document.getElementById('redo-btn').addEventListener('click', () => this.redo());

        // Version search and filter
        document.getElementById('version-search').addEventListener('input', (e) => {
            this.filterVersions(e.target.value);
        });

        document.getElementById('version-filter').addEventListener('change', (e) => {
            this.filterVersionsByType(e.target.value);
        });

        // Modal events
        this.initializeModalEvents();

        // Comparison view events
        document.getElementById('export-comparison-btn').addEventListener('click', () => {
            this.exportComparisonReport();
        });

        document.getElementById('close-comparison-btn').addEventListener('click', () => {
            this.hideComparisonView();
        });
    }

    // Initialize modal event listeners
    initializeModalEvents() {
        // Snapshot modal
        document.getElementById('close-snapshot-modal').addEventListener('click', () => {
            this.hideModal('snapshot-modal');
        });

        document.getElementById('cancel-snapshot').addEventListener('click', () => {
            this.hideModal('snapshot-modal');
        });

        document.getElementById('snapshot-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSnapshot();
        });

        // Restore modal
        document.getElementById('close-restore-modal').addEventListener('click', () => {
            this.hideModal('restore-modal');
        });

        document.getElementById('cancel-restore').addEventListener('click', () => {
            this.hideModal('restore-modal');
        });

        document.getElementById('confirm-restore').addEventListener('click', () => {
            this.confirmRestore();
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.hideModal(overlay.id);
                }
            });
        });
    }

    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'z':
                        e.preventDefault();
                        if (e.shiftKey) {
                            this.redo();
                        } else {
                            this.undo();
                        }
                        break;
                    case 'y':
                        e.preventDefault();
                        this.redo();
                        break;
                }
            }
        });
    }

    // Load available floors
    async loadFloors() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/floors`);
            if (response.ok) {
                const floors = await response.json();
                const select = document.getElementById('floor-select');
                select.innerHTML = '<option value="">Select a floor...</option>';
                
                floors.forEach(floor => {
                    const option = document.createElement('option');
                    option.value = floor.id;
                    option.textContent = floor.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            this.showToast('Error loading floors', 'error');
        }
    }

    // Load versions for current floor
    async loadVersions() {
        if (!this.currentFloor) return;

        try {
            this.showProgress('Loading versions...');
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions`);
            
            if (response.ok) {
                this.versions = await response.json();
                this.renderVersionList();
                this.hideProgress();
            } else {
                throw new Error('Failed to load versions');
            }
        } catch (error) {
            this.hideProgress();
            this.showToast('Error loading versions', 'error');
        }
    }

    // Render version list
    renderVersionList() {
        const container = document.getElementById('version-list');
        
        if (this.versions.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    <i class="fas fa-history text-2xl mb-2"></i>
                    <p>No versions found. Create your first snapshot to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.versions.map(version => this.createVersionItem(version)).join('');
        
        // Add event listeners to version items
        container.querySelectorAll('.version-item').forEach((item, index) => {
            item.addEventListener('click', () => this.selectVersion(this.versions[index]));
        });
    }

    // Create version item HTML
    createVersionItem(version) {
        const date = new Date(version.created_at).toLocaleString();
        const tags = this.getVersionTags(version);
        
        return `
            <div class="version-item p-4 cursor-pointer ${version.type}" data-version-id="${version.id}">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center mb-2">
                            <h4 class="font-medium text-gray-900">${version.description || 'Untitled Version'}</h4>
                            ${tags}
                        </div>
                        <div class="text-sm text-gray-600 mb-2">
                            <span class="font-medium">${version.created_by}</span> • ${date}
                        </div>
                        <div class="text-xs text-gray-500">
                            ${version.changes_count || 0} changes • ${version.size || '0 KB'}
                        </div>
                    </div>
                    
                    <div class="version-actions">
                        <button class="compare-button" onclick="event.stopPropagation(); floorVersionControl.compareVersion('${version.id}')">
                            <i class="fas fa-exchange-alt"></i>
                        </button>
                        <button class="restore-button" onclick="event.stopPropagation(); floorVersionControl.showRestoreModal('${version.id}')">
                            <i class="fas fa-undo"></i>
                        </button>
                        <button class="export-button" onclick="event.stopPropagation(); floorVersionControl.exportVersion('${version.id}')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="delete-button" onclick="event.stopPropagation(); floorVersionControl.deleteVersion('${version.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Get version tags HTML
    getVersionTags(version) {
        const tags = [];
        
        if (version.type === 'auto-save') {
            tags.push('<span class="version-tag tag-auto-save">Auto-save</span>');
        }
        if (version.type === 'branch') {
            tags.push('<span class="version-tag tag-branch">Branch</span>');
        }
        if (version.is_restored) {
            tags.push('<span class="version-tag tag-restored">Restored</span>');
        }
        
        return tags.join('');
    }

    // Select version
    selectVersion(version) {
        this.selectedVersion = version;
        
        // Update UI
        document.querySelectorAll('.version-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        const selectedItem = document.querySelector(`[data-version-id="${version.id}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
        
        this.renderVersionDetails(version);
    }

    // Render version details
    renderVersionDetails(version) {
        const container = document.getElementById('version-details');
        const date = new Date(version.created_at).toLocaleString();
        
        container.innerHTML = `
            <div class="space-y-4">
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">${version.description || 'Untitled Version'}</h4>
                    <p class="text-sm text-gray-600">${version.created_by}</p>
                    <p class="text-sm text-gray-600">${date}</p>
                </div>
                
                <div class="bg-gray-50 p-3 rounded-md">
                    <h5 class="font-medium text-gray-900 mb-2">Version Information</h5>
                    <div class="space-y-1 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Type:</span>
                            <span class="font-medium">${this.formatVersionType(version.type)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Changes:</span>
                            <span class="font-medium">${version.changes_count || 0}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Size:</span>
                            <span class="font-medium">${version.size || '0 KB'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">ID:</span>
                            <span class="font-mono text-xs">${version.id}</span>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-2">
                    <button class="w-full restore-button py-2 px-4 rounded-md" onclick="floorVersionControl.showRestoreModal('${version.id}')">
                        <i class="fas fa-undo mr-2"></i>Restore This Version
                    </button>
                    <button class="w-full compare-button py-2 px-4 rounded-md" onclick="floorVersionControl.compareVersion('${version.id}')">
                        <i class="fas fa-exchange-alt mr-2"></i>Compare with Current
                    </button>
                    <button class="w-full export-button py-2 px-4 rounded-md" onclick="floorVersionControl.exportVersion('${version.id}')">
                        <i class="fas fa-download mr-2"></i>Export Version
                    </button>
                </div>
            </div>
        `;
    }

    // Format version type
    formatVersionType(type) {
        const types = {
            'manual': 'Manual Snapshot',
            'auto-save': 'Auto Save',
            'branch': 'Branch',
            'restored': 'Restored'
        };
        return types[type] || type;
    }

    // Filter versions by search term
    filterVersions(searchTerm) {
        const items = document.querySelectorAll('.version-item');
        const term = searchTerm.toLowerCase();
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(term) ? 'block' : 'none';
        });
    }

    // Filter versions by type
    filterVersionsByType(type) {
        const items = document.querySelectorAll('.version-item');
        
        items.forEach(item => {
            if (type === 'all' || item.classList.contains(type)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Show snapshot modal
    showSnapshotModal() {
        document.getElementById('snapshot-modal').style.display = 'block';
        document.getElementById('snapshot-description').focus();
    }

    // Create snapshot
    async createSnapshot() {
        const description = document.getElementById('snapshot-description').value;
        const tags = document.getElementById('snapshot-tags').value;
        const isAutoSave = document.getElementById('snapshot-auto-save').checked;

        if (!this.currentFloor) {
            this.showToast('Please select a floor first', 'warning');
            return;
        }

        try {
            this.showProgress('Creating snapshot...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description,
                    tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
                    type: isAutoSave ? 'auto-save' : 'manual'
                })
            });

            if (response.ok) {
                const newVersion = await response.json();
                this.versions.unshift(newVersion);
                this.renderVersionList();
                this.hideModal('snapshot-modal');
                this.showToast('Snapshot created successfully', 'success');
                
                // Reset form
                document.getElementById('snapshot-form').reset();
            } else {
                throw new Error('Failed to create snapshot');
            }
        } catch (error) {
            this.showToast('Error creating snapshot', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Show restore modal
    async showRestoreModal(versionId) {
        const version = this.versions.find(v => v.id === versionId);
        if (!version) return;

        // Check for conflicts
        const conflicts = await this.checkConflicts(versionId);
        
        document.getElementById('restore-version-info').innerHTML = `
            <div class="font-medium">${version.description || 'Untitled Version'}</div>
            <div class="text-sm text-gray-600">${version.created_by} • ${new Date(version.created_at).toLocaleString()}</div>
        `;

        // Show/hide conflict warning
        const warning = document.getElementById('restore-warning');
        if (conflicts.length > 0) {
            warning.style.display = 'block';
            document.getElementById('conflict-list').innerHTML = conflicts.map(conflict => 
                `<li>${conflict}</li>`
            ).join('');
        } else {
            warning.style.display = 'none';
        }

        document.getElementById('restore-modal').style.display = 'block';
        this.selectedVersion = version;
    }

    // Check for conflicts
    async checkConflicts(versionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${versionId}/conflicts`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error checking conflicts:', error);
        }
        return [];
    }

    // Confirm restore
    async confirmRestore() {
        if (!this.selectedVersion) return;

        try {
            this.hideModal('restore-modal');
            this.showProgress('Restoring version...', 'This may take a few moments...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${this.selectedVersion.id}/restore`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showToast('Version restored successfully', 'success');
                this.loadVersions(); // Reload versions
                
                // Add to undo stack
                this.undoStack.push({
                    action: 'restore',
                    versionId: this.selectedVersion.id,
                    timestamp: Date.now()
                });
                this.updateUndoRedoButtons();
            } else {
                throw new Error('Failed to restore version');
            }
        } catch (error) {
            this.showToast('Error restoring version', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Compare version
    async compareVersion(versionId) {
        try {
            this.showProgress('Loading comparison...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${versionId}/compare`);
            if (response.ok) {
                const comparison = await response.json();
                this.showComparisonView(comparison);
            } else {
                throw new Error('Failed to load comparison');
            }
        } catch (error) {
            this.showToast('Error loading comparison', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Show comparison view
    showComparisonView(comparison) {
        document.getElementById('comparison-view').style.display = 'block';
        
        // Update labels
        document.getElementById('from-version-label').textContent = `From: ${comparison.from_version.description || 'Current'}`;
        document.getElementById('to-version-label').textContent = `To: ${comparison.to_version.description || 'Selected Version'}`;
        
        // Render comparison content
        this.renderComparisonContent(comparison);
    }

    // Render comparison content
    renderComparisonContent(comparison) {
        const fromContent = document.getElementById('from-version-content');
        const toContent = document.getElementById('to-version-content');
        
        fromContent.innerHTML = this.renderDiffContent(comparison.from_data, comparison.changes, 'from');
        toContent.innerHTML = this.renderDiffContent(comparison.to_data, comparison.changes, 'to');
    }

    // Render diff content
    renderDiffContent(data, changes, side) {
        if (!data) return '<div class="text-gray-500">No data available</div>';
        
        let html = '<div class="space-y-2">';
        
        changes.forEach(change => {
            const changeClass = this.getChangeClass(change.type);
            const indicator = `<span class="change-indicator ${changeClass}"></span>`;
            
            if (side === 'from' && change.type === 'removed') {
                html += `<div class="diff-removed p-2 rounded">${indicator}${change.key}: ${change.old_value}</div>`;
            } else if (side === 'to' && change.type === 'added') {
                html += `<div class="diff-added p-2 rounded">${indicator}${change.key}: ${change.new_value}</div>`;
            } else if (change.type === 'modified') {
                const value = side === 'from' ? change.old_value : change.new_value;
                html += `<div class="diff-modified p-2 rounded">${indicator}${change.key}: ${value}</div>`;
            } else if (change.type === 'unchanged') {
                html += `<div class="p-2">${change.key}: ${change.value}</div>`;
            }
        });
        
        html += '</div>';
        return html;
    }

    // Get change class
    getChangeClass(type) {
        const classes = {
            'added': 'change-added',
            'removed': 'change-removed',
            'modified': 'change-modified'
        };
        return classes[type] || '';
    }

    // Hide comparison view
    hideComparisonView() {
        document.getElementById('comparison-view').style.display = 'none';
    }

    // Export comparison report
    async exportComparisonReport() {
        try {
            this.showProgress('Generating report...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/export-comparison`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'pdf'
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `version-comparison-${Date.now()}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.showToast('Comparison report exported successfully', 'success');
            } else {
                throw new Error('Failed to export report');
            }
        } catch (error) {
            this.showToast('Error exporting report', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Export version
    async exportVersion(versionId) {
        try {
            this.showProgress('Exporting version...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${versionId}/export`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `version-${versionId}-${Date.now()}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.showToast('Version exported successfully', 'success');
            } else {
                throw new Error('Failed to export version');
            }
        } catch (error) {
            this.showToast('Error exporting version', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Delete version
    async deleteVersion(versionId) {
        if (!confirm('Are you sure you want to delete this version? This action cannot be undone.')) {
            return;
        }

        try {
            this.showProgress('Deleting version...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${versionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.versions = this.versions.filter(v => v.id !== versionId);
                this.renderVersionList();
                this.showToast('Version deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete version');
            }
        } catch (error) {
            this.showToast('Error deleting version', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Undo functionality
    undo() {
        if (this.undoStack.length === 0) return;
        
        const lastAction = this.undoStack.pop();
        this.redoStack.push(lastAction);
        
        // Perform undo action
        if (lastAction.action === 'restore') {
            this.undoRestore(lastAction);
        }
        
        this.updateUndoRedoButtons();
    }

    // Redo functionality
    redo() {
        if (this.redoStack.length === 0) return;
        
        const nextAction = this.redoStack.pop();
        this.undoStack.push(nextAction);
        
        // Perform redo action
        if (nextAction.action === 'restore') {
            this.redoRestore(nextAction);
        }
        
        this.updateUndoRedoButtons();
    }

    // Undo restore
    async undoRestore(action) {
        try {
            this.showProgress('Undoing restore...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${action.versionId}/undo-restore`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showToast('Restore undone successfully', 'success');
                this.loadVersions();
            } else {
                throw new Error('Failed to undo restore');
            }
        } catch (error) {
            this.showToast('Error undoing restore', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Redo restore
    async redoRestore(action) {
        try {
            this.showProgress('Redoing restore...');
            
            const response = await fetch(`${this.apiBaseUrl}/floors/${this.currentFloor}/versions/${action.versionId}/restore`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showToast('Restore redone successfully', 'success');
                this.loadVersions();
            } else {
                throw new Error('Failed to redo restore');
            }
        } catch (error) {
            this.showToast('Error redoing restore', 'error');
        } finally {
            this.hideProgress();
        }
    }

    // Update undo/redo buttons
    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('undo-btn');
        const redoBtn = document.getElementById('redo-btn');
        
        undoBtn.disabled = this.undoStack.length === 0;
        redoBtn.disabled = this.redoStack.length === 0;
    }

    // Show modal
    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    // Hide modal
    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    // Show progress
    showProgress(title = 'Processing...', message = 'Please wait while we process your request.') {
        document.getElementById('progress-title').textContent = title;
        document.getElementById('progress-message').textContent = message;
        document.getElementById('progress-modal').style.display = 'block';
        this.isProcessing = true;
    }

    // Hide progress
    hideProgress() {
        document.getElementById('progress-modal').style.display = 'none';
        this.isProcessing = false;
    }

    // Show toast notification
    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        toast.className = `toast ${type} p-4 rounded-md shadow-lg`;
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="fas ${this.getToastIcon(type)} mr-2"></i>
                    <span>${message}</span>
                </div>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }

    // Get toast icon
    getToastIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }
}

// Initialize the floor version control system
const floorVersionControl = new FloorVersionControl();
