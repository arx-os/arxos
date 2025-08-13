/**
 * Auto-Snapshot Manager for Frontend
 *
 * Provides UI controls and monitoring for auto-snapshot functionality:
 * - Configuration management
 * - Real-time monitoring
 * - Manual snapshot creation
 * - Service statistics
 */

class AutoSnapshotManager {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: '/auto-snapshot',
            updateInterval: 5000, // 5 seconds
            enableNotifications: true,
            enableRealTimeUpdates: true,
            showActivityIndicators: true,
            ...options
        };

        this.service = null;
        this.config = null;
        this.stats = null;
        this.activeFloors = new Set();
        this.updateTimer = null;
        this.isInitialized = false;
        this.eventListeners = new Map();

        this.initialize();
    }

    async initialize() {
        try {
            await this.loadConfiguration();
            await this.loadStats();
            await this.loadActiveFloors();

            if (this.options.enableRealTimeUpdates) {
                this.startRealTimeUpdates();
            }

            this.isInitialized = true;
            this.emitEvent('initialized', { manager: this });

        } catch (error) {
            console.error('Failed to initialize AutoSnapshotManager:', error);
            this.emitEvent('error', { error, context: 'initialization' });
        }
    }

    // Configuration Management
    async loadConfiguration() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/config`);
            if (!response.ok) throw new Error('Failed to load configuration');

            this.config = await response.json();
            this.emitEvent('configLoaded', { config: this.config });

        } catch (error) {
            console.error('Error loading configuration:', error);
            throw error;
        }
    }

    async updateConfiguration(newConfig) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });

            if (!response.ok) throw new Error('Failed to update configuration');

            this.config = await response.json();
            this.emitEvent('configUpdated', { config: this.config });

            if (this.options.enableNotifications) {
                this.showNotification('Auto-snapshot configuration updated', 'success');
            }

            return this.config;

        } catch (error) {
            console.error('Error updating configuration:', error);
            this.showNotification('Failed to update configuration', 'error');
            throw error;
        }
    }

    // Statistics and Monitoring
    async loadStats() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/stats`);
            if (!response.ok) throw new Error('Failed to load stats');

            this.stats = await response.json();
            this.emitEvent('statsLoaded', { stats: this.stats });

        } catch (error) {
            console.error('Error loading stats:', error);
            throw error;
        }
    }

    async loadActiveFloors() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/active-floors`);
            if (!response.ok) throw new Error('Failed to load active floors');

            const data = await response.json();
            this.activeFloors = new Set(data.active_floors);
            this.emitEvent('activeFloorsLoaded', { activeFloors: this.activeFloors });

        } catch (error) {
            console.error('Error loading active floors:', error);
            throw error;
        }
    }

    // Manual Snapshot Creation
    async createManualSnapshot(floorId, options = {}) {
        try {
            const requestData = {
                floor_id: floorId,
                description: options.description || 'Manual snapshot',
                tags: options.tags || [],
                user_id: options.userId,
                session_id: options.sessionId
            };

            const response = await fetch(`${this.options.apiBaseUrl}/create-manual`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) throw new Error('Failed to create manual snapshot');

            const snapshot = await response.json();
            this.emitEvent('manualSnapshotCreated', { snapshot, floorId });

            if (this.options.enableNotifications) {
                this.showNotification('Manual snapshot created successfully', 'success');
            }

            return snapshot;

        } catch (error) {
            console.error('Error creating manual snapshot:', error);
            this.showNotification('Failed to create manual snapshot', 'error');
            throw error;
        }
    }

    // Change Tracking
    async trackChanges(floorId, currentData, options = {}) {
        try {
            const requestData = {
                floor_id: floorId,
                current_data: currentData,
                previous_data: options.previousData,
                user_id: options.userId,
                session_id: options.sessionId
            };

            const response = await fetch(`${this.options.apiBaseUrl}/track-changes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) throw new Error('Failed to track changes');

            const result = await response.json();

            if (result) {
                // Auto-snapshot was created
                this.emitEvent('autoSnapshotCreated', { snapshot: result, floorId });

                if (this.options.enableNotifications) {
                    this.showNotification(`Auto-snapshot created: ${result.description}`, 'info');
                }
            }

            return result;

        } catch (error) {
            console.error('Error tracking changes:', error);
            throw error;
        }
    }

    // Floor Management
    async activateFloor(floorId) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/floors/${floorId}/activate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to activate floor');

            this.activeFloors.add(floorId);
            this.emitEvent('floorActivated', { floorId });

            if (this.options.enableNotifications) {
                this.showNotification(`Auto-snapshot activated for floor ${floorId}`, 'success');
            }

        } catch (error) {
            console.error('Error activating floor:', error);
            this.showNotification('Failed to activate floor', 'error');
            throw error;
        }
    }

    async deactivateFloor(floorId) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/floors/${floorId}/deactivate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to deactivate floor');

            this.activeFloors.delete(floorId);
            this.emitEvent('floorDeactivated', { floorId });

            if (this.options.enableNotifications) {
                this.showNotification(`Auto-snapshot deactivated for floor ${floorId}`, 'info');
            }

        } catch (error) {
            console.error('Error deactivating floor:', error);
            this.showNotification('Failed to deactivate floor', 'error');
            throw error;
        }
    }

    // Snapshot Management
    async getFloorSnapshots(floorId, options = {}) {
        try {
            const params = new URLSearchParams({
                limit: options.limit || 50,
                offset: options.offset || 0
            });

            const response = await fetch(`${this.options.apiBaseUrl}/floors/${floorId}/snapshots?${params}`);
            if (!response.ok) throw new Error('Failed to get floor snapshots');

            return await response.json();

        } catch (error) {
            console.error('Error getting floor snapshots:', error);
            throw error;
        }
    }

    async getFloorActivity(floorId) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/floors/${floorId}/activity`);
            if (!response.ok) throw new Error('Failed to get floor activity');

            return await response.json();

        } catch (error) {
            console.error('Error getting floor activity:', error);
            throw error;
        }
    }

    // Cleanup Operations
    async triggerCleanup(floorId) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/cleanup/${floorId}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to trigger cleanup');

            const result = await response.json();
            this.emitEvent('cleanupTriggered', { floorId, result });

            if (this.options.enableNotifications) {
                this.showNotification(`Cleanup triggered for floor ${floorId}`, 'info');
            }

            return result;

        } catch (error) {
            console.error('Error triggering cleanup:', error);
            this.showNotification('Failed to trigger cleanup', 'error');
            throw error;
        }
    }

    async triggerCleanupAll() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/cleanup/all`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to trigger cleanup for all floors');

            const result = await response.json();
            this.emitEvent('cleanupAllTriggered', { result });

            if (this.options.enableNotifications) {
                this.showNotification(result.message, 'info');
            }

            return result;

        } catch (error) {
            console.error('Error triggering cleanup for all floors:', error);
            this.showNotification('Failed to trigger cleanup', 'error');
            throw error;
        }
    }

    // Real-time Updates
    startRealTimeUpdates() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }

        this.updateTimer = setInterval(async () => {
            try {
                await this.loadStats();
                await this.loadActiveFloors();
                this.emitEvent('statsUpdated', { stats: this.stats, activeFloors: this.activeFloors });
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }, this.options.updateInterval);
    }

    stopRealTimeUpdates() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    // UI Rendering
    renderConfigurationPanel(container) {
        if (!this.config) return;

        container.innerHTML = `
            <div class="auto-snapshot-config-panel">
                <h3 class="text-lg font-semibold mb-4">Auto-Snapshot Configuration</h3>

                <form id="auto-snapshot-config-form" class="space-y-4">
                    <div class="flex items-center">
                        <input type="checkbox" id="config-enabled"
                               ${this.config.enabled ? 'checked' : ''}
                               class="mr-2">
                        <label for="config-enabled" class="text-sm font-medium">
                            Enable Auto-Snapshot
                        </label>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-1">Time Interval (minutes)</label>
                            <input type="number" id="config-time-interval"
                                   value="${this.config.time_interval_minutes}"
                                   min="1" max="1440" class="w-full border rounded px-2 py-1">
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">Change Threshold</label>
                            <input type="number" id="config-change-threshold"
                                   value="${this.config.change_threshold}"
                                   min="1" max="1000" class="w-full border rounded px-2 py-1">
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">Major Edit Threshold</label>
                            <input type="number" id="config-major-edit-threshold"
                                   value="${this.config.major_edit_threshold}"
                                   min="1" max="1000" class="w-full border rounded px-2 py-1">
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">Max Snapshots/Hour</label>
                            <input type="number" id="config-max-hourly"
                                   value="${this.config.max_snapshots_per_hour}"
                                   min="1" max="100" class="w-full border rounded px-2 py-1">
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">Max Snapshots/Day</label>
                            <input type="number" id="config-max-daily"
                                   value="${this.config.max_snapshots_per_day}"
                                   min="1" max="1000" class="w-full border rounded px-2 py-1">
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">Retention (days)</label>
                            <input type="number" id="config-retention"
                                   value="${this.config.retention_days}"
                                   min="1" max="365" class="w-full border rounded px-2 py-1">
                        </div>
                    </div>

                    <div class="flex items-center space-x-4">
                        <div class="flex items-center">
                            <input type="checkbox" id="config-cleanup-enabled"
                                   ${this.config.cleanup_enabled ? 'checked' : ''}
                                   class="mr-2">
                            <label for="config-cleanup-enabled" class="text-sm">
                                Enable Cleanup
                            </label>
                        </div>

                        <div class="flex items-center">
                            <input type="checkbox" id="config-compression-enabled"
                                   ${this.config.compression_enabled ? 'checked' : ''}
                                   class="mr-2">
                            <label for="config-compression-enabled" class="text-sm">
                                Enable Compression
                            </label>
                        </div>

                        <div class="flex items-center">
                            <input type="checkbox" id="config-backup-enabled"
                                   ${this.config.backup_enabled ? 'checked' : ''}
                                   class="mr-2">
                            <label for="config-backup-enabled" class="text-sm">
                                Enable Backup
                            </label>
                        </div>
                    </div>

                    <div class="flex space-x-2">
                        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                            Save Configuration
                        </button>
                        <button type="button" id="reset-config" class="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400">
                            Reset to Defaults
                        </button>
                    </div>
                </form>
            </div>
        `;

        // Add event listeners
        this.addConfigurationEventListeners(container);
    }

    renderStatsPanel(container) {
        if (!this.stats) return;

        container.innerHTML = `
            <div class="auto-snapshot-stats-panel">
                <h3 class="text-lg font-semibold mb-4">Auto-Snapshot Statistics</h3>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-blue-50 p-3 rounded">
                        <div class="text-sm text-blue-600">Service Status</div>
                        <div class="text-lg font-semibold ${this.stats.running ? 'text-green-600' : 'text-red-600'}">
                            ${this.stats.running ? 'Running' : 'Stopped'}
                        </div>
                    </div>

                    <div class="bg-green-50 p-3 rounded">
                        <div class="text-sm text-green-600">Active Floors</div>
                        <div class="text-lg font-semibold text-green-700">
                            ${this.stats.active_floors}
                        </div>
                    </div>

                    <div class="bg-purple-50 p-3 rounded">
                        <div class="text-sm text-purple-600">Total Cleanups</div>
                        <div class="text-lg font-semibold text-purple-700">
                            ${this.stats.cleanup_stats.total_cleanups || 0}
                        </div>
                    </div>

                    <div class="bg-orange-50 p-3 rounded">
                        <div class="text-sm text-orange-600">Snapshots Removed</div>
                        <div class="text-lg font-semibold text-orange-700">
                            ${this.stats.cleanup_stats.total_removed || 0}
                        </div>
                    </div>
                </div>

                <div class="space-y-2">
                    <button id="refresh-stats" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                        Refresh Stats
                    </button>
                    <button id="trigger-cleanup-all" class="bg-orange-600 text-white px-3 py-1 rounded text-sm hover:bg-orange-700">
                        Trigger Cleanup (All Floors)
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        this.addStatsEventListeners(container);
    }

    renderFloorActivityPanel(container, floorId) {
        container.innerHTML = `
            <div class="auto-snapshot-floor-activity-panel">
                <h3 class="text-lg font-semibold mb-4">Floor Activity - ${floorId}</h3>

                <div class="space-y-4">
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center">
                            <input type="checkbox" id="floor-active-${floorId}"
                                   ${this.activeFloors.has(floorId) ? 'checked' : ''}
                                   class="mr-2">
                            <label for="floor-active-${floorId}" class="text-sm font-medium">
                                Auto-Snapshot Active
                            </label>
                        </div>

                        <button id="create-manual-${floorId}" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                            Create Manual Snapshot
                        </button>

                        <button id="trigger-cleanup-${floorId}" class="bg-orange-600 text-white px-3 py-1 rounded text-sm hover:bg-orange-700">
                            Trigger Cleanup
                        </button>
                    </div>

                    <div id="floor-activity-content-${floorId}" class="bg-gray-50 p-3 rounded">
                        <div class="text-sm text-gray-600">Loading activity data...</div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        this.addFloorActivityEventListeners(container, floorId);

        // Load activity data
        this.loadFloorActivityData(floorId);
    }

    // Event Listeners
    addConfigurationEventListeners(container) {
        const form = container.querySelector('#auto-snapshot-config-form');
        const resetBtn = container.querySelector('#reset-config');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const newConfig = {
                enabled: container.querySelector('#config-enabled').checked,
                time_interval_minutes: parseInt(container.querySelector('#config-time-interval').value),
                change_threshold: parseInt(container.querySelector('#config-change-threshold').value),
                major_edit_threshold: parseInt(container.querySelector('#config-major-edit-threshold').value),
                max_snapshots_per_hour: parseInt(container.querySelector('#config-max-hourly').value),
                max_snapshots_per_day: parseInt(container.querySelector('#config-max-daily').value),
                retention_days: parseInt(container.querySelector('#config-retention').value),
                cleanup_enabled: container.querySelector('#config-cleanup-enabled').checked,
                compression_enabled: container.querySelector('#config-compression-enabled').checked,
                backup_enabled: container.querySelector('#config-backup-enabled').checked
            };

            try {
                await this.updateConfiguration(newConfig);
            } catch (error) {
                console.error('Error updating configuration:', error);
            }
        });

        resetBtn.addEventListener('click', async () => {
            try {
                await this.updateConfiguration({
                    enabled: true,
                    time_interval_minutes: 15,
                    change_threshold: 10,
                    major_edit_threshold: 25,
                    max_snapshots_per_hour: 4,
                    max_snapshots_per_day: 24,
                    retention_days: 30,
                    cleanup_enabled: true,
                    compression_enabled: true,
                    backup_enabled: true
                });

                // Reload configuration panel
                this.renderConfigurationPanel(container);
            } catch (error) {
                console.error('Error resetting configuration:', error);
            }
        });
    }

    addStatsEventListeners(container) {
        const refreshBtn = container.querySelector('#refresh-stats');
        const cleanupBtn = container.querySelector('#trigger-cleanup-all');

        refreshBtn.addEventListener('click', async () => {
            try {
                await this.loadStats();
                this.renderStatsPanel(container);
            } catch (error) {
                console.error('Error refreshing stats:', error);
            }
        });

        cleanupBtn.addEventListener('click', async () => {
            try {
                await this.triggerCleanupAll();
            } catch (error) {
                console.error('Error triggering cleanup:', error);
            }
        });
    }

    addFloorActivityEventListeners(container, floorId) {
        const activeCheckbox = container.querySelector(`#floor-active-${floorId}`);
        const manualBtn = container.querySelector(`#create-manual-${floorId}`);
        const cleanupBtn = container.querySelector(`#trigger-cleanup-${floorId}`);

        activeCheckbox.addEventListener('change', async () => {
            try {
                if (activeCheckbox.checked) {
                    await this.activateFloor(floorId);
                } else {
                    await this.deactivateFloor(floorId);
                }
            } catch (error) {
                console.error('Error toggling floor activation:', error);
                // Revert checkbox state
                activeCheckbox.checked = !activeCheckbox.checked;
            }
        });

        manualBtn.addEventListener('click', async () => {
            try {
                const description = prompt('Enter snapshot description (optional):');
                await this.createManualSnapshot(floorId, { description });
            } catch (error) {
                console.error('Error creating manual snapshot:', error);
            }
        });

        cleanupBtn.addEventListener('click', async () => {
            try {
                await this.triggerCleanup(floorId);
            } catch (error) {
                console.error('Error triggering cleanup:', error);
            }
        });
    }

    async loadFloorActivityData(floorId) {
        try {
            const activity = await this.getFloorActivity(floorId);
            const content = document.querySelector(`#floor-activity-content-${floorId}`);

            if (content) {
                content.innerHTML = `
                    <div class="space-y-2">
                        <div class="text-sm">
                            <strong>Total Snapshots:</strong> ${activity.total_snapshots}
                        </div>
                        <div class="text-sm">
                            <strong>Last Activity:</strong> ${activity.activity.last_activity || 'None'}
                        </div>
                        <div class="text-sm">
                            <strong>User ID:</strong> ${activity.activity.user_id || 'None'}
                        </div>
                        <div class="text-sm">
                            <strong>Session ID:</strong> ${activity.activity.session_id || 'None'}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading floor activity data:', error);
        }
    }

    // Event System
    addEventListener(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emitEvent(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // Utility Methods
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-black' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    // Cleanup
    destroy() {
        this.stopRealTimeUpdates();
        this.eventListeners.clear();
        this.isInitialized = false;
    }
}

// Export for use in other modules
window.AutoSnapshotManager = AutoSnapshotManager;
