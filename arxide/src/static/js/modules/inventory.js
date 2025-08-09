/**
 * Inventory Module
 * Handles asset inventory management, loading, and basic operations
 */

export class Inventory {
    constructor(options = {}) {
        this.options = {
            pageSize: options.pageSize || 20,
            defaultSortField: options.defaultSortField || 'id',
            defaultSortAsc: options.defaultSortAsc !== false,
            enableLogging: options.enableLogging !== false,
            ...options
        };

        // Inventory state
        this.assets = [];
        this.currentPage = 1;
        this.sortField = this.options.defaultSortField;
        this.sortAsc = this.options.defaultSortAsc;
        this.isLoading = false;

        // Filters
        this.filters = {
            building: '',
            system: '',
            assetType: '',
            room: '',
            status: ''
        };

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for filter changes
        document.addEventListener('filterChanged', (event) => {
            this.handleFilterChange(event.detail);
        });

        // Listen for sort changes
        document.addEventListener('sortChanged', (event) => {
            this.handleSortChange(event.detail);
        });

        // Listen for page changes
        document.addEventListener('pageChanged', (event) => {
            this.handlePageChange(event.detail);
        });
    }

    // Asset loading methods
    async loadAssets() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.triggerEvent('loadingStarted');

        try {
            const startTime = performance.now();
            const url = this.buildAssetUrl();

            this.logInfo('Loading assets', {
                building_id: this.filters.building,
                filters: this.filters,
                url: url
            });

            const response = await fetch(url, {
                headers: this.getAuthHeaders()
            });

            const duration = performance.now() - startTime;
            this.logApiRequest('GET', url, response.status, duration);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.assets = data;
            this.currentPage = 1;

            this.logBusinessEvent('asset_inventory', 'assets_loaded', {
                asset_count: data.length,
                building_id: this.filters.building,
                filters: this.filters,
                page_size: this.options.pageSize
            });

            this.triggerEvent('assetsLoaded', {
                assets: this.assets,
                count: this.assets.length
            });

        } catch (error) {
            this.logError('Failed to load assets', {
                building_id: this.filters.building,
                filters: this.filters,
                error: error.message
            });

            this.triggerEvent('assetsLoadFailed', { error });
        } finally {
            this.isLoading = false;
            this.triggerEvent('loadingCompleted');
        }
    }

    buildAssetUrl() {
        const baseUrl = `/api/buildings/${this.filters.building}/assets`;
        const params = new URLSearchParams();

        if (this.filters.system) params.append('system', this.filters.system);
        if (this.filters.assetType) params.append('assetType', this.filters.assetType);
        if (this.filters.room) params.append('roomId', this.filters.room);
        if (this.filters.status) params.append('status', this.filters.status);

        const queryString = params.toString();
        return queryString ? `${baseUrl}?${queryString}` : baseUrl;
    }

    getAuthHeaders() {
        const token = localStorage.getItem('arx_jwt');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    // Asset operations
    async getAsset(assetId) {
        try {
            const response = await fetch(`/api/assets/${assetId}`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const asset = await response.json();
            this.triggerEvent('assetLoaded', { asset });
            return asset;

        } catch (error) {
            this.logError('Failed to load asset', { assetId, error: error.message });
            this.triggerEvent('assetLoadFailed', { assetId, error });
            throw error;
        }
    }

    async createAsset(assetData) {
        try {
            const response = await fetch('/api/assets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(assetData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const asset = await response.json();
            this.assets.push(asset);

            this.logBusinessEvent('asset_inventory', 'asset_created', {
                asset_id: asset.id,
                asset_type: asset.asset_type
            });

            this.triggerEvent('assetCreated', { asset });
            return asset;

        } catch (error) {
            this.logError('Failed to create asset', { assetData, error: error.message });
            this.triggerEvent('assetCreateFailed', { assetData, error });
            throw error;
        }
    }

    async updateAsset(assetId, assetData) {
        try {
            const response = await fetch(`/api/assets/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(assetData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const asset = await response.json();

            // Update asset in local array
            const index = this.assets.findIndex(a => a.id === assetId);
            if (index !== -1) {
                this.assets[index] = asset;
            }

            this.logBusinessEvent('asset_inventory', 'asset_updated', {
                asset_id: assetId,
                asset_type: asset.asset_type
            });

            this.triggerEvent('assetUpdated', { asset });
            return asset;

        } catch (error) {
            this.logError('Failed to update asset', { assetId, assetData, error: error.message });
            this.triggerEvent('assetUpdateFailed', { assetId, assetData, error });
            throw error;
        }
    }

    async deleteAsset(assetId) {
        try {
            const response = await fetch(`/api/assets/${assetId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Remove asset from local array
            this.assets = this.assets.filter(a => a.id !== assetId);

            this.logBusinessEvent('asset_inventory', 'asset_deleted', {
                asset_id: assetId
            });

            this.triggerEvent('assetDeleted', { assetId });

        } catch (error) {
            this.logError('Failed to delete asset', { assetId, error: error.message });
            this.triggerEvent('assetDeleteFailed', { assetId, error });
            throw error;
        }
    }

    async deleteSelectedAssets(assetIds) {
        try {
            const response = await fetch('/api/assets/bulk-delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ asset_ids: assetIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Remove assets from local array
            this.assets = this.assets.filter(a => !assetIds.includes(a.id));

            this.logBusinessEvent('asset_inventory', 'assets_bulk_deleted', {
                asset_count: assetIds.length,
                asset_ids: assetIds
            });

            this.triggerEvent('assetsBulkDeleted', { assetIds });

        } catch (error) {
            this.logError('Failed to delete assets', { assetIds, error: error.message });
            this.triggerEvent('assetsBulkDeleteFailed', { assetIds, error });
            throw error;
        }
    }

    // Sorting and pagination
    sortAssets(field) {
        if (this.sortField === field) {
            this.sortAsc = !this.sortAsc;
        } else {
            this.sortField = field;
            this.sortAsc = true;
        }

        this.triggerEvent('sortChanged', { field: this.sortField, asc: this.sortAsc });
    }

    getSortedAssets() {
        const sorted = [...this.assets];
        sorted.sort((a, b) => {
            let v1 = a[this.sortField], v2 = b[this.sortField];

            // Handle null/undefined values
            if (v1 == null && v2 == null) return 0;
            if (v1 == null) return this.sortAsc ? -1 : 1;
            if (v2 == null) return this.sortAsc ? 1 : -1;

            // Handle string values
            if (typeof v1 === 'string') v1 = v1.toLowerCase();
            if (typeof v2 === 'string') v2 = v2.toLowerCase();

            if (v1 < v2) return this.sortAsc ? -1 : 1;
            if (v1 > v2) return this.sortAsc ? 1 : -1;
            return 0;
        });

        return sorted;
    }

    getPaginatedAssets() {
        const sorted = this.getSortedAssets();
        const start = (this.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        return sorted.slice(start, end);
    }

    getTotalPages() {
        return Math.ceil(this.assets.length / this.options.pageSize);
    }

    goToPage(page) {
        const totalPages = this.getTotalPages();
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.triggerEvent('pageChanged', { page: this.currentPage, totalPages });
        }
    }

    nextPage() {
        this.goToPage(this.currentPage + 1);
    }

    prevPage() {
        this.goToPage(this.currentPage - 1);
    }

    // Filter handling
    setFilter(filterName, value) {
        this.filters[filterName] = value;
        this.currentPage = 1; // Reset to first page when filters change
        this.triggerEvent('filterChanged', { filterName, value, filters: this.filters });
    }

    clearFilters() {
        this.filters = {
            building: '',
            system: '',
            assetType: '',
            room: '',
            status: ''
        };
        this.currentPage = 1;
        this.triggerEvent('filtersCleared', { filters: this.filters });
    }

    // Event handlers
    handleFilterChange(detail) {
        const { filterName, value } = detail;
        this.setFilter(filterName, value);
    }

    handleSortChange(detail) {
        const { field, asc } = detail;
        this.sortField = field;
        this.sortAsc = asc;
    }

    handlePageChange(detail) {
        const { page } = detail;
        this.currentPage = page;
    }

    // Utility methods
    getAssetById(assetId) {
        return this.assets.find(asset => asset.id === assetId);
    }

    getAssetsByType(assetType) {
        return this.assets.filter(asset => asset.asset_type === assetType);
    }

    getAssetsBySystem(system) {
        return this.assets.filter(asset => asset.system === system);
    }

    getAssetsByStatus(status) {
        return this.assets.filter(asset => asset.status === status);
    }

    getAssetCount() {
        return this.assets.length;
    }

    getAssetTypes() {
        return [...new Set(this.assets.map(asset => asset.asset_type))];
    }

    getSystems() {
        return [...new Set(this.assets.map(asset => asset.system))];
    }

    getStatuses() {
        return [...new Set(this.assets.map(asset => asset.status))];
    }

    // Logging methods
    logInfo(message, data = {}) {
        if (this.options.enableLogging && window.arxLogger) {
            window.arxLogger.info(message, data);
        }
    }

    logError(message, data = {}) {
        if (this.options.enableLogging && window.arxLogger) {
            window.arxLogger.error(message, data);
        }
    }

    logApiRequest(method, url, status, duration) {
        if (this.options.enableLogging && window.arxLogger) {
            window.arxLogger.apiRequest(method, url, status, duration);
        }
    }

    logBusinessEvent(category, action, data = {}) {
        if (this.options.enableLogging && window.arxLogger) {
            window.arxLogger.businessEvent(category, action, data);
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
                    handler({ ...data, inventory: this });
                } catch (error) {
                    console.error(`Error in inventory event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.assets = [];
        this.currentPage = 1;
        this.filters = {};

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
