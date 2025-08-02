/**
 * WebTMA Adapter
 * Handles WebTMA-specific CMMS integration patterns and link formats
 */

export class WebTMAAdapter {
    constructor(options = {}) {
        this.options = {
            name: 'WebTMA',
            version: '1.0.0',
            supportedLinkTypes: ['work_order', 'equipment', 'pm_schedule', 'standard'],
            defaultLinkFormat: 'standard',
            enableRichText: true,
            enableAttachments: true,
            ...options
        };
        
        // WebTMA-specific configurations
        this.config = {
            baseUrl: options.baseUrl || '',
            apiKey: options.apiKey || '',
            organizationId: options.organizationId || '',
            defaultAccessLevel: options.defaultAccessLevel || 'public'
        };
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for WebTMA-specific events
        document.addEventListener('webtmaIntegration', (event) => {
            this.handleWebTMAIntegration(event.detail);
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
                case 'work_order':
                    return await this.integrateWithWorkOrder(link, object, cmmsData, options);
                
                case 'equipment':
                    return await this.integrateWithEquipment(link, object, cmmsData, options);
                
                case 'pm_schedule':
                    return await this.integrateWithPMSchedule(link, object, cmmsData, options);
                
                case 'link':
                default:
                    return await this.generateStandardLink(link, object, options);
            }
            
        } catch (error) {
            console.error('WebTMA integration failed:', error);
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
                case 'work_order':
                    return await this.generateWorkOrderLink(link, object, options);
                
                case 'equipment':
                    return await this.generateEquipmentLink(link, object, options);
                
                case 'pm_schedule':
                    return await this.generatePMScheduleLink(link, object, options);
                
                case 'standard':
                default:
                    return await this.generateStandardLink(link, object, options);
            }
            
        } catch (error) {
            console.error('WebTMA link generation failed:', error);
            throw error;
        }
    }

    // Work Order Integration
    async integrateWithWorkOrder(link, object, cmmsData, options) {
        const {
            workOrderId,
            workOrderNumber,
            description,
            priority = 'normal',
            status = 'open'
        } = cmmsData;
        
        try {
            // Generate work order specific link
            const workOrderLink = await this.generateWorkOrderLink(link, object, {
                workOrderId,
                workOrderNumber,
                ...options
            });
            
            // Create work order integration data
            const integrationData = {
                type: 'work_order',
                workOrderId,
                workOrderNumber,
                description: description || `View ${object.object_type} ${object.id} in Arxos`,
                priority,
                status,
                link: workOrderLink,
                object: {
                    id: object.id,
                    type: object.object_type,
                    location: `${object.building_id} - ${object.floor_id}`
                },
                metadata: {
                    arxosObjectId: object.id,
                    arxosBuildingId: object.building_id,
                    arxosFloorId: object.floor_id,
                    integrationTimestamp: Date.now()
                }
            };
            
            // Send to WebTMA API if configured
            if (this.config.baseUrl && this.config.apiKey) {
                await this.sendToWebTMA('work_orders', integrationData);
            }
            
            this.triggerEvent('workOrderIntegrated', { 
                workOrderId, 
                link: workOrderLink, 
                object 
            });
            
            return {
                success: true,
                type: 'work_order',
                workOrderId,
                link: workOrderLink,
                integrationData
            };
            
        } catch (error) {
            console.error('Work order integration failed:', error);
            throw error;
        }
    }

    async generateWorkOrderLink(link, object, options) {
        const {
            workOrderId,
            workOrderNumber,
            includeDescription = true,
            includeLocation = true
        } = options;
        
        // Create WebTMA-specific link format
        const webtmaLink = new URL(link.url);
        
        // Add WebTMA-specific parameters
        webtmaLink.searchParams.set('cmms_type', 'webtma');
        webtmaLink.searchParams.set('integration_type', 'work_order');
        
        if (workOrderId) {
            webtmaLink.searchParams.set('work_order_id', workOrderId);
        }
        
        if (workOrderNumber) {
            webtmaLink.searchParams.set('work_order_number', workOrderNumber);
        }
        
        // Add object context
        webtmaLink.searchParams.set('object_context', JSON.stringify({
            id: object.id,
            type: object.object_type,
            building: object.building_id,
            floor: object.floor_id,
            description: includeDescription ? `${object.object_type} ${object.id}` : '',
            location: includeLocation ? `${object.building_id} - ${object.floor_id}` : ''
        }));
        
        return webtmaLink.toString();
    }

    // Equipment Integration
    async integrateWithEquipment(link, object, cmmsData, options) {
        const {
            equipmentId,
            equipmentNumber,
            equipmentName,
            category,
            manufacturer,
            model
        } = cmmsData;
        
        try {
            // Generate equipment specific link
            const equipmentLink = await this.generateEquipmentLink(link, object, {
                equipmentId,
                equipmentNumber,
                ...options
            });
            
            // Create equipment integration data
            const integrationData = {
                type: 'equipment',
                equipmentId,
                equipmentNumber,
                equipmentName: equipmentName || `${object.object_type} ${object.id}`,
                category,
                manufacturer,
                model,
                link: equipmentLink,
                object: {
                    id: object.id,
                    type: object.object_type,
                    location: `${object.building_id} - ${object.floor_id}`
                },
                metadata: {
                    arxosObjectId: object.id,
                    arxosBuildingId: object.building_id,
                    arxosFloorId: object.floor_id,
                    integrationTimestamp: Date.now()
                }
            };
            
            // Send to WebTMA API if configured
            if (this.config.baseUrl && this.config.apiKey) {
                await this.sendToWebTMA('equipment', integrationData);
            }
            
            this.triggerEvent('equipmentIntegrated', { 
                equipmentId, 
                link: equipmentLink, 
                object 
            });
            
            return {
                success: true,
                type: 'equipment',
                equipmentId,
                link: equipmentLink,
                integrationData
            };
            
        } catch (error) {
            console.error('Equipment integration failed:', error);
            throw error;
        }
    }

    async generateEquipmentLink(link, object, options) {
        const {
            equipmentId,
            equipmentNumber,
            includeSpecs = true,
            includeLocation = true
        } = options;
        
        // Create WebTMA-specific link format
        const webtmaLink = new URL(link.url);
        
        // Add WebTMA-specific parameters
        webtmaLink.searchParams.set('cmms_type', 'webtma');
        webtmaLink.searchParams.set('integration_type', 'equipment');
        
        if (equipmentId) {
            webtmaLink.searchParams.set('equipment_id', equipmentId);
        }
        
        if (equipmentNumber) {
            webtmaLink.searchParams.set('equipment_number', equipmentNumber);
        }
        
        // Add object context
        webtmaLink.searchParams.set('object_context', JSON.stringify({
            id: object.id,
            type: object.object_type,
            building: object.building_id,
            floor: object.floor_id,
            specs: includeSpecs ? this.extractObjectSpecs(object) : {},
            location: includeLocation ? `${object.building_id} - ${object.floor_id}` : ''
        }));
        
        return webtmaLink.toString();
    }

    // PM Schedule Integration
    async integrateWithPMSchedule(link, object, cmmsData, options) {
        const {
            scheduleId,
            scheduleName,
            frequency,
            nextDue,
            assignedTo
        } = cmmsData;
        
        try {
            // Generate PM schedule specific link
            const pmScheduleLink = await this.generatePMScheduleLink(link, object, {
                scheduleId,
                scheduleName,
                ...options
            });
            
            // Create PM schedule integration data
            const integrationData = {
                type: 'pm_schedule',
                scheduleId,
                scheduleName,
                frequency,
                nextDue,
                assignedTo,
                link: pmScheduleLink,
                object: {
                    id: object.id,
                    type: object.object_type,
                    location: `${object.building_id} - ${object.floor_id}`
                },
                metadata: {
                    arxosObjectId: object.id,
                    arxosBuildingId: object.building_id,
                    arxosFloorId: object.floor_id,
                    integrationTimestamp: Date.now()
                }
            };
            
            // Send to WebTMA API if configured
            if (this.config.baseUrl && this.config.apiKey) {
                await this.sendToWebTMA('pm_schedules', integrationData);
            }
            
            this.triggerEvent('pmScheduleIntegrated', { 
                scheduleId, 
                link: pmScheduleLink, 
                object 
            });
            
            return {
                success: true,
                type: 'pm_schedule',
                scheduleId,
                link: pmScheduleLink,
                integrationData
            };
            
        } catch (error) {
            console.error('PM schedule integration failed:', error);
            throw error;
        }
    }

    async generatePMScheduleLink(link, object, options) {
        const {
            scheduleId,
            scheduleName,
            includeFrequency = true,
            includeLocation = true
        } = options;
        
        // Create WebTMA-specific link format
        const webtmaLink = new URL(link.url);
        
        // Add WebTMA-specific parameters
        webtmaLink.searchParams.set('cmms_type', 'webtma');
        webtmaLink.searchParams.set('integration_type', 'pm_schedule');
        
        if (scheduleId) {
            webtmaLink.searchParams.set('schedule_id', scheduleId);
        }
        
        if (scheduleName) {
            webtmaLink.searchParams.set('schedule_name', scheduleName);
        }
        
        // Add object context
        webtmaLink.searchParams.set('object_context', JSON.stringify({
            id: object.id,
            type: object.object_type,
            building: object.building_id,
            floor: object.floor_id,
            frequency: includeFrequency ? this.extractPMFrequency(object) : {},
            location: includeLocation ? `${object.building_id} - ${object.floor_id}` : ''
        }));
        
        return webtmaLink.toString();
    }

    // Standard Link Generation
    async generateStandardLink(link, object, options) {
        const {
            includeDescription = true,
            includeLocation = true,
            includeMetadata = true
        } = options;
        
        // Create WebTMA-specific link format
        const webtmaLink = new URL(link.url);
        
        // Add WebTMA-specific parameters
        webtmaLink.searchParams.set('cmms_type', 'webtma');
        webtmaLink.searchParams.set('integration_type', 'standard');
        
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
        
        webtmaLink.searchParams.set('object_context', JSON.stringify(objectContext));
        
        return webtmaLink.toString();
    }

    // WebTMA API Communication
    async sendToWebTMA(endpoint, data) {
        if (!this.config.baseUrl || !this.config.apiKey) {
            throw new Error('WebTMA API not configured');
        }
        
        try {
            const response = await fetch(`${this.config.baseUrl}/api/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'X-Organization-ID': this.config.organizationId
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`WebTMA API error: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to send data to WebTMA:', error);
            throw error;
        }
    }

    async testConnection(config = {}) {
        try {
            const testConfig = { ...this.config, ...config };
            
            if (!testConfig.baseUrl || !testConfig.apiKey) {
                return {
                    success: false,
                    message: 'WebTMA API not configured'
                };
            }
            
            const response = await fetch(`${testConfig.baseUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${testConfig.apiKey}`,
                    'X-Organization-ID': testConfig.organizationId
                }
            });
            
            if (response.ok) {
                return {
                    success: true,
                    message: 'WebTMA connection successful'
                };
            } else {
                return {
                    success: false,
                    message: `WebTMA connection failed: ${response.status}`
                };
            }
            
        } catch (error) {
            return {
                success: false,
                message: `WebTMA connection test failed: ${error.message}`
            };
        }
    }

    // Utility methods
    extractObjectSpecs(object) {
        const specs = {};
        
        if (object.metadata) {
            // Extract common equipment specifications
            const specKeys = ['manufacturer', 'model', 'serial_number', 'capacity', 'voltage', 'amperage'];
            
            specKeys.forEach(key => {
                if (object.metadata[key]) {
                    specs[key] = object.metadata[key];
                }
            });
        }
        
        return specs;
    }

    extractPMFrequency(object) {
        const frequency = {};
        
        if (object.metadata && object.metadata.maintenance) {
            const maintenance = object.metadata.maintenance;
            
            if (maintenance.frequency) {
                frequency.value = maintenance.frequency.value;
                frequency.unit = maintenance.frequency.unit;
            }
            
            if (maintenance.lastPerformed) {
                frequency.lastPerformed = maintenance.lastPerformed;
            }
            
            if (maintenance.nextDue) {
                frequency.nextDue = maintenance.nextDue;
            }
        }
        
        return frequency;
    }

    // Event handlers
    handleWebTMAIntegration(detail) {
        this.integrate(detail);
    }

    onLinkGenerated(link) {
        // Handle link generation for WebTMA
        this.triggerEvent('linkGeneratedForWebTMA', { link });
    }

    // Public API methods
    getCapabilities() {
        return {
            name: this.options.name,
            version: this.options.version,
            supportedLinkTypes: this.options.supportedLinkTypes,
            features: [
                'work_order_integration',
                'equipment_integration',
                'pm_schedule_integration',
                'rich_text_support',
                'attachment_support',
                'api_integration'
            ]
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
                    console.error(`Error in WebTMA adapter event handler for ${event}:`, error);
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