// Version Control Panel Component
class VersionControlPanel {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            floorId: null,
            showCreateButton: true,
            showUndoRedo: true,
            showSearch: true,
            showFilter: true,
            maxHeight: '400px',
            onVersionSelect: null,
            onVersionRestore: null,
            onVersionCompare: null,
            ...options
        };

        this.versions = [];
        this.selectedVersion = null;
        this.isCollapsed = false;

        this.render();
        this.initializeEventListeners();
        this.loadVersions();
    }

    // Render the panel
    render() {
        this.container.innerHTML = `
            <div class="version-control-panel bg-white rounded-lg shadow-md border">
                <!-- Header -->
                <div class="p-4 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-history text-blue-600"></i>
                            <h3 class="text-lg font-semibold text-gray-900">Version History</h3>
                            <span class="text-sm text-gray-500">(${this.versions.length})</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            ${this.options.showCreateButton ? `
                                <button class="create-version-btn bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded-md transition-colors">
                                    <i class="fas fa-camera mr-1"></i>Snapshot
                                </button>
                            ` : ''}
                            <button class="collapse-btn text-gray-400 hover:text-gray-600">
                                <i class="fas fa-chevron-up"></i>
                            </button>
                        </div>
                    </div>

                    ${this.options.showUndoRedo ? `
                        <div class="undo-redo-controls mt-3 flex items-center space-x-2">
                            <button class="undo-btn bg-gray-500 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded disabled:opacity-50" disabled>
                                <i class="fas fa-undo mr-1"></i>Undo
                            </button>
                            <button class="redo-btn bg-gray-500 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded disabled:opacity-50" disabled>
                                <i class="fas fa-redo mr-1"></i>Redo
                            </button>
                        </div>
                    ` : ''}

                    ${(this.options.showSearch || this.options.showFilter) ? `
                        <div class="version-controls mt-3 flex items-center space-x-2">
                            ${this.options.showSearch ? `
                                <input type="text" class="version-search border border-gray-300 rounded px-2 py-1 text-sm flex-1"
                                       placeholder="Search versions...">
                            ` : ''}
                            ${this.options.showFilter ? `
                                <select class="version-filter border border-gray-300 rounded px-2 py-1 text-sm">
                                    <option value="all">All</option>
                                    <option value="manual">Manual</option>
                                    <option value="auto-save">Auto-save</option>
                                    <option value="branch">Branches</option>
                                </select>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>

                <!-- Version List -->
                <div class="version-list-container" style="max-height: ${this.options.maxHeight}; overflow-y: auto;">
                    <div class="version-list divide-y divide-gray-200">
                        <div class="p-4 text-center text-gray-500">
                            <i class="fas fa-spinner fa-spin text-lg mb-2"></i>
                            <p class="text-sm">Loading versions...</p>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="p-3 border-t border-gray-200 bg-gray-50">
                    <div class="flex items-center justify-between text-xs text-gray-600">
                        <span>Select a version to view details</span>
                        <div class="flex items-center space-x-2">
                            <button class="refresh-btn text-blue-600 hover:text-blue-800">
                                <i class="fas fa-sync-alt mr-1"></i>Refresh
                            </button>
                            <button class="expand-btn text-blue-600 hover:text-blue-800">
                                <i class="fas fa-expand mr-1"></i>Expand
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Collapse/expand
        this.container.querySelector('.collapse-btn').addEventListener('click', () => {
            this.toggleCollapse();
        });

        // Create version
        if (this.options.showCreateButton) {
            this.container.querySelector('.create-version-btn').addEventListener('click', () => {
                this.showCreateVersionModal();
            });
        }

        // Undo/Redo
        if (this.options.showUndoRedo) {
            this.container.querySelector('.undo-btn').addEventListener('click', () => {
                this.undo();
            });
            this.container.querySelector('.redo-btn').addEventListener('click', () => {
                this.redo();
            });
        }

        // Search
        if (this.options.showSearch) {
            this.container.querySelector('.version-search').addEventListener('input', (e) => {
                this.filterVersions(e.target.value);
            });
        }

        // Filter
        if (this.options.showFilter) {
            this.container.querySelector('.version-filter').addEventListener('change', (e) => {
                this.filterVersionsByType(e.target.value);
            });
        }

        // Refresh
        this.container.querySelector('.refresh-btn').addEventListener('click', () => {
            this.loadVersions();
        });

        // Expand
        this.container.querySelector('.expand-btn').addEventListener('click', () => {
            this.expandToFullView();
        });
    }

    // Toggle collapse state
    toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const listContainer = this.container.querySelector('.version-list-container');
        const collapseBtn = this.container.querySelector('.collapse-btn i');

        if (this.isCollapsed) {
            listContainer.style.display = 'none';
            collapseBtn.className = 'fas fa-chevron-down';
        } else {
            listContainer.style.display = 'block';
            collapseBtn.className = 'fas fa-chevron-up';
        }
    }

    // Load versions
    async loadVersions() {
        if (!this.options.floorId) {
            this.showEmptyState('No floor selected');
            return;
        }

        try {
            const response = await fetch(`/api/floors/${this.options.floorId}/versions`);
            if (response.ok) {
                this.versions = await response.json();
                this.renderVersionList();
                this.updateVersionCount();
            } else {
                throw new Error('Failed to load versions');
            }
        } catch (error) {
            this.showEmptyState('Error loading versions');
        }
    }

    // Render version list
    renderVersionList() {
        const container = this.container.querySelector('.version-list');

        if (this.versions.length === 0) {
            this.showEmptyState('No versions found');
            return;
        }

        container.innerHTML = this.versions.map(version => this.createVersionItem(version)).join('');

        // Add event listeners
        container.querySelectorAll('.version-item').forEach((item, index) => {
            item.addEventListener('click', () => this.selectVersion(this.versions[index]));
        });
    }

    // Create version item
    createVersionItem(version) {
        const date = new Date(version.created_at).toLocaleDateString();
        const time = new Date(version.created_at).toLocaleTimeString();
        const tags = this.getVersionTags(version);

        return `
            <div class="version-item p-3 cursor-pointer hover:bg-gray-50 transition-colors ${version.type}" data-version-id="${version.id}">
                <div class="flex justify-between items-start">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center mb-1">
                            <h4 class="font-medium text-gray-900 text-sm truncate">${version.description || 'Untitled Version'}</h4>
                            ${tags}
                        </div>
                        <div class="text-xs text-gray-600 mb-1">
                            <span class="font-medium">${version.created_by}</span> • ${date} ${time}
                        </div>
                        <div class="text-xs text-gray-500">
                            ${version.changes_count || 0} changes
                        </div>
                    </div>

                    <div class="version-actions ml-2 flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button class="compare-btn text-purple-600 hover:text-purple-800 p-1"
                                onclick="event.stopPropagation(); this.closest('.version-control-panel').versionControlPanel.compareVersion('${version.id}')">
                            <i class="fas fa-exchange-alt text-xs"></i>
                        </button>
                        <button class="restore-btn text-blue-600 hover:text-blue-800 p-1"
                                onclick="event.stopPropagation(); this.closest('.version-control-panel').versionControlPanel.restoreVersion('${version.id}')">
                            <i class="fas fa-undo text-xs"></i>
                        </button>
                        <button class="export-btn text-green-600 hover:text-green-800 p-1"
                                onclick="event.stopPropagation(); this.closest('.version-control-panel').versionControlPanel.exportVersion('${version.id}')">
                            <i class="fas fa-download text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Get version tags
    getVersionTags(version) {
        const tags = [];

        if (version.type === 'auto-save') {
            tags.push('<span class="version-tag tag-auto-save text-xs px-1 py-0.5 rounded bg-gray-100 text-gray-600 ml-1">Auto</span>');
        }
        if (version.type === 'branch') {
            tags.push('<span class="version-tag tag-branch text-xs px-1 py-0.5 rounded bg-green-100 text-green-700 ml-1">Branch</span>');
        }
        if (version.is_restored) {
            tags.push('<span class="version-tag tag-restored text-xs px-1 py-0.5 rounded bg-yellow-100 text-yellow-700 ml-1">Restored</span>');
        }

        return tags.join('');
    }

    // Show empty state
    showEmptyState(message) {
        const container = this.container.querySelector('.version-list');
        container.innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <i class="fas fa-inbox text-lg mb-2"></i>
                <p class="text-sm">${message}</p>
            </div>
        `;
    }

    // Update version count
    updateVersionCount() {
        const countElement = this.container.querySelector('h3 + span');
        if (countElement) {
            countElement.textContent = `(${this.versions.length})`;
        }
    }

    // Select version
    selectVersion(version) {
        this.selectedVersion = version;

        // Update UI
        this.container.querySelectorAll('.version-item').forEach(item => {
            item.classList.remove('selected', 'bg-blue-50', 'border-l-4', 'border-blue-500');
        });

        const selectedItem = this.container.querySelector(`[data-version-id="${version.id}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected', 'bg-blue-50', 'border-l-4', 'border-blue-500');
        }

        // Call callback
        if (this.options.onVersionSelect) {
            this.options.onVersionSelect(version);
        }
    }

    // Filter versions by search term
    filterVersions(searchTerm) {
        const items = this.container.querySelectorAll('.version-item');
        const term = searchTerm.toLowerCase();

        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(term) ? 'block' : 'none';
        });
    }

    // Filter versions by type
    filterVersionsByType(type) {
        const items = this.container.querySelectorAll('.version-item');

        items.forEach(item => {
            if (type === 'all' || item.classList.contains(type)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Show create version modal
    showCreateVersionModal() {
        // Create a simple modal for creating versions
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 w-96">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">Create Version</h3>
                    <button class="close-modal text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <form class="create-version-form">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea class="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                                  rows="3" placeholder="Describe this version..."></textarea>
                    </div>

                    <div class="mb-4">
                        <label class="flex items-center">
                            <input type="checkbox" class="mr-2">
                            <span class="text-sm text-gray-700">Auto-save version</span>
                        </label>
                    </div>

                    <div class="flex justify-end space-x-3">
                        <button type="button" class="cancel-create bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded text-sm">
                            Cancel
                        </button>
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm">
                            Create Version
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.cancel-create').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.create-version-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createVersion(modal);
        });
    }

    // Create version
    async createVersion(modal) {
        const description = modal.querySelector('textarea').value;
        const isAutoSave = modal.querySelector('input[type="checkbox"]').checked;

        try {
            const response = await fetch(`/api/floors/${this.options.floorId}/versions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description,
                    type: isAutoSave ? 'auto-save' : 'manual'
                })
            });

            if (response.ok) {
                const newVersion = await response.json();
                this.versions.unshift(newVersion);
                this.renderVersionList();
                this.updateVersionCount();
                document.body.removeChild(modal);
                this.showNotification('Version created successfully', 'success');
            } else {
                throw new Error('Failed to create version');
            }
        } catch (error) {
            this.showNotification('Error creating version', 'error');
        }
    }

    // Compare version
    async compareVersion(versionId) {
        if (this.options.onVersionCompare) {
            this.options.onVersionCompare(versionId);
        } else {
            // Default behavior - open in new window
            window.open(`/floor_version_control.html?compare=${versionId}`, '_blank');
        }
    }

    // Restore version
    async restoreVersion(versionId) {
        if (this.options.onVersionRestore) {
            this.options.onVersionRestore(versionId);
        } else {
            // Default behavior - show confirmation
            if (confirm('Are you sure you want to restore this version?')) {
                try {
                    const response = await fetch(`/api/floors/${this.options.floorId}/versions/${versionId}/restore`, {
                        method: 'POST'
                    });

                    if (response.ok) {
                        this.showNotification('Version restored successfully', 'success');
                        this.loadVersions();
                    } else {
                        throw new Error('Failed to restore version');
                    }
                } catch (error) {
                    this.showNotification('Error restoring version', 'error');
                }
            }
        }
    }

    // Export version
    async exportVersion(versionId) {
        try {
            const response = await fetch(`/api/floors/${this.options.floorId}/versions/${versionId}/export`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `version-${versionId}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
                this.showNotification('Version exported successfully', 'success');
            } else {
                throw new Error('Failed to export version');
            }
        } catch (error) {
            this.showNotification('Error exporting version', 'error');
        }
    }

    // Undo functionality
    undo() {
        // Implementation would depend on the undo stack
        this.showNotification('Undo functionality not implemented', 'warning');
    }

    // Redo functionality
    redo() {
        // Implementation would depend on the redo stack
        this.showNotification('Redo functionality not implemented', 'warning');
    }

    // Expand to full view
    expandToFullView() {
        window.open('/floor_version_control.html', '_blank');
    }

    // Show notification
    showNotification(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg text-white text-sm ${
            type === 'success' ? 'bg-green-600' :
            type === 'error' ? 'bg-red-600' :
            type === 'warning' ? 'bg-yellow-600' : 'bg-blue-600'
        }`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }

    // Update floor ID
    updateFloorId(floorId) {
        this.options.floorId = floorId;
        this.loadVersions();
    }

    // Get selected version
    getSelectedVersion() {
        return this.selectedVersion;
    }

    // Get all versions
    getVersions() {
        return this.versions;
    }

    // Destroy the panel
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VersionControlPanel;
}
