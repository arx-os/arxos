/**
 * SVG-BIM Markup Layer Service
 *
 * Implements scalable, layered SVG interface for MEP markup editing and view-only browsing.
 * Features:
 * - MEP layer management (E, LV, FA, N, M, P, S)
 * - Edit mode gating with permission-aware front-end
 * - Layer toggles with HTMX + Tailwind panel
 * - Object diff overlay for change review
 * - Optimized symbol loading and snapping logic
 */

class SVGMarkupLayer {
    constructor(options = {}) {
        this.options = {
            enableEditMode: true,
            enableLayerToggles: true,
            enableDiffOverlay: true,
            enableSnapping: true,
            enablePermissionGating: true,
            ...options
        };

        // MEP Layer definitions with color standards
        this.mepLayers = {
            E: {  // Electrical
                name: "Electrical",
                color: "#FF6B35",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Electrical systems, panels, circuits, outlets"
            },
            LV: {  // Low Voltage
                name: "Low Voltage",
                color: "#4ECDC4",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Data, communications, security systems"
            },
            FA: {  // Fire Alarm
                name: "Fire Alarm",
                color: "#FFE66D",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Fire detection and alarm systems"
            },
            N: {  // Network
                name: "Network",
                color: "#95E1D3",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Network infrastructure and connectivity"
            },
            M: {  // Mechanical
                name: "Mechanical",
                color: "#F38181",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "HVAC, ventilation, air handling"
            },
            P: {  // Plumbing
                name: "Plumbing",
                color: "#A8E6CF",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Water supply, drainage, fixtures"
            },
            S: {  // Security
                name: "Security",
                color: "#FF8B94",
                opacity: 0.8,
                visible: true,
                editable: true,
                description: "Access control, surveillance, security"
            }
        };

        // User permissions and roles
        this.userPermissions = {
            canEdit: false,
            canCreate: false,
            canDelete: false,
            canView: true,
            role: 'viewer'
        };

        // Current edit mode state
        this.editMode = {
            active: false,
            currentLayer: null,
            selectedObjects: new Set(),
            clipboard: null
        };

        // Layer visibility state
        this.layerVisibility = {};
        Object.keys(this.mepLayers).forEach(layer => {
            this.layerVisibility[layer] = true;
        });

        // Snapping configuration
        this.snappingConfig = {
            enabled: true,
            tolerance: 10,
            snapToGrid: true,
            gridSize: 20,
            snapToObjects: true,
            snapToLines: true,
            snapToIntersections: true
        };

        // Diff overlay state
        this.diffOverlay = {
            active: false,
            changes: new Map(),
            originalState: new Map(),
            modifiedState: new Map()
        };

        // Event handlers
        this.eventHandlers = new Map();

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the markup layer
     */
    initialize() {
        this.createLayerTogglePanel();
        this.setupEventListeners();
        this.loadUserPermissions();
        this.updateEditMode();
        this.applyLayerVisibility();

        console.log('SVG Markup Layer initialized');
    }

    /**
     * Create layer toggle panel with HTMX + Tailwind
     */
    createLayerTogglePanel() {
        const panel = document.createElement('div');
        panel.id = 'layer-toggle-panel';
        panel.className = 'fixed top-4 right-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50';
        panel.style.minWidth = '280px';

        panel.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-800">MEP Layers</h3>
                <button id="close-layer-panel" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>

            <div class="space-y-3">
                ${Object.entries(this.mepLayers).map(([key, layer]) => `
                    <div class="flex items-center justify-between p-2 rounded border border-gray-200 hover:bg-gray-50">
                        <div class="flex items-center space-x-3">
                            <div class="w-4 h-4 rounded" style="background-color: ${layer.color}; opacity: ${layer.opacity}"></div>
                            <div>
                                <div class="font-medium text-sm text-gray-800">${layer.name}</div>
                                <div class="text-xs text-gray-500">${layer.description}</div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" class="sr-only peer" data-layer="${key}" ${layer.visible ? 'checked' : ''}>
                                <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                            ${layer.editable ? `
                                <button class="edit-layer-btn p-1 text-gray-400 hover:text-blue-600" data-layer="${key}" title="Edit layer">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                                    </svg>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="mt-4 pt-4 border-t border-gray-200">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700">Edit Mode</span>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="sr-only peer" id="edit-mode-toggle" ${this.editMode.active ? 'checked' : ''}>
                        <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>

                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700">Snapping</span>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="sr-only peer" id="snapping-toggle" ${this.snappingConfig.enabled ? 'checked' : ''}>
                        <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>

                <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-700">Diff Overlay</span>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="sr-only peer" id="diff-overlay-toggle" ${this.diffOverlay.active ? 'checked' : ''}>
                        <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>
            </div>
        `;

        document.body.appendChild(panel);
        this.setupLayerToggleEvents();
    }

    /**
     * Setup event listeners for layer toggles
     */
    setupLayerToggleEvents() {
        // Layer visibility toggles
        document.querySelectorAll('[data-layer]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const layer = e.target.dataset.layer;
                const visible = e.target.checked;
                this.toggleLayerVisibility(layer, visible);
            });
        });

        // Edit mode toggle
        const editModeToggle = document.getElementById('edit-mode-toggle');
        if (editModeToggle) {
            editModeToggle.addEventListener('change', (e) => {
                this.setEditMode(e.target.checked);
            });
        }

        // Snapping toggle
        const snappingToggle = document.getElementById('snapping-toggle');
        if (snappingToggle) {
            snappingToggle.addEventListener('change', (e) => {
                this.setSnapping(e.target.checked);
            });
        }

        // Diff overlay toggle
        const diffOverlayToggle = document.getElementById('diff-overlay-toggle');
        if (diffOverlayToggle) {
            diffOverlayToggle.addEventListener('change', (e) => {
                this.setDiffOverlay(e.target.checked);
            });
        }

        // Close panel button
        const closeBtn = document.getElementById('close-layer-panel');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideLayerPanel();
            });
        }

        // Edit layer buttons
        document.querySelectorAll('.edit-layer-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const layer = e.target.closest('button').dataset.layer;
                this.editLayer(layer);
            });
        });
    }

    /**
     * Setup main event listeners
     */
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Mouse events for snapping
        if (this.snappingConfig.enabled) {
            document.addEventListener('mousemove', (e) => {
                this.handleSnapping(e);
            });
        }

        // HTMX events
        document.addEventListener('htmx:afterRequest', (e) => {
            this.handleHTMXEvents(e);
        });
    }

    /**
     * Load user permissions from server
     */
    async loadUserPermissions() {
        try {
            const response = await fetch('/api/user/permissions');
            if (response.ok) {
                this.userPermissions = await response.json();
                this.updateEditMode();
            }
        } catch (error) {
            console.warn('Failed to load user permissions:', error);
        }
    }

    /**
     * Update edit mode based on permissions
     */
    updateEditMode() {
        const canEdit = this.userPermissions.canEdit && this.userPermissions.role !== 'viewer';

        if (!canEdit) {
            this.setEditMode(false);
        }

        // Update UI elements
        const editModeToggle = document.getElementById('edit-mode-toggle');
        if (editModeToggle) {
            editModeToggle.disabled = !canEdit;
            if (!canEdit) {
                editModeToggle.checked = false;
            }
        }
    }

    /**
     * Set edit mode
     */
    setEditMode(active) {
        this.editMode.active = active && this.userPermissions.canEdit;

        // Update UI
        const editModeToggle = document.getElementById('edit-mode-toggle');
        if (editModeToggle) {
            editModeToggle.checked = this.editMode.active;
        }

        // Apply edit mode to SVG elements
        this.applyEditMode();

        // Trigger event
        this.triggerEvent('editModeChanged', { active: this.editMode.active });
    }

    /**
     * Apply edit mode to SVG elements
     */
    applyEditMode() {
        const svgElements = document.querySelectorAll('svg');

        svgElements.forEach(svg => {
            if (this.editMode.active) {
                svg.classList.add('edit-mode');
                svg.style.cursor = 'crosshair';
            } else {
                svg.classList.remove('edit-mode');
                svg.style.cursor = 'default';
            }
        });

        // Update placed symbols
        const placedSymbols = document.querySelectorAll('.placed-symbol');
        placedSymbols.forEach(symbol => {
            if (this.editMode.active) {
                symbol.classList.add('editable');
                symbol.style.cursor = 'pointer';
            } else {
                symbol.classList.remove('editable');
                symbol.style.cursor = 'default';
            }
        });
    }

    /**
     * Toggle layer visibility
     */
    toggleLayerVisibility(layerKey, visible) {
        this.layerVisibility[layerKey] = visible;

        // Update layer elements
        const layerElements = document.querySelectorAll(`[data-layer="${layerKey}"]`);
        layerElements.forEach(element => {
            if (visible) {
                element.style.display = '';
                element.style.opacity = this.mepLayers[layerKey].opacity;
            } else {
                element.style.display = 'none';
            }
        });

        // Trigger event
        this.triggerEvent('layerVisibilityChanged', { layer: layerKey, visible });
    }

    /**
     * Apply layer visibility to all elements
     */
    applyLayerVisibility() {
        Object.entries(this.layerVisibility).forEach(([layer, visible]) => {
            this.toggleLayerVisibility(layer, visible);
        });
    }

    /**
     * Set snapping configuration
     */
    setSnapping(enabled) {
        this.snappingConfig.enabled = enabled;

        // Update UI
        const snappingToggle = document.getElementById('snapping-toggle');
        if (snappingToggle) {
            snappingToggle.checked = enabled;
        }

        // Trigger event
        this.triggerEvent('snappingChanged', { enabled });
    }

    /**
     * Handle snapping during mouse movement
     */
    handleSnapping(event) {
        if (!this.snappingConfig.enabled) return;

        const svgElement = event.target.closest('svg');
        if (!svgElement) return;

        const rect = svgElement.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Calculate snapped position
        const snappedPosition = this.calculateSnappedPosition(x, y);

        // Update cursor position indicator
        this.updateSnapIndicator(snappedPosition);
    }

    /**
     * Calculate snapped position
     */
    calculateSnappedPosition(x, y) {
        let snappedX = x;
        let snappedY = y;

        if (this.snappingConfig.snapToGrid) {
            snappedX = Math.round(x / this.snappingConfig.gridSize) * this.snappingConfig.gridSize;
            snappedY = Math.round(y / this.snappingConfig.gridSize) * this.snappingConfig.gridSize;
        }

        if (this.snappingConfig.snapToObjects) {
            const objectSnap = this.findNearestObject(x, y);
            if (objectSnap && objectSnap.distance < this.snappingConfig.tolerance) {
                snappedX = objectSnap.x;
                snappedY = objectSnap.y;
            }
        }

        return { x: snappedX, y: snappedY };
    }

    /**
     * Find nearest object for snapping
     */
    findNearestObject(x, y) {
        const objects = document.querySelectorAll('.placed-symbol');
        let nearest = null;
        let minDistance = Infinity;

        objects.forEach(obj => {
            const objX = parseFloat(obj.getAttribute('data-x') || 0);
            const objY = parseFloat(obj.getAttribute('data-y') || 0);
            const distance = Math.sqrt((x - objX) ** 2 + (y - objY) ** 2);

            if (distance < minDistance) {
                minDistance = distance;
                nearest = { x: objX, y: objY, distance };
            }
        });

        return nearest;
    }

    /**
     * Update snap indicator
     */
    updateSnapIndicator(position) {
        let indicator = document.getElementById('snap-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'snap-indicator';
            indicator.className = 'absolute w-2 h-2 bg-blue-500 rounded-full pointer-events-none z-50';
            document.body.appendChild(indicator);
        }

        indicator.style.left = `${position.x}px`;
        indicator.style.top = `${position.y}px`;
    }

    /**
     * Set diff overlay mode
     */
    setDiffOverlay(active) {
        this.diffOverlay.active = active;

        // Update UI
        const diffOverlayToggle = document.getElementById('diff-overlay-toggle');
        if (diffOverlayToggle) {
            diffOverlayToggle.checked = active;
        }

        if (active) {
            this.captureOriginalState();
            this.showDiffOverlay();
        } else {
            this.hideDiffOverlay();
        }

        // Trigger event
        this.triggerEvent('diffOverlayChanged', { active });
    }

    /**
     * Capture original state for diff
     */
    captureOriginalState() {
        const objects = document.querySelectorAll('.placed-symbol');
        objects.forEach(obj => {
            const id = obj.getAttribute('data-id');
            if (id) {
                this.diffOverlay.originalState.set(id, {
                    x: parseFloat(obj.getAttribute('data-x') || 0),
                    y: parseFloat(obj.getAttribute('data-y') || 0),
                    rotation: parseFloat(obj.getAttribute('data-rotation') || 0),
                    layer: obj.getAttribute('data-layer'),
                    properties: this.getObjectProperties(obj)
                });
            }
        });
    }

    /**
     * Show diff overlay
     */
    showDiffOverlay() {
        // Create diff overlay elements
        const objects = document.querySelectorAll('.placed-symbol');
        objects.forEach(obj => {
            const id = obj.getAttribute('data-id');
            if (id && this.diffOverlay.originalState.has(id)) {
                const original = this.diffOverlay.originalState.get(id);
                const current = {
                    x: parseFloat(obj.getAttribute('data-x') || 0),
                    y: parseFloat(obj.getAttribute('data-y') || 0),
                    rotation: parseFloat(obj.getAttribute('data-rotation') || 0),
                    layer: obj.getAttribute('data-layer'),
                    properties: this.getObjectProperties(obj)
                };

                // Check for changes
                if (this.hasChanges(original, current)) {
                    this.createDiffIndicator(obj, original, current);
                }
            }
        });
    }

    /**
     * Hide diff overlay
     */
    hideDiffOverlay() {
        const diffIndicators = document.querySelectorAll('.diff-indicator');
        diffIndicators.forEach(indicator => indicator.remove());
    }

    /**
     * Check if object has changes
     */
    hasChanges(original, current) {
        return original.x !== current.x ||
               original.y !== current.y ||
               original.rotation !== current.rotation ||
               original.layer !== current.layer ||
               JSON.stringify(original.properties) !== JSON.stringify(current.properties);
    }

    /**
     * Create diff indicator
     */
    createDiffIndicator(obj, original, current) {
        const indicator = document.createElement('div');
        indicator.className = 'diff-indicator absolute border-2 border-yellow-400 bg-yellow-100 bg-opacity-50 pointer-events-none z-40';
        indicator.style.left = `${Math.min(original.x, current.x)}px`;
        indicator.style.top = `${Math.min(original.y, current.y)}px`;
        indicator.style.width = `${Math.abs(current.x - original.x) + 40}px`;
        indicator.style.height = `${Math.abs(current.y - original.y) + 40}px`;

        obj.parentElement.appendChild(indicator);
    }

    /**
     * Get object properties
     */
    getObjectProperties(obj) {
        const properties = {};
        const dataAttributes = obj.attributes;

        for (let i = 0; i < dataAttributes.length; i++) {
            const attr = dataAttributes[i];
            if (attr.name.startsWith('data-')) {
                properties[attr.name] = attr.value;
            }
        }

        return properties;
    }

    /**
     * Edit layer properties
     */
    editLayer(layerKey) {
        if (!this.userPermissions.canEdit) {
            this.showNotification('Insufficient permissions to edit layers', 'error');
            return;
        }

        const layer = this.mepLayers[layerKey];
        if (!layer) return;

        // Create edit dialog using HTMX
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        dialog.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold mb-4">Edit ${layer.name} Layer</h3>
                <form hx-post="/api/layers/${layerKey}" hx-target="#layer-edit-result">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Name</label>
                            <input type="text" name="name" value="${layer.name}" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Color</label>
                            <input type="color" name="color" value="${layer.color}" class="mt-1 block w-full">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Opacity</label>
                            <input type="range" name="opacity" min="0" max="1" step="0.1" value="${layer.opacity}" class="mt-1 block w-full">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Description</label>
                            <textarea name="description" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">${layer.description}</textarea>
                        </div>
                    </div>
                    <div class="mt-6 flex justify-end space-x-3">
                        <button type="button" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50" onclick="this.closest('.fixed').remove()">Cancel</button>
                        <button type="submit" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700">Save</button>
                    </div>
                </form>
                <div id="layer-edit-result"></div>
            </div>
        `;

        document.body.appendChild(dialog);
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Layer visibility shortcuts
        Object.keys(this.mepLayers).forEach((layer, index) => {
            if (event.key === (index + 1).toString()) {
                event.preventDefault();
                this.toggleLayerVisibility(layer, !this.layerVisibility[layer]);
            }
        });

        // Edit mode toggle
        if (event.key === 'e' && event.ctrlKey) {
            event.preventDefault();
            this.setEditMode(!this.editMode.active);
        }

        // Snapping toggle
        if (event.key === 's' && event.ctrlKey) {
            event.preventDefault();
            this.setSnapping(!this.snappingConfig.enabled);
        }

        // Diff overlay toggle
        if (event.key === 'd' && event.ctrlKey) {
            event.preventDefault();
            this.setDiffOverlay(!this.diffOverlay.active);
        }
    }

    /**
     * Handle HTMX events
     */
    handleHTMXEvents(event) {
        if (event.detail.xhr.responseURL.includes('/api/layers/')) {
            // Layer edit completed
            this.refreshLayerPanel();
        }
    }

    /**
     * Refresh layer panel
     */
    refreshLayerPanel() {
        // Recreate layer panel with updated data
        const panel = document.getElementById('layer-toggle-panel');
        if (panel) {
            panel.remove();
        }
        this.createLayerTogglePanel();
    }

    /**
     * Show/hide layer panel
     */
    showLayerPanel() {
        const panel = document.getElementById('layer-toggle-panel');
        if (panel) {
            panel.style.display = 'block';
        }
    }

    hideLayerPanel() {
        const panel = document.getElementById('layer-toggle-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * Trigger custom event
     */
    triggerEvent(eventName, data) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }

    /**
     * Add event listener
     */
    addEventListener(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, []);
        }
        this.eventHandlers.get(eventName).push(handler);
        document.addEventListener(eventName, handler);
    }

    /**
     * Remove event listener
     */
    removeEventListener(eventName, handler) {
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
        document.removeEventListener(eventName, handler);
    }

    /**
     * Get current layer state
     */
    getLayerState() {
        return {
            visibility: this.layerVisibility,
            editMode: this.editMode.active,
            snapping: this.snappingConfig.enabled,
            diffOverlay: this.diffOverlay.active
        };
    }

    /**
     * Export layer configuration
     */
    exportLayerConfig() {
        return {
            layers: this.mepLayers,
            visibility: this.layerVisibility,
            snapping: this.snappingConfig,
            userPermissions: this.userPermissions
        };
    }

    /**
     * Import layer configuration
     */
    importLayerConfig(config) {
        if (config.layers) {
            this.mepLayers = { ...this.mepLayers, ...config.layers };
        }
        if (config.visibility) {
            this.layerVisibility = { ...this.layerVisibility, ...config.visibility };
        }
        if (config.snapping) {
            this.snappingConfig = { ...this.snappingConfig, ...config.snapping };
        }
        if (config.userPermissions) {
            this.userPermissions = { ...this.userPermissions, ...config.userPermissions };
        }

        this.refreshLayerPanel();
        this.applyLayerVisibility();
        this.updateEditMode();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SVGMarkupLayer;
}
