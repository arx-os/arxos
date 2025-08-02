/**
 * CMMS Integration Manager
 * Orchestrates all CMMS integration features and handles different platform patterns
 */

import { DeepLinkRouter } from './deep-link-router.js';
import { ObjectRegistry } from './object-registry.js';
import { LinkGenerator } from './link-generator.js';

export class CMMSIntegrationManager {
    constructor(options = {}) {
        this.options = {
            enableWebTMA: options.enableWebTMA !== false,
            enableMaximo: options.enableMaximo !== false,
            enableSAPPM: options.enableSAPPM !== false,
            enableGeneric: options.enableGeneric !== false,
            defaultAccessType: options.defaultAccessType || 'public',
            enableAnalytics: options.enableAnalytics !== false,
            ...options
        };
        
        // Core modules
        this.deepLinkRouter = null;
        this.objectRegistry = null;
        this.linkGenerator = null;
        
        // CMMS adapters
        this.adapters = new Map();
        
        // Integration configurations
        this.configurations = new Map();
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    async initialize() {
        try {
            // Initialize core modules
            this.deepLinkRouter = new DeepLinkRouter({
                enableHighlighting: true,
                enableZooming: true
            });
            
            this.objectRegistry = new ObjectRegistry({
                enableCaching: true,
                enableIndexing: true
            });
            
            this.linkGenerator = new LinkGenerator({
                enableQRCode: true,
                enableAnalytics: this.options.enableAnalytics
            });
            
            // Initialize CMMS adapters
            await this.initializeAdapters();
            
            // Load configurations
            await this.loadConfigurations();
            
            // Setup event listeners
            this.setupEventListeners();
            
            this.triggerEvent('initialized', { 
                adapters: Array.from(this.adapters.keys()),
                configurations: Array.from(this.configurations.keys())
            });
            
        } catch (error) {
            console.error('CMMS Integration Manager initialization failed:', error);
            this.triggerEvent('initializationFailed', { error });
        }
    }

    async initializeAdapters() {
        // Initialize WebTMA adapter
        if (this.options.enableWebTMA) {
            try {
                const { WebTMAAdapter } = await import('./cmms/webtma-adapter.js');
                this.adapters.set('webtma', new WebTMAAdapter());
            } catch (error) {
                console.warn('WebTMA adapter not available:', error);
            }
        }
        
        // Initialize Maximo adapter
        if (this.options.enableMaximo) {
            try {
                const { MaximoAdapter } = await import('./cmms/maximo-adapter.js');
                this.adapters.set('maximo', new MaximoAdapter());
            } catch (error) {
                console.warn('Maximo adapter not available:', error);
            }
        }
        
        // Initialize SAP PM adapter
        if (this.options.enableSAPPM) {
            try {
                const { SAPPMAdapter } = await import('./cmms/sappm-adapter.js');
                this.adapters.set('sappm', new SAPPMAdapter());
            } catch (error) {
                console.warn('SAP PM adapter not available:', error);
            }
        }
        
        // Initialize generic adapter
        if (this.options.enableGeneric) {
            try {
                const { GenericAdapter } = await import('./cmms/generic-adapter.js');
                this.adapters.set('generic', new GenericAdapter());
            } catch (error) {
                console.warn('Generic adapter not available:', error);
            }
        }
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/cmms/config', {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const configs = await response.json();
                configs.forEach(config => {
                    this.configurations.set(config.id, config);
                });
            }
        } catch (error) {
            console.error('Failed to load CMMS configurations:', error);
        }
    }

    setupEventListeners() {
        // Listen for object selection
        document.addEventListener('objectSelected', (event) => {
            this.handleObjectSelection(event.detail);
        });
        
        // Listen for link generation
        this.linkGenerator.addEventListener('linkGenerated', (event) => {
            this.handleLinkGenerated(event);
        });
        
        // Listen for CMMS integration requests
        document.addEventListener('cmmsIntegration', (event) => {
            this.handleCMMSIntegrationRequest(event.detail);
        });
    }

    // CMMS integration methods
    async integrateWithCMMS(params) {
        const {
            cmmsType,
            objectId,
            integrationType = 'link',
            cmmsData = {},
            options = {}
        } = params;
        
        try {
            // Validate CMMS type
            if (!this.adapters.has(cmmsType)) {
                throw new Error(`Unsupported CMMS type: ${cmmsType}`);
            }
            
            const adapter = this.adapters.get(cmmsType);
            
            // Get object details
            const object = this.objectRegistry.getObject(objectId);
            if (!object) {
                throw new Error(`Object '${objectId}' not found`);
            }
            
            // Generate link
            const link = await this.linkGenerator.generateLink({
                objectId: object.id,
                buildingId: object.building_id,
                floorId: object.floor_id,
                accessType: options.accessType || this.options.defaultAccessType,
                expiresAt: options.expiresAt,
                viewOptions: options.viewOptions,
                highlight: options.highlight !== false,
                zoom: options.zoom !== false
            });
            
            // Integrate with CMMS
            const integrationResult = await adapter.integrate({
                link,
                object,
                integrationType,
                cmmsData,
                options
            });
            
            this.triggerEvent('cmmsIntegrationCompleted', {
                cmmsType,
                objectId,
                link,
                result: integrationResult
            });
            
            return integrationResult;
            
        } catch (error) {
            console.error('CMMS integration failed:', error);
            this.triggerEvent('cmmsIntegrationFailed', { params, error });
            throw error;
        }
    }

    async generateCMMSLink(params) {
        const {
            cmmsType,
            objectId,
            linkType = 'standard',
            options = {}
        } = params;
        
        try {
            // Get object details
            const object = this.objectRegistry.getObject(objectId);
            if (!object) {
                throw new Error(`Object '${objectId}' not found`);
            }
            
            // Generate link
            const link = await this.linkGenerator.generateLink({
                objectId: object.id,
                buildingId: object.building_id,
                floorId: object.floor_id,
                accessType: options.accessType || this.options.defaultAccessType,
                expiresAt: options.expiresAt,
                viewOptions: options.viewOptions,
                highlight: options.highlight !== false,
                zoom: options.zoom !== false
            });
            
            // Generate CMMS-specific link format
            const adapter = this.adapters.get(cmmsType);
            if (adapter && adapter.generateLink) {
                const cmmsLink = await adapter.generateLink({
                    link,
                    object,
                    linkType,
                    options
                });
                
                return cmmsLink;
            }
            
            return link;
            
        } catch (error) {
            console.error('CMMS link generation failed:', error);
            throw error;
        }
    }

    async testCMMSConnection(cmmsType, config = {}) {
        try {
            if (!this.adapters.has(cmmsType)) {
                throw new Error(`Unsupported CMMS type: ${cmmsType}`);
            }
            
            const adapter = this.adapters.get(cmmsType);
            
            if (adapter.testConnection) {
                const result = await adapter.testConnection(config);
                
                this.triggerEvent('cmmsConnectionTested', {
                    cmmsType,
                    config,
                    result
                });
                
                return result;
            }
            
            return { success: true, message: 'Connection test not implemented' };
            
        } catch (error) {
            console.error('CMMS connection test failed:', error);
            this.triggerEvent('cmmsConnectionTestFailed', { cmmsType, config, error });
            throw error;
        }
    }

    // Configuration management
    async saveConfiguration(config) {
        try {
            const response = await fetch('/api/cmms/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save configuration: ${response.status}`);
            }
            
            const savedConfig = await response.json();
            this.configurations.set(savedConfig.id, savedConfig);
            
            this.triggerEvent('configurationSaved', { config: savedConfig });
            
            return savedConfig;
            
        } catch (error) {
            console.error('Failed to save configuration:', error);
            throw error;
        }
    }

    async updateConfiguration(configId, updates) {
        try {
            const response = await fetch(`/api/cmms/config/${configId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(updates)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update configuration: ${response.status}`);
            }
            
            const updatedConfig = await response.json();
            this.configurations.set(configId, updatedConfig);
            
            this.triggerEvent('configurationUpdated', { config: updatedConfig });
            
            return updatedConfig;
            
        } catch (error) {
            console.error('Failed to update configuration:', error);
            throw error;
        }
    }

    async deleteConfiguration(configId) {
        try {
            const response = await fetch(`/api/cmms/config/${configId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete configuration: ${response.status}`);
            }
            
            this.configurations.delete(configId);
            
            this.triggerEvent('configurationDeleted', { configId });
            
        } catch (error) {
            console.error('Failed to delete configuration:', error);
            throw error;
        }
    }

    getConfiguration(configId) {
        return this.configurations.get(configId);
    }

    getAllConfigurations() {
        return Array.from(this.configurations.values());
    }

    // Platform-specific methods
    async integrateWithWebTMA(params) {
        return this.integrateWithCMMS({
            ...params,
            cmmsType: 'webtma'
        });
    }

    async integrateWithMaximo(params) {
        return this.integrateWithCMMS({
            ...params,
            cmmsType: 'maximo'
        });
    }

    async integrateWithSAPPM(params) {
        return this.integrateWithCMMS({
            ...params,
            cmmsType: 'sappm'
        });
    }

    // Event handlers
    handleObjectSelection(detail) {
        const { object } = detail;
        
        // Update deep link router
        this.deepLinkRouter.updateURL({
            building_id: object.building_id,
            floor_id: object.floor_id,
            object_id: object.id
        });
        
        this.triggerEvent('objectSelectedForIntegration', { object });
    }

    handleLinkGenerated(event) {
        const { link } = event;
        
        // Notify adapters of new link
        this.adapters.forEach((adapter, cmmsType) => {
            if (adapter.onLinkGenerated) {
                adapter.onLinkGenerated(link);
            }
        });
        
        this.triggerEvent('linkGeneratedForCMMS', { link });
    }

    handleCMMSIntegrationRequest(detail) {
        this.integrateWithCMMS(detail);
    }

    // Analytics and reporting
    async getIntegrationAnalytics(options = {}) {
        const {
            cmmsType = null,
            startDate = null,
            endDate = null,
            groupBy = 'day'
        } = options;
        
        try {
            const params = new URLSearchParams();
            if (cmmsType) params.append('cmms_type', cmmsType);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            if (groupBy) params.append('group_by', groupBy);
            
            const response = await fetch(`/api/cmms/analytics?${params}`, {
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get analytics: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to get integration analytics:', error);
            throw error;
        }
    }

    async generateIntegrationReport(options = {}) {
        try {
            const response = await fetch('/api/cmms/reports/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(options)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to generate report: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to generate integration report:', error);
            throw error;
        }
    }

    // Public API methods
    getSupportedCMMSTypes() {
        return Array.from(this.adapters.keys());
    }

    getAdapter(cmmsType) {
        return this.adapters.get(cmmsType);
    }

    isCMMSSupported(cmmsType) {
        return this.adapters.has(cmmsType);
    }

    getManagerStats() {
        return {
            supportedCMMSTypes: this.getSupportedCMMSTypes(),
            activeConfigurations: this.configurations.size,
            totalObjects: this.objectRegistry.getObjectCount(),
            totalLinks: this.linkGenerator.getGeneratorStats().totalLinks,
            adapters: Array.from(this.adapters.entries()).map(([type, adapter]) => ({
                type,
                name: adapter.name || type,
                version: adapter.version || '1.0.0',
                capabilities: adapter.getCapabilities ? adapter.getCapabilities() : []
            }))
        };
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
                    handler({ ...data, manager: this });
                } catch (error) {
                    console.error(`Error in CMMS integration manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // Destroy core modules
        if (this.deepLinkRouter) {
            this.deepLinkRouter.destroy();
        }
        
        if (this.objectRegistry) {
            this.objectRegistry.destroy();
        }
        
        if (this.linkGenerator) {
            this.linkGenerator.destroy();
        }
        
        // Destroy adapters
        this.adapters.forEach(adapter => {
            if (adapter.destroy) {
                adapter.destroy();
            }
        });
        
        this.adapters.clear();
        this.configurations.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 