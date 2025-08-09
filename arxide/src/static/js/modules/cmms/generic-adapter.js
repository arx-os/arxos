/**
 * Generic CMMS Adapter
 * Handles integration with any CMMS platform that supports hyperlinks
 */

export class GenericAdapter {
    constructor(options = {}) {
        this.options = {
            name: 'Generic CMMS',
            version: '1.0.0',
            supportedLinkTypes: ['standard', 'custom'],
            defaultLinkFormat: 'standard',
            enableCustomFields: true,
            enableMetadata: true,
            ...options
        };

        // Generic CMMS configurations
        this.config = {
            cmmsName: options.cmmsName || 'Unknown CMMS',
            baseUrl: options.baseUrl || '',
            apiKey: options.apiKey || '',
            organizationId: options.organizationId || '',
            customFields: options.customFields || {},
            linkTemplates: options.linkTemplates || {},
            ...options
        };

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for generic CMMS integration events
        document.addEventListener('genericCMMSIntegration', (event) => {
            this.handleGenericCMMSIntegration(event.detail);
        });
    }

    // Core integration methods
    async integrate(params) {
        const {
            link,
            object,
            integrationType = 'link',
            cmmsData = {},
            options = {}
        } = params;

        try {
            switch (integrationType) {
                case 'custom':
                    return await this.integrateWithCustomFormat(link, object, cmmsData, options);

                case 'link':
                default:
                    return await this.generateStandardLink(link, object, options);
            }

        } catch (error) {
            console.error('Generic CMMS integration failed:', error);
            this.triggerEvent('integrationFailed', { params, error });
            throw error;
        }
    }

    async generateLink(params) {
        const {
            link,
            object,
            linkType = 'standard',
            options = {}
        } = params;

        try {
            switch (linkType) {
                case 'custom':
                    return await this.generateCustomLink(link, object, options);

                case 'standard':
                default:
                    return await this.generateStandardLink(link, object, options);
            }

        } catch (error) {
            console.error('Generic CMMS link generation failed:', error);
            throw error;
        }
    }

    // Standard Link Generation
    async generateStandardLink(link, object, options) {
        const {
            includeDescription = true,
            includeLocation = true,
            includeMetadata = true,
            customFields = {}
        } = options;

        // Create generic CMMS-specific link format
        const genericLink = new URL(link.url);

        // Add generic CMMS-specific parameters
        genericLink.searchParams.set('cmms_type', 'generic');
        genericLink.searchParams.set('cmms_name', this.config.cmmsName);
        genericLink.searchParams.set('integration_type', 'standard');

        // Add object context
        const objectContext = {
            id: object.id,
            type: object.object_type,
            building: object.building_id,
            floor: object.floor_id
        };

        if (includeDescription) {
            objectContext.description = `${object.object_type} ${object.id}`;
        }

        if (includeLocation) {
            objectContext.location = `${object.building_id} - ${object.floor_id}`;
        }

        if (includeMetadata && object.metadata) {
            objectContext.metadata = object.metadata;
        }

        // Add custom fields
        if (Object.keys(customFields).length > 0) {
            objectContext.customFields = customFields;
        }

        genericLink.searchParams.set('object_context', JSON.stringify(objectContext));

        return genericLink.toString();
    }

    // Custom Link Generation
    async generateCustomLink(link, object, options) {
        const {
            templateName,
            customFields = {},
            includeMetadata = true
        } = options;

        // Use custom template if specified
        if (templateName && this.config.linkTemplates[templateName]) {
            return this.applyCustomTemplate(link, object, templateName, customFields);
        }

        // Create custom link format
        const customLink = new URL(link.url);

        // Add custom CMMS-specific parameters
        customLink.searchParams.set('cmms_type', 'generic');
        customLink.searchParams.set('cmms_name', this.config.cmmsName);
        customLink.searchParams.set('integration_type', 'custom');

        // Add object context with custom fields
        const objectContext = {
            id: object.id,
            type: object.object_type,
            building: object.building_id,
            floor: object.floor_id,
            customFields: customFields
        };

        if (includeMetadata && object.metadata) {
            objectContext.metadata = object.metadata;
        }

        customLink.searchParams.set('object_context', JSON.stringify(objectContext));

        return customLink.toString();
    }

    // Custom Integration
    async integrateWithCustomFormat(link, object, cmmsData, options) {
        const {
            cmmsRecordType,
            cmmsRecordId,
            customFields = {},
            metadata = {}
        } = cmmsData;

        try {
            // Generate custom link
            const customLink = await this.generateCustomLink(link, object, {
                customFields,
                ...options
            });

            // Create custom integration data
            const integrationData = {
                type: 'custom',
                cmmsRecordType,
                cmmsRecordId,
                cmmsName: this.config.cmmsName,
                link: customLink,
                object: {
                    id: object.id,
                    type: object.object_type,
                    location: `${object.building_id} - ${object.floor_id}`
                },
                customFields,
                metadata: {
                    ...metadata,
                    arxosObjectId: object.id,
                    arxosBuildingId: object.building_id,
                    arxosFloorId: object.floor_id,
                    integrationTimestamp: Date.now()
                }
            };

            // Send to CMMS API if configured
            if (this.config.baseUrl && this.config.apiKey) {
                await this.sendToCMMS(cmmsRecordType, integrationData);
            }

            this.triggerEvent('customIntegrationCompleted', {
                cmmsRecordType,
                cmmsRecordId,
                link: customLink,
                object
            });

            return {
                success: true,
                type: 'custom',
                cmmsRecordType,
                cmmsRecordId,
                link: customLink,
                integrationData
            };

        } catch (error) {
            console.error('Custom integration failed:', error);
            throw error;
        }
    }

    // Template Management
    applyCustomTemplate(link, object, templateName, customFields) {
        const template = this.config.linkTemplates[templateName];
        if (!template) {
            throw new Error(`Template '${templateName}' not found`);
        }

        // Create link based on template
        const templatedLink = new URL(link.url);

        // Apply template parameters
        Object.entries(template.parameters || {}).forEach(([key, value]) => {
            if (typeof value === 'string') {
                // Replace placeholders with object values
                const replacedValue = this.replacePlaceholders(value, object, customFields);
                templatedLink.searchParams.set(key, replacedValue);
            } else {
                templatedLink.searchParams.set(key, JSON.stringify(value));
            }
        });

        // Add template metadata
        templatedLink.searchParams.set('template_name', templateName);
        templatedLink.searchParams.set('cmms_type', 'generic');
        templatedLink.searchParams.set('cmms_name', this.config.cmmsName);

        return templatedLink.toString();
    }

    replacePlaceholders(template, object, customFields) {
        let result = template;

        // Replace object placeholders
        result = result.replace(/\{object\.(\w+)\}/g, (match, key) => {
            return object[key] || '';
        });

        // Replace custom field placeholders
        result = result.replace(/\{custom\.(\w+)\}/g, (match, key) => {
            return customFields[key] || '';
        });

        // Replace metadata placeholders
        result = result.replace(/\{metadata\.(\w+)\}/g, (match, key) => {
            return object.metadata && object.metadata[key] ? object.metadata[key] : '';
        });

        return result;
    }

    // CMMS API Communication
    async sendToCMMS(endpoint, data) {
        if (!this.config.baseUrl || !this.config.apiKey) {
            throw new Error('CMMS API not configured');
        }

        try {
            const response = await fetch(`${this.config.baseUrl}/api/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'X-Organization-ID': this.config.organizationId,
                    'X-CMMS-Name': this.config.cmmsName
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`CMMS API error: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Failed to send data to CMMS:', error);
            throw error;
        }
    }

    async testConnection(config = {}) {
        try {
            const testConfig = { ...this.config, ...config };

            if (!testConfig.baseUrl || !testConfig.apiKey) {
                return {
                    success: false,
                    message: 'CMMS API not configured'
                };
            }

            const response = await fetch(`${testConfig.baseUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${testConfig.apiKey}`,
                    'X-Organization-ID': testConfig.organizationId,
                    'X-CMMS-Name': testConfig.cmmsName
                }
            });

            if (response.ok) {
                return {
                    success: true,
                    message: `${testConfig.cmmsName} connection successful`
                };
            } else {
                return {
                    success: false,
                    message: `${testConfig.cmmsName} connection failed: ${response.status}`
                };
            }

        } catch (error) {
            return {
                success: false,
                message: `${this.config.cmmsName} connection test failed: ${error.message}`
            };
        }
    }

    // Template Management
    addLinkTemplate(name, template) {
        this.config.linkTemplates[name] = template;
        this.triggerEvent('templateAdded', { name, template });
    }

    removeLinkTemplate(name) {
        if (this.config.linkTemplates[name]) {
            delete this.config.linkTemplates[name];
            this.triggerEvent('templateRemoved', { name });
        }
    }

    getLinkTemplate(name) {
        return this.config.linkTemplates[name];
    }

    getAllLinkTemplates() {
        return this.config.linkTemplates;
    }

    // Custom Field Management
    addCustomField(name, value) {
        this.config.customFields[name] = value;
        this.triggerEvent('customFieldAdded', { name, value });
    }

    removeCustomField(name) {
        if (this.config.customFields[name]) {
            delete this.config.customFields[name];
            this.triggerEvent('customFieldRemoved', { name });
        }
    }

    getCustomField(name) {
        return this.config.customFields[name];
    }

    getAllCustomFields() {
        return this.config.customFields;
    }

    // Event handlers
    handleGenericCMMSIntegration(detail) {
        this.integrate(detail);
    }

    onLinkGenerated(link) {
        // Handle link generation for generic CMMS
        this.triggerEvent('linkGeneratedForGenericCMMS', { link });
    }

    // Public API methods
    getCapabilities() {
        return {
            name: this.options.name,
            version: this.options.version,
            supportedLinkTypes: this.options.supportedLinkTypes,
            features: [
                'standard_link_generation',
                'custom_link_generation',
                'template_support',
                'custom_fields_support',
                'metadata_support',
                'api_integration'
            ],
            templates: Object.keys(this.config.linkTemplates),
            customFields: Object.keys(this.config.customFields)
        };
    }

    getConfiguration() {
        return {
            ...this.config,
            name: this.options.name,
            version: this.options.version
        };
    }

    updateConfiguration(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.triggerEvent('configurationUpdated', { config: this.config });
    }

    // Utility methods
    validateCustomFields(fields) {
        const errors = [];

        // Validate field names
        Object.keys(fields).forEach(fieldName => {
            if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(fieldName)) {
                errors.push(`Invalid field name: ${fieldName}`);
            }
        });

        // Validate field values
        Object.entries(fields).forEach(([fieldName, fieldValue]) => {
            if (typeof fieldValue === 'string' && fieldValue.length > 1000) {
                errors.push(`Field value too long: ${fieldName}`);
            }
        });

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    sanitizeCustomFields(fields) {
        const sanitized = {};

        Object.entries(fields).forEach(([key, value]) => {
            // Sanitize key
            const sanitizedKey = key.replace(/[^a-zA-Z0-9_]/g, '_');

            // Sanitize value
            let sanitizedValue = value;
            if (typeof value === 'string') {
                sanitizedValue = value.substring(0, 1000); // Limit length
            }

            sanitized[sanitizedKey] = sanitizedValue;
        });

        return sanitized;
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
                    handler({ ...data, adapter: this });
                } catch (error) {
                    console.error(`Error in generic CMMS adapter event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
