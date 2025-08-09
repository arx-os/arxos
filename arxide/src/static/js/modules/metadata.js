/**
 * Metadata Module
 * Handles asset metadata management and analysis
 */

export class Metadata {
    constructor(options = {}) {
        this.options = {
            enableMetadataValidation: options.enableMetadataValidation !== false,
            enableMetadataAnalysis: options.enableMetadataAnalysis !== false,
            maxMetadataSize: options.maxMetadataSize || 1024 * 1024, // 1MB
            ...options
        };

        // Metadata state
        this.metadata = new Map();
        this.metadataSchemas = new Map();
        this.metadataAnalytics = {};

        // Metadata templates
        this.metadataTemplates = {
            'HVAC': {
                capacity: { type: 'number', unit: 'BTU/hr', required: true },
                efficiency_rating: { type: 'number', unit: 'SEER', required: true },
                manufacturer: { type: 'string', required: true },
                model: { type: 'string', required: true },
                installation_date: { type: 'date', required: false },
                warranty_expiry: { type: 'date', required: false }
            },
            'Electrical': {
                voltage: { type: 'number', unit: 'V', required: true },
                amperage: { type: 'number', unit: 'A', required: true },
                phase: { type: 'string', enum: ['Single', 'Three'], required: true },
                manufacturer: { type: 'string', required: true },
                installation_date: { type: 'date', required: false }
            },
            'Plumbing': {
                flow_rate: { type: 'number', unit: 'GPM', required: false },
                pressure: { type: 'number', unit: 'PSI', required: false },
                material: { type: 'string', enum: ['Copper', 'PVC', 'Steel'], required: true },
                manufacturer: { type: 'string', required: true },
                installation_date: { type: 'date', required: false }
            }
        };

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadMetadataSchemas();
    }

    setupEventListeners() {
        // Listen for metadata changes
        document.addEventListener('metadataChanged', (event) => {
            this.handleMetadataChange(event.detail);
        });

        // Listen for metadata validation
        document.addEventListener('metadataValidation', (event) => {
            this.handleMetadataValidation(event.detail);
        });
    }

    // Metadata loading methods
    async loadMetadataSchemas() {
        try {
            const response = await fetch('/api/metadata/schemas', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const schemas = await response.json();
            schemas.forEach(schema => {
                this.metadataSchemas.set(schema.id, schema);
            });

            this.triggerEvent('metadataSchemasLoaded', {
                schemas: Array.from(this.metadataSchemas.values()),
                count: this.metadataSchemas.size
            });

        } catch (error) {
            console.error('Failed to load metadata schemas:', error);
            this.triggerEvent('metadataSchemasLoadFailed', { error });
        }
    }

    // Metadata operations
    async getAssetMetadata(assetId) {
        try {
            const response = await fetch(`/api/assets/${assetId}/metadata`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const metadata = await response.json();
            this.metadata.set(assetId, metadata);

            this.triggerEvent('metadataLoaded', { assetId, metadata });
            return metadata;

        } catch (error) {
            console.error('Failed to load asset metadata:', error);
            this.triggerEvent('metadataLoadFailed', { assetId, error });
            throw error;
        }
    }

    async updateAssetMetadata(assetId, metadata) {
        try {
            // Validate metadata
            if (this.options.enableMetadataValidation) {
                const validationErrors = this.validateMetadata(assetId, metadata);
                if (validationErrors.length > 0) {
                    throw new Error(`Metadata validation failed: ${validationErrors.join(', ')}`);
                }
            }

            const response = await fetch(`/api/assets/${assetId}/metadata`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(metadata)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const updatedMetadata = await response.json();
            this.metadata.set(assetId, updatedMetadata);

            this.triggerEvent('metadataUpdated', { assetId, metadata: updatedMetadata });
            return updatedMetadata;

        } catch (error) {
            console.error('Failed to update asset metadata:', error);
            this.triggerEvent('metadataUpdateFailed', { assetId, metadata, error });
            throw error;
        }
    }

    async deleteAssetMetadata(assetId) {
        try {
            const response = await fetch(`/api/assets/${assetId}/metadata`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.metadata.delete(assetId);

            this.triggerEvent('metadataDeleted', { assetId });

        } catch (error) {
            console.error('Failed to delete asset metadata:', error);
            this.triggerEvent('metadataDeleteFailed', { assetId, error });
            throw error;
        }
    }

    // Metadata validation
    validateMetadata(assetId, metadata) {
        const errors = [];

        // Get asset to determine type
        const asset = this.getAssetById(assetId);
        if (!asset) {
            errors.push('Asset not found');
            return errors;
        }

        // Get schema for asset type
        const schema = this.getMetadataSchema(asset.asset_type);
        if (!schema) {
            return errors; // No schema means no validation required
        }

        // Validate required fields
        Object.entries(schema.fields).forEach(([fieldName, fieldConfig]) => {
            if (fieldConfig.required && !metadata[fieldName]) {
                errors.push(`Required field '${fieldName}' is missing`);
            }
        });

        // Validate field types
        Object.entries(metadata).forEach(([fieldName, value]) => {
            const fieldConfig = schema.fields[fieldName];
            if (fieldConfig) {
                const typeError = this.validateFieldType(fieldName, value, fieldConfig);
                if (typeError) {
                    errors.push(typeError);
                }
            }
        });

        // Validate metadata size
        const metadataSize = JSON.stringify(metadata).length;
        if (metadataSize > this.options.maxMetadataSize) {
            errors.push(`Metadata size (${metadataSize} bytes) exceeds maximum allowed size (${this.options.maxMetadataSize} bytes)`);
        }

        return errors;
    }

    validateFieldType(fieldName, value, fieldConfig) {
        if (value == null) return null;

        switch (fieldConfig.type) {
            case 'string':
                if (typeof value !== 'string') {
                    return `Field '${fieldName}' must be a string`;
                }
                if (fieldConfig.maxLength && value.length > fieldConfig.maxLength) {
                    return `Field '${fieldName}' cannot exceed ${fieldConfig.maxLength} characters`;
                }
                break;

            case 'number':
                if (typeof value !== 'number' || isNaN(value)) {
                    return `Field '${fieldName}' must be a number`;
                }
                if (fieldConfig.min !== undefined && value < fieldConfig.min) {
                    return `Field '${fieldName}' must be at least ${fieldConfig.min}`;
                }
                if (fieldConfig.max !== undefined && value > fieldConfig.max) {
                    return `Field '${fieldName}' cannot exceed ${fieldConfig.max}`;
                }
                break;

            case 'date':
                const date = new Date(value);
                if (isNaN(date.getTime())) {
                    return `Field '${fieldName}' must be a valid date`;
                }
                break;

            case 'boolean':
                if (typeof value !== 'boolean') {
                    return `Field '${fieldName}' must be a boolean`;
                }
                break;

            case 'enum':
                if (!fieldConfig.enum.includes(value)) {
                    return `Field '${fieldName}' must be one of: ${fieldConfig.enum.join(', ')}`;
                }
                break;
        }

        return null;
    }

    // Metadata schema methods
    getMetadataSchema(assetType) {
        return this.metadataSchemas.get(assetType) || this.metadataTemplates[assetType];
    }

    getAvailableSchemas() {
        return Array.from(this.metadataSchemas.keys());
    }

    createMetadataFromTemplate(assetType, metadata = {}) {
        const template = this.getMetadataSchema(assetType);
        if (!template) {
            throw new Error(`No metadata template found for asset type: ${assetType}`);
        }

        const defaultMetadata = {};
        Object.entries(template.fields).forEach(([fieldName, fieldConfig]) => {
            if (fieldConfig.default !== undefined) {
                defaultMetadata[fieldName] = fieldConfig.default;
            }
        });

        return { ...defaultMetadata, ...metadata };
    }

    // Metadata analytics
    async analyzeMetadata(assetIds = null) {
        if (!this.options.enableMetadataAnalysis) return;

        try {
            const assets = assetIds ?
                assetIds.map(id => this.getAssetById(id)).filter(Boolean) :
                this.getAllAssets();

            const analysis = {
                totalAssets: assets.length,
                assetsWithMetadata: 0,
                metadataCompleteness: {},
                fieldUsage: {},
                valueRanges: {},
                commonValues: {}
            };

            for (const asset of assets) {
                const metadata = this.metadata.get(asset.id);
                if (metadata) {
                    analysis.assetsWithMetadata++;
                    this.analyzeAssetMetadata(asset, metadata, analysis);
                }
            }

            this.metadataAnalytics = analysis;
            this.triggerEvent('metadataAnalysisCompleted', { analysis });

        } catch (error) {
            console.error('Failed to analyze metadata:', error);
            this.triggerEvent('metadataAnalysisFailed', { error });
        }
    }

    analyzeAssetMetadata(asset, metadata, analysis) {
        const schema = this.getMetadataSchema(asset.asset_type);
        if (!schema) return;

        // Analyze field usage
        Object.entries(schema.fields).forEach(([fieldName, fieldConfig]) => {
            if (!analysis.fieldUsage[fieldName]) {
                analysis.fieldUsage[fieldName] = {
                    total: 0,
                    populated: 0,
                    type: fieldConfig.type
                };
            }

            analysis.fieldUsage[fieldName].total++;
            if (metadata[fieldName] !== undefined && metadata[fieldName] !== null) {
                analysis.fieldUsage[fieldName].populated++;
            }
        });

        // Analyze value ranges for numeric fields
        Object.entries(metadata).forEach(([fieldName, value]) => {
            const fieldConfig = schema.fields[fieldName];
            if (fieldConfig && fieldConfig.type === 'number' && typeof value === 'number') {
                if (!analysis.valueRanges[fieldName]) {
                    analysis.valueRanges[fieldName] = {
                        min: Infinity,
                        max: -Infinity,
                        sum: 0,
                        count: 0
                    };
                }

                const range = analysis.valueRanges[fieldName];
                range.min = Math.min(range.min, value);
                range.max = Math.max(range.max, value);
                range.sum += value;
                range.count++;
            }
        });

        // Analyze common values
        Object.entries(metadata).forEach(([fieldName, value]) => {
            if (!analysis.commonValues[fieldName]) {
                analysis.commonValues[fieldName] = {};
            }

            const valueStr = String(value);
            analysis.commonValues[fieldName][valueStr] =
                (analysis.commonValues[fieldName][valueStr] || 0) + 1;
        });
    }

    getMetadataAnalytics() {
        return { ...this.metadataAnalytics };
    }

    // Metadata search
    async searchMetadata(query, filters = {}) {
        try {
            const searchParams = {
                query,
                filters,
                options: {
                    includeArchived: filters.includeArchived || false,
                    limit: filters.limit || 100
                }
            };

            const response = await fetch('/api/metadata/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(searchParams)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const results = await response.json();
            this.triggerEvent('metadataSearchCompleted', { query, results });
            return results;

        } catch (error) {
            console.error('Failed to search metadata:', error);
            this.triggerEvent('metadataSearchFailed', { query, error });
            throw error;
        }
    }

    // Metadata export/import
    async exportMetadata(assetIds, format = 'json') {
        try {
            const exportParams = {
                asset_ids: assetIds,
                format: format,
                include_schemas: true
            };

            const response = await fetch('/api/metadata/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(exportParams)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `asset_metadata_${Date.now()}.${format}`;
            a.click();

            URL.revokeObjectURL(url);

            this.triggerEvent('metadataExported', { assetIds, format });

        } catch (error) {
            console.error('Failed to export metadata:', error);
            this.triggerEvent('metadataExportFailed', { assetIds, format, error });
            throw error;
        }
    }

    async importMetadata(file, options = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('options', JSON.stringify(options));

            const response = await fetch('/api/metadata/import', {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders()
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            this.triggerEvent('metadataImported', { result });
            return result;

        } catch (error) {
            console.error('Failed to import metadata:', error);
            this.triggerEvent('metadataImportFailed', { file, error });
            throw error;
        }
    }

    // Event handlers
    handleMetadataChange(detail) {
        const { assetId, metadata } = detail;
        this.metadata.set(assetId, metadata);
    }

    handleMetadataValidation(detail) {
        const { assetId, metadata } = detail;
        const errors = this.validateMetadata(assetId, metadata);

        if (errors.length > 0) {
            this.triggerEvent('metadataValidationFailed', { assetId, errors });
        } else {
            this.triggerEvent('metadataValidationPassed', { assetId });
        }
    }

    // Utility methods
    getAssetById(assetId) {
        // This would typically come from the inventory module
        return window.assetInventory?.getAssetById(assetId);
    }

    getAllAssets() {
        // This would typically come from the inventory module
        return window.assetInventory?.getAssets() || [];
    }

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
                    handler({ ...data, metadata: this });
                } catch (error) {
                    console.error(`Error in metadata event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.metadata.clear();
        this.metadataSchemas.clear();
        this.metadataAnalytics = {};

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
