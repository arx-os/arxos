/**
 * Asset Inventory Manager
 * Orchestrates inventory, search, categories, and metadata modules for asset management
 */

import { Inventory } from './inventory.js';
import { Search } from './search.js';
import { Categories } from './categories.js';
import { Metadata } from './metadata.js';

export class AssetInventoryManager {
    constructor(options = {}) {
        this.options = {
            enableCharts: options.enableCharts !== false,
            enableExport: options.enableExport !== false,
            enableBulkOperations: options.enableBulkOperations !== false,
            ...options
        };
        
        // Initialize modules
        this.inventory = new Inventory(options);
        this.search = new Search(options);
        this.categories = new Categories(options);
        this.metadata = new Metadata(options);
        
        // Connect modules
        this.connectModules();
        
        // UI state
        this.selectedAssets = new Set();
        this.isLoading = false;
        
        // UI elements
        this.assetModal = null;
        this.exportModal = null;
        this.charts = {};
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createUI();
    }

    connectModules() {
        // Connect inventory events
        this.inventory.addEventListener('assetsLoaded', (data) => {
            this.handleAssetsLoaded(data);
        });
        
        this.inventory.addEventListener('assetCreated', (data) => {
            this.handleAssetCreated(data);
        });
        
        this.inventory.addEventListener('assetUpdated', (data) => {
            this.handleAssetUpdated(data);
        });
        
        this.inventory.addEventListener('assetDeleted', (data) => {
            this.handleAssetDeleted(data);
        });
        
        // Connect search events
        this.search.addEventListener('searchCompleted', (data) => {
            this.handleSearchCompleted(data);
        });
        
        this.search.addEventListener('advancedSearchCompleted', (data) => {
            this.handleAdvancedSearchCompleted(data);
        });
        
        // Connect categories events
        this.categories.addEventListener('categoriesLoaded', (data) => {
            this.handleCategoriesLoaded(data);
        });
        
        this.categories.addEventListener('categorySelected', (data) => {
            this.handleCategorySelected(data);
        });
        
        // Connect metadata events
        this.metadata.addEventListener('metadataLoaded', (data) => {
            this.handleMetadataLoaded(data);
        });
        
        this.metadata.addEventListener('metadataUpdated', (data) => {
            this.handleMetadataUpdated(data);
        });
    }

    setupEventListeners() {
        // Listen for asset selection changes
        document.addEventListener('assetSelected', (event) => {
            this.handleAssetSelection(event.detail);
        });
        
        // Listen for bulk operations
        document.addEventListener('bulkOperationRequested', (event) => {
            this.handleBulkOperation(event.detail);
        });
        
        // Listen for export requests
        document.addEventListener('exportRequested', (event) => {
            this.handleExportRequest(event.detail);
        });
    }

    // Asset management methods
    async loadAssets() {
        this.isLoading = true;
        this.triggerEvent('loadingStarted');
        
        try {
            await this.inventory.loadAssets();
            await this.categories.loadCategories();
            
            this.updateSummaryCards();
            this.renderCharts();
            
        } catch (error) {
            console.error('Failed to load assets:', error);
            this.triggerEvent('loadingFailed', { error });
        } finally {
            this.isLoading = false;
            this.triggerEvent('loadingCompleted');
        }
    }

    async createAsset(assetData) {
        try {
            const asset = await this.inventory.createAsset(assetData);
            
            // Create metadata if template exists
            if (asset.asset_type) {
                const metadata = this.metadata.createMetadataFromTemplate(asset.asset_type);
                await this.metadata.updateAssetMetadata(asset.id, metadata);
            }
            
            this.updateSummaryCards();
            this.renderCharts();
            
            return asset;
            
        } catch (error) {
            console.error('Failed to create asset:', error);
            throw error;
        }
    }

    async updateAsset(assetId, assetData) {
        try {
            const asset = await this.inventory.updateAsset(assetId, assetData);
            this.updateSummaryCards();
            this.renderCharts();
            return asset;
            
        } catch (error) {
            console.error('Failed to update asset:', error);
            throw error;
        }
    }

    async deleteAsset(assetId) {
        try {
            await this.inventory.deleteAsset(assetId);
            await this.metadata.deleteAssetMetadata(assetId);
            
            this.selectedAssets.delete(assetId);
            this.updateSummaryCards();
            this.renderCharts();
            
        } catch (error) {
            console.error('Failed to delete asset:', error);
            throw error;
        }
    }

    // Search methods
    async searchAssets(query, options = {}) {
        return await this.search.search(query, options);
    }

    async advancedSearch(filters, options = {}) {
        return await this.search.advancedSearch(filters, options);
    }

    // Category methods
    async createCategory(categoryData) {
        return await this.categories.createCategory(categoryData);
    }

    async updateCategory(categoryId, categoryData) {
        return await this.categories.updateCategory(categoryId, categoryData);
    }

    async deleteCategory(categoryId) {
        return await this.categories.deleteCategory(categoryId);
    }

    // Metadata methods
    async getAssetMetadata(assetId) {
        return await this.metadata.getAssetMetadata(assetId);
    }

    async updateAssetMetadata(assetId, metadata) {
        return await this.metadata.updateAssetMetadata(assetId, metadata);
    }

    // Bulk operations
    async deleteSelectedAssets() {
        if (this.selectedAssets.size === 0) return;
        
        try {
            const assetIds = Array.from(this.selectedAssets);
            await this.inventory.deleteSelectedAssets(assetIds);
            
            // Clear selection
            this.selectedAssets.clear();
            this.updateSummaryCards();
            this.renderCharts();
            
            this.triggerEvent('bulkDeleteCompleted', { assetIds });
            
        } catch (error) {
            console.error('Failed to delete selected assets:', error);
            this.triggerEvent('bulkDeleteFailed', { error });
            throw error;
        }
    }

    async exportSelectedAssets(format = 'csv') {
        if (this.selectedAssets.size === 0) return;
        
        try {
            const assetIds = Array.from(this.selectedAssets);
            const assets = assetIds.map(id => this.inventory.getAssetById(id)).filter(Boolean);
            
            const exportData = {
                assets: assets,
                format: format,
                timestamp: new Date().toISOString()
            };
            
            const response = await fetch('/api/assets/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(exportData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `asset_export_${Date.now()}.${format}`;
            a.click();
            
            URL.revokeObjectURL(url);
            
            this.triggerEvent('exportCompleted', { assetIds, format });
            
        } catch (error) {
            console.error('Failed to export assets:', error);
            this.triggerEvent('exportFailed', { error });
            throw error;
        }
    }

    // Asset selection
    selectAsset(assetId) {
        this.selectedAssets.add(assetId);
        this.triggerEvent('assetSelected', { assetId, selected: true });
    }

    deselectAsset(assetId) {
        this.selectedAssets.delete(assetId);
        this.triggerEvent('assetSelected', { assetId, selected: false });
    }

    toggleAssetSelection(assetId) {
        if (this.selectedAssets.has(assetId)) {
            this.deselectAsset(assetId);
        } else {
            this.selectAsset(assetId);
        }
    }

    selectAllAssets() {
        const assets = this.inventory.getPaginatedAssets();
        assets.forEach(asset => {
            this.selectedAssets.add(asset.id);
        });
        this.triggerEvent('allAssetsSelected', { count: assets.length });
    }

    deselectAllAssets() {
        this.selectedAssets.clear();
        this.triggerEvent('allAssetsDeselected');
    }

    getSelectedAssets() {
        return Array.from(this.selectedAssets);
    }

    getSelectedAssetsCount() {
        return this.selectedAssets.size;
    }

    // Event handlers
    handleAssetsLoaded(data) {
        this.triggerEvent('assetsLoaded', data);
    }

    handleAssetCreated(data) {
        this.triggerEvent('assetCreated', data);
    }

    handleAssetUpdated(data) {
        this.triggerEvent('assetUpdated', data);
    }

    handleAssetDeleted(data) {
        this.triggerEvent('assetDeleted', data);
    }

    handleSearchCompleted(data) {
        this.triggerEvent('searchCompleted', data);
    }

    handleAdvancedSearchCompleted(data) {
        this.triggerEvent('advancedSearchCompleted', data);
    }

    handleCategoriesLoaded(data) {
        this.triggerEvent('categoriesLoaded', data);
    }

    handleCategorySelected(data) {
        this.triggerEvent('categorySelected', data);
    }

    handleMetadataLoaded(data) {
        this.triggerEvent('metadataLoaded', data);
    }

    handleMetadataUpdated(data) {
        this.triggerEvent('metadataUpdated', data);
    }

    handleAssetSelection(detail) {
        const { assetId, selected } = detail;
        if (selected) {
            this.selectAsset(assetId);
        } else {
            this.deselectAsset(assetId);
        }
    }

    handleBulkOperation(detail) {
        const { operation, assetIds } = detail;
        
        switch (operation) {
            case 'delete':
                this.deleteSelectedAssets();
                break;
            case 'export':
                this.exportSelectedAssets();
                break;
            default:
                console.warn('Unknown bulk operation:', operation);
        }
    }

    handleExportRequest(detail) {
        const { format, assetIds } = detail;
        if (assetIds && assetIds.length > 0) {
            // Export specific assets
            this.exportAssets(assetIds, format);
        } else {
            // Export selected assets
            this.exportSelectedAssets(format);
        }
    }

    // UI methods
    createUI() {
        this.createAssetModal();
        this.createExportModal();
    }

    createAssetModal() {
        this.assetModal = document.createElement('div');
        this.assetModal.id = 'asset-modal';
        this.assetModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.assetModal.style.display = 'none';
        
        this.assetModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-900">Asset Details</h3>
                    <button id="close-asset-modal" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="asset-modal-content">
                    <!-- Asset form will be populated here -->
                </div>
            </div>
        `;
        
        document.body.appendChild(this.assetModal);
        this.setupAssetModalEvents();
    }

    createExportModal() {
        this.exportModal = document.createElement('div');
        this.exportModal.id = 'export-modal';
        this.exportModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.exportModal.style.display = 'none';
        
        this.exportModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-900">Export Assets</h3>
                    <button id="close-export-modal" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Format</label>
                        <select id="export-format" class="w-full border border-gray-300 rounded-md px-3 py-2">
                            <option value="csv">CSV</option>
                            <option value="json">JSON</option>
                            <option value="xlsx">Excel</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Include</label>
                        <div class="space-y-2">
                            <label class="flex items-center">
                                <input type="checkbox" id="include-metadata" class="mr-2" checked>
                                <span class="text-sm text-gray-700">Metadata</span>
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" id="include-categories" class="mr-2" checked>
                                <span class="text-sm text-gray-700">Categories</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="mt-6 flex space-x-2">
                    <button id="export-confirm" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                        Export
                    </button>
                    <button id="export-cancel" class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.exportModal);
        this.setupExportModalEvents();
    }

    setupAssetModalEvents() {
        const closeButton = this.assetModal.querySelector('#close-asset-modal');
        closeButton.addEventListener('click', () => {
            this.closeAssetModal();
        });
    }

    setupExportModalEvents() {
        const closeButton = this.exportModal.querySelector('#close-export-modal');
        const cancelButton = this.exportModal.querySelector('#export-cancel');
        const confirmButton = this.exportModal.querySelector('#export-confirm');
        
        closeButton.addEventListener('click', () => {
            this.closeExportModal();
        });
        
        cancelButton.addEventListener('click', () => {
            this.closeExportModal();
        });
        
        confirmButton.addEventListener('click', () => {
            this.handleExportConfirm();
        });
    }

    // UI control methods
    showAssetModal(assetId = null) {
        if (this.assetModal) {
            this.renderAssetForm(assetId);
            this.assetModal.style.display = 'flex';
        }
    }

    closeAssetModal() {
        if (this.assetModal) {
            this.assetModal.style.display = 'none';
        }
    }

    showExportModal() {
        if (this.exportModal) {
            this.exportModal.style.display = 'flex';
        }
    }

    closeExportModal() {
        if (this.exportModal) {
            this.exportModal.style.display = 'none';
        }
    }

    async renderAssetForm(assetId) {
        const content = this.assetModal.querySelector('#asset-modal-content');
        
        if (assetId) {
            // Edit existing asset
            const asset = this.inventory.getAssetById(assetId);
            const metadata = await this.metadata.getAssetMetadata(assetId);
            
            content.innerHTML = this.generateAssetForm(asset, metadata, true);
        } else {
            // Create new asset
            content.innerHTML = this.generateAssetForm(null, null, false);
        }
        
        this.setupAssetFormEvents();
    }

    generateAssetForm(asset, metadata, isEdit) {
        const title = isEdit ? 'Edit Asset' : 'Create Asset';
        const submitText = isEdit ? 'Update Asset' : 'Create Asset';
        
        return `
            <form id="asset-form" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Asset Type</label>
                        <select id="asset-type" class="w-full border border-gray-300 rounded-md px-3 py-2" required>
                            <option value="">Select Asset Type</option>
                            <option value="HVAC" ${asset?.asset_type === 'HVAC' ? 'selected' : ''}>HVAC</option>
                            <option value="Electrical" ${asset?.asset_type === 'Electrical' ? 'selected' : ''}>Electrical</option>
                            <option value="Plumbing" ${asset?.asset_type === 'Plumbing' ? 'selected' : ''}>Plumbing</option>
                            <option value="Fire Protection" ${asset?.asset_type === 'Fire Protection' ? 'selected' : ''}>Fire Protection</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">System</label>
                        <input type="text" id="asset-system" class="w-full border border-gray-300 rounded-md px-3 py-2" 
                               value="${asset?.system || ''}" required>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Location</label>
                    <input type="text" id="asset-location" class="w-full border border-gray-300 rounded-md px-3 py-2" 
                           value="${asset?.location?.room || ''}" placeholder="Room/Area">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Status</label>
                        <select id="asset-status" class="w-full border border-gray-300 rounded-md px-3 py-2">
                            <option value="Active" ${asset?.status === 'Active' ? 'selected' : ''}>Active</option>
                            <option value="Inactive" ${asset?.status === 'Inactive' ? 'selected' : ''}>Inactive</option>
                            <option value="Maintenance" ${asset?.status === 'Maintenance' ? 'selected' : ''}>Maintenance</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Estimated Value</label>
                        <input type="number" id="asset-value" class="w-full border border-gray-300 rounded-md px-3 py-2" 
                               value="${asset?.estimated_value || ''}" placeholder="0.00">
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button type="submit" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                        ${submitText}
                    </button>
                    <button type="button" id="cancel-asset-form" class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm">
                        Cancel
                    </button>
                </div>
            </form>
        `;
    }

    setupAssetFormEvents() {
        const form = this.assetModal.querySelector('#asset-form');
        const cancelButton = this.assetModal.querySelector('#cancel-asset-form');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAssetFormSubmit();
        });
        
        cancelButton.addEventListener('click', () => {
            this.closeAssetModal();
        });
    }

    async handleAssetFormSubmit() {
        const formData = new FormData(this.assetModal.querySelector('#asset-form'));
        const assetData = {
            asset_type: formData.get('asset-type'),
            system: formData.get('asset-system'),
            location: { room: formData.get('asset-location') },
            status: formData.get('asset-status'),
            estimated_value: parseFloat(formData.get('asset-value')) || null
        };
        
        try {
            if (this.currentAssetId) {
                await this.updateAsset(this.currentAssetId, assetData);
            } else {
                await this.createAsset(assetData);
            }
            
            this.closeAssetModal();
            
        } catch (error) {
            console.error('Failed to save asset:', error);
            // Show error message to user
        }
    }

    handleExportConfirm() {
        const format = this.exportModal.querySelector('#export-format').value;
        const includeMetadata = this.exportModal.querySelector('#include-metadata').checked;
        const includeCategories = this.exportModal.querySelector('#include-categories').checked;
        
        this.exportSelectedAssets(format);
        this.closeExportModal();
    }

    // Summary and charts
    updateSummaryCards() {
        const assets = this.inventory.getAssets();
        const stats = {
            total: assets.length,
            active: assets.filter(a => a.status === 'Active').length,
            maintenance: assets.filter(a => a.status === 'Maintenance').length,
            inactive: assets.filter(a => a.status === 'Inactive').length
        };
        
        this.triggerEvent('summaryUpdated', { stats });
    }

    renderCharts() {
        if (!this.options.enableCharts) return;
        
        this.renderSystemChart();
        this.renderStatusChart();
        this.renderValueChart();
    }

    renderSystemChart() {
        const assets = this.inventory.getAssets();
        const systemData = {};
        
        assets.forEach(asset => {
            systemData[asset.system] = (systemData[asset.system] || 0) + 1;
        });
        
        this.triggerEvent('systemChartUpdated', { data: systemData });
    }

    renderStatusChart() {
        const assets = this.inventory.getAssets();
        const statusData = {};
        
        assets.forEach(asset => {
            statusData[asset.status] = (statusData[asset.status] || 0) + 1;
        });
        
        this.triggerEvent('statusChartUpdated', { data: statusData });
    }

    renderValueChart() {
        const assets = this.inventory.getAssets();
        const valueRanges = {
            '0-10k': 0,
            '10k-50k': 0,
            '50k-100k': 0,
            '100k+': 0
        };
        
        assets.forEach(asset => {
            const value = asset.estimated_value || 0;
            if (value <= 10000) valueRanges['0-10k']++;
            else if (value <= 50000) valueRanges['10k-50k']++;
            else if (value <= 100000) valueRanges['50k-100k']++;
            else valueRanges['100k+']++;
        });
        
        this.triggerEvent('valueChartUpdated', { data: valueRanges });
    }

    // Utility methods
    getAuthHeaders() {
        const token = localStorage.getItem('arx_jwt');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    // Module access methods
    getInventory() {
        return this.inventory;
    }

    getSearch() {
        return this.search;
    }

    getCategories() {
        return this.categories;
    }

    getMetadata() {
        return this.metadata;
    }

    // Public API methods
    async getAssets() {
        return this.inventory.getAssets();
    }

    async getAsset(assetId) {
        return this.inventory.getAsset(assetId);
    }

    async searchAssets(query, options = {}) {
        return this.search.search(query, options);
    }

    async getCategories() {
        return this.categories.getCategories();
    }

    async getAssetMetadata(assetId) {
        return this.metadata.getAssetMetadata(assetId);
    }

    getInventoryStatistics() {
        return {
            totalAssets: this.inventory.getAssetCount(),
            selectedAssets: this.getSelectedAssetsCount(),
            categories: this.categories.getCategoryStatistics(),
            searchResults: this.search.getSearchResultCount()
        };
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
                    console.error(`Error in asset inventory manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // Destroy modules
        if (this.inventory) {
            this.inventory.destroy();
        }
        if (this.search) {
            this.search.destroy();
        }
        if (this.categories) {
            this.categories.destroy();
        }
        if (this.metadata) {
            this.metadata.destroy();
        }
        
        // Clear state
        this.selectedAssets.clear();
        
        // Remove UI elements
        if (this.assetModal) {
            this.assetModal.remove();
        }
        if (this.exportModal) {
            this.exportModal.remove();
        }
        
        // Clear event handlers
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 