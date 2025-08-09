/**
 * Deep Link Router
 * Handles URL parameter parsing, object navigation, and access control for CMMS integration
 */

export class DeepLinkRouter {
    constructor(options = {}) {
        this.options = {
            enableHighlighting: options.enableHighlighting !== false,
            enableZooming: options.enableZooming !== false,
            highlightDuration: options.highlightDuration || 5000,
            zoomLevel: options.zoomLevel || 1.5,
            ...options
        };

        // Navigation state
        this.currentObject = null;
        this.navigationHistory = [];
        this.isNavigating = false;

        // URL parameters
        this.supportedParams = ['building_id', 'floor_id', 'object_id', 'view', 'highlight', 'zoom'];

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.parseCurrentURL();
    }

    setupEventListeners() {
        // Listen for URL changes
        window.addEventListener('popstate', () => {
            this.handleURLChange();
        });

        // Listen for hash changes
        window.addEventListener('hashchange', () => {
            this.handleURLChange();
        });

        // Listen for object selection
        document.addEventListener('objectSelected', (event) => {
            this.handleObjectSelection(event.detail);
        });
    }

    // URL parsing and validation
    parseCurrentURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};

        // Extract supported parameters
        this.supportedParams.forEach(param => {
            const value = urlParams.get(param);
            if (value) {
                params[param] = value;
            }
        });

        // Handle deep link navigation
        if (params.building_id && params.object_id) {
            this.navigateToObject(params);
        }
    }

    handleURLChange() {
        this.parseCurrentURL();
    }

    // Object navigation
    async navigateToObject(params) {
        if (this.isNavigating) return;

        this.isNavigating = true;
        this.triggerEvent('navigationStarted', { params });

        try {
            // Validate parameters
            const validationResult = await this.validateNavigationParams(params);
            if (!validationResult.valid) {
                throw new Error(validationResult.error);
            }

            // Check access permissions
            const accessResult = await this.checkAccessPermissions(params);
            if (!accessResult.granted) {
                throw new Error('Access denied');
            }

            // Navigate to building and floor
            await this.navigateToBuilding(params.building_id);
            await this.navigateToFloor(params.floor_id);

            // Navigate to object
            await this.navigateToSpecificObject(params.object_id);

            // Apply view options
            if (params.view) {
                await this.applyViewOptions(params.view);
            }

            // Apply highlighting
            if (params.highlight !== 'false' && this.options.enableHighlighting) {
                await this.highlightObject(params.object_id);
            }

            // Apply zooming
            if (params.zoom !== 'false' && this.options.enableZooming) {
                await this.zoomToObject(params.object_id);
            }

            // Update navigation history
            this.updateNavigationHistory(params);

            this.triggerEvent('navigationCompleted', {
                params,
                object: this.currentObject
            });

        } catch (error) {
            console.error('Navigation failed:', error);
            this.triggerEvent('navigationFailed', { params, error });
        } finally {
            this.isNavigating = false;
            this.triggerEvent('navigationEnded');
        }
    }

    // Parameter validation
    async validateNavigationParams(params) {
        const errors = [];

        // Required parameters
        if (!params.building_id) {
            errors.push('building_id is required');
        }

        if (!params.object_id) {
            errors.push('object_id is required');
        }

        // Validate building exists
        if (params.building_id) {
            const buildingExists = await this.validateBuilding(params.building_id);
            if (!buildingExists) {
                errors.push(`Building '${params.building_id}' not found`);
            }
        }

        // Validate floor exists
        if (params.floor_id) {
            const floorExists = await this.validateFloor(params.building_id, params.floor_id);
            if (!floorExists) {
                errors.push(`Floor '${params.floor_id}' not found in building '${params.building_id}'`);
            }
        }

        // Validate object exists
        if (params.object_id) {
            const objectExists = await this.validateObject(params.object_id);
            if (!objectExists) {
                errors.push(`Object '${params.object_id}' not found`);
            }
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    async validateBuilding(buildingId) {
        try {
            const response = await fetch(`/api/buildings/${buildingId}`, {
                headers: this.getAuthHeaders()
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async validateFloor(buildingId, floorId) {
        try {
            const response = await fetch(`/api/buildings/${buildingId}/floors/${floorId}`, {
                headers: this.getAuthHeaders()
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async validateObject(objectId) {
        try {
            const response = await fetch(`/api/objects/${objectId}`, {
                headers: this.getAuthHeaders()
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Access control
    async checkAccessPermissions(params) {
        try {
            const response = await fetch('/api/access/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({
                    building_id: params.building_id,
                    floor_id: params.floor_id,
                    object_id: params.object_id,
                    access_type: 'deep_link'
                })
            });

            if (!response.ok) {
                return { granted: false, reason: 'Access denied' };
            }

            const result = await response.json();
            return { granted: result.granted, reason: result.reason };

        } catch (error) {
            console.error('Access check failed:', error);
            return { granted: false, reason: 'Access check failed' };
        }
    }

    // Navigation methods
    async navigateToBuilding(buildingId) {
        // Trigger building selection event
        this.triggerEvent('buildingSelected', { buildingId });

        // Wait for building to load
        await this.waitForBuildingLoad(buildingId);
    }

    async navigateToFloor(floorId) {
        // Trigger floor selection event
        this.triggerEvent('floorSelected', { floorId });

        // Wait for floor to load
        await this.waitForFloorLoad(floorId);
    }

    async navigateToSpecificObject(objectId) {
        // Get object details
        const object = await this.getObjectDetails(objectId);
        if (!object) {
            throw new Error(`Object '${objectId}' not found`);
        }

        this.currentObject = object;

        // Trigger object selection event
        this.triggerEvent('objectSelected', { object });

        // Wait for object to be available in viewer
        await this.waitForObjectLoad(objectId);
    }

    async applyViewOptions(viewOptions) {
        const options = typeof viewOptions === 'string' ?
            JSON.parse(viewOptions) : viewOptions;

        // Apply view settings
        if (options.zoom) {
            await this.setZoomLevel(options.zoom);
        }

        if (options.pan) {
            await this.setPanPosition(options.pan);
        }

        if (options.rotation) {
            await this.setRotation(options.rotation);
        }

        this.triggerEvent('viewOptionsApplied', { options });
    }

    async highlightObject(objectId) {
        // Highlight object in viewer
        this.triggerEvent('objectHighlight', {
            objectId,
            duration: this.options.highlightDuration
        });

        // Remove highlight after duration
        setTimeout(() => {
            this.triggerEvent('objectHighlightEnd', { objectId });
        }, this.options.highlightDuration);
    }

    async zoomToObject(objectId) {
        // Get object coordinates
        const object = await this.getObjectDetails(objectId);
        if (!object || !object.spatial_coordinates) {
            return;
        }

        // Calculate zoom target
        const target = this.calculateZoomTarget(object.spatial_coordinates);

        // Trigger zoom to object
        this.triggerEvent('zoomToObject', {
            objectId,
            target,
            zoomLevel: this.options.zoomLevel
        });
    }

    // Utility methods
    async getObjectDetails(objectId) {
        try {
            const response = await fetch(`/api/objects/${objectId}`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                return null;
            }

            return await response.json();

        } catch (error) {
            console.error('Failed to get object details:', error);
            return null;
        }
    }

    calculateZoomTarget(coordinates) {
        // Calculate center point of object
        if (coordinates.bounds) {
            const { x1, y1, x2, y2 } = coordinates.bounds;
            return {
                x: (x1 + x2) / 2,
                y: (y1 + y2) / 2
            };
        }

        // Use center point if available
        if (coordinates.center) {
            return coordinates.center;
        }

        // Use position if available
        if (coordinates.position) {
            return coordinates.position;
        }

        return null;
    }

    async waitForBuildingLoad(buildingId) {
        return new Promise((resolve) => {
            const checkBuilding = () => {
                if (window.currentBuilding && window.currentBuilding.id === buildingId) {
                    resolve();
                } else {
                    setTimeout(checkBuilding, 100);
                }
            };
            checkBuilding();
        });
    }

    async waitForFloorLoad(floorId) {
        return new Promise((resolve) => {
            const checkFloor = () => {
                if (window.currentFloor && window.currentFloor.id === floorId) {
                    resolve();
                } else {
                    setTimeout(checkFloor, 100);
                }
            };
            checkFloor();
        });
    }

    async waitForObjectLoad(objectId) {
        return new Promise((resolve) => {
            const checkObject = () => {
                const object = document.querySelector(`[data-object-id="${objectId}"]`);
                if (object) {
                    resolve();
                } else {
                    setTimeout(checkObject, 100);
                }
            };
            checkObject();
        });
    }

    // URL management
    updateURL(params) {
        const url = new URL(window.location);

        // Clear existing parameters
        this.supportedParams.forEach(param => {
            url.searchParams.delete(param);
        });

        // Add new parameters
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.set(key, value);
            }
        });

        // Update URL without reloading
        window.history.pushState({}, '', url);
    }

    generateDeepLink(params) {
        const url = new URL(window.location.origin + window.location.pathname);

        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.set(key, value);
            }
        });

        return url.toString();
    }

    // Navigation history
    updateNavigationHistory(params) {
        this.navigationHistory.push({
            params: { ...params },
            timestamp: Date.now()
        });

        // Keep only last 10 entries
        if (this.navigationHistory.length > 10) {
            this.navigationHistory.shift();
        }

        this.triggerEvent('navigationHistoryUpdated', {
            history: this.navigationHistory
        });
    }

    getNavigationHistory() {
        return [...this.navigationHistory];
    }

    // Event handlers
    handleObjectSelection(detail) {
        const { object } = detail;
        this.currentObject = object;

        // Update URL with object information
        this.updateURL({
            building_id: object.building_id,
            floor_id: object.floor_id,
            object_id: object.id
        });
    }

    // Public API methods
    async navigateToObjectById(objectId, options = {}) {
        const object = await this.getObjectDetails(objectId);
        if (!object) {
            throw new Error(`Object '${objectId}' not found`);
        }

        const params = {
            building_id: object.building_id,
            floor_id: object.floor_id,
            object_id: object.id,
            ...options
        };

        return this.navigateToObject(params);
    }

    getCurrentObject() {
        return this.currentObject;
    }

    isNavigating() {
        return this.isNavigating;
    }

    // Utility methods
    getAuthHeaders() {
        const token = localStorage.getItem('arx_jwt');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
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
                    handler({ ...data, router: this });
                } catch (error) {
                    console.error(`Error in deep link router event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.currentObject = null;
        this.navigationHistory = [];

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
