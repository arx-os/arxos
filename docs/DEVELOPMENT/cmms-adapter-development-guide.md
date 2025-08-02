# CMMS Adapter Development Guide

## 🎯 **Overview**

This guide provides step-by-step instructions for Arxos team members to add new CMMS (Computerized Maintenance Management System) vendors to the Arxos integration system.

## 📋 **Prerequisites**

Before adding a new CMMS vendor, ensure you have:

- **CMMS Vendor Documentation**: API documentation, integration guides
- **Test Environment Access**: Sandbox/test instance of the CMMS
- **Vendor Contact**: For technical questions and support
- **Understanding of CMMS Features**: Work orders, assets, PM schedules, etc.

## 🏗️ **Architecture Overview**

The CMMS integration system uses a **pluggable adapter pattern**:

```
frontend/web/static/js/modules/cmms/
├── webtma-adapter.js        # WebTMA integration
├── generic-adapter.js       # Generic CMMS support
├── maximo-adapter.js        # Maximo integration (example)
├── sappm-adapter.js         # SAP PM integration (example)
└── [your-vendor]-adapter.js # Your new adapter
```

### **Standard Adapter Interface**

All adapters must implement this interface:

```javascript
class VendorAdapter {
    constructor(options) { /* ... */ }
    async integrate(params) { /* ... */ }
    async generateLink(params) { /* ... */ }
    async testConnection(config) { /* ... */ }
    getCapabilities() { /* ... */ }
    getConfiguration() { /* ... */ }
    updateConfiguration(newConfig) { /* ... */ }
}
```

## 🚀 **Step-by-Step Implementation Guide**

### **Step 1: Research & Analysis**

#### **1.1 Study the CMMS Vendor**
- [ ] Review vendor's API documentation
- [ ] Identify supported integration points (work orders, assets, PM schedules)
- [ ] Understand authentication methods (API keys, OAuth, etc.)
- [ ] Document URL/link requirements
- [ ] Identify vendor-specific features

#### **1.2 Create Vendor Analysis Document**
```markdown
# [Vendor Name] Analysis

## Integration Points
- Work Orders: ✅/❌
- Assets: ✅/❌
- PM Schedules: ✅/❌
- Other: [list]

## API Details
- Base URL: https://api.vendor.com
- Authentication: API Key / OAuth / Other
- Rate Limits: [document]
- API Version: [version]

## Link Requirements
- URL Format: [document]
- Required Parameters: [list]
- Optional Parameters: [list]

## Vendor-Specific Features
- [list unique features]
```

### **Step 2: Create the Adapter File**

#### **2.1 Create New Adapter File**
Create a new file: `frontend/web/static/js/modules/cmms/[vendor-name]-adapter.js`

#### **2.2 Basic Adapter Structure**
```javascript
/**
 * [Vendor Name] Adapter
 * Handles [Vendor Name]-specific CMMS integration patterns
 */

export class [VendorName]Adapter {
    constructor(options = {}) {
        this.options = {
            name: '[Vendor Name]',
            version: '1.0.0',
            supportedLinkTypes: ['work_order', 'asset', 'pm_schedule', 'standard'],
            defaultLinkFormat: 'standard',
            // Vendor-specific options
            ...options
        };
        
        // Vendor-specific configurations
        this.config = {
            baseUrl: options.baseUrl || '',
            apiKey: options.apiKey || '',
            organizationId: options.organizationId || '',
            // Add vendor-specific config options
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
        // Listen for vendor-specific events
        document.addEventListener('[vendorName]Integration', (event) => {
            this.handleVendorIntegration(event.detail);
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
                
                case 'asset':
                    return await this.integrateWithAsset(link, object, cmmsData, options);
                
                case 'pm_schedule':
                    return await this.integrateWithPMSchedule(link, object, cmmsData, options);
                
                case 'link':
                default:
                    return await this.generateStandardLink(link, object, options);
            }
            
        } catch (error) {
            console.error('[Vendor Name] integration failed:', error);
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
                
                case 'asset':
                    return await this.generateAssetLink(link, object, options);
                
                case 'pm_schedule':
                    return await this.generatePMScheduleLink(link, object, options);
                
                case 'standard':
                default:
                    return await this.generateStandardLink(link, object, options);
            }
            
        } catch (error) {
            console.error('[Vendor Name] link generation failed:', error);
            throw error;
        }
    }

    // Vendor-specific integration methods
    async integrateWithWorkOrder(link, object, cmmsData, options) {
        // Implement vendor-specific work order integration
        // See WebTMA adapter for reference implementation
    }

    async integrateWithAsset(link, object, cmmsData, options) {
        // Implement vendor-specific asset integration
    }

    async integrateWithPMSchedule(link, object, cmmsData, options) {
        // Implement vendor-specific PM schedule integration
    }

    // Link generation methods
    async generateWorkOrderLink(link, object, options) {
        // Implement vendor-specific work order link generation
    }

    async generateAssetLink(link, object, options) {
        // Implement vendor-specific asset link generation
    }

    async generatePMScheduleLink(link, object, options) {
        // Implement vendor-specific PM schedule link generation
    }

    async generateStandardLink(link, object, options) {
        // Implement vendor-specific standard link generation
    }

    // Vendor API communication
    async sendToVendor(endpoint, data) {
        // Implement vendor-specific API communication
    }

    async testConnection(config = {}) {
        // Implement vendor-specific connection testing
    }

    // Event handlers
    handleVendorIntegration(detail) {
        this.integrate(detail);
    }

    onLinkGenerated(link) {
        // Handle link generation for vendor
        this.triggerEvent('linkGeneratedForVendor', { link });
    }

    // Public API methods
    getCapabilities() {
        return {
            name: this.options.name,
            version: this.options.version,
            supportedLinkTypes: this.options.supportedLinkTypes,
            features: [
                'work_order_integration',
                'asset_integration',
                'pm_schedule_integration',
                // Add vendor-specific features
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
                    console.error(`Error in [Vendor Name] adapter event handler for ${event}:`, error);
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
```

### **Step 3: Register the Adapter**

#### **3.1 Update CMMS Integration Manager**
Add your adapter to `frontend/web/static/js/modules/cmms-integration-manager.js`:

```javascript
async initializeAdapters() {
    // ... existing adapters ...
    
    // Add your new adapter
    if (this.options.enable[YourVendor]) {
        try {
            const { [YourVendor]Adapter } = await import('./cmms/[vendor-name]-adapter.js');
            this.adapters.set('[vendor-name]', new [YourVendor]Adapter());
        } catch (error) {
            console.warn('[Your Vendor] adapter not available:', error);
        }
    }
}
```

#### **3.2 Add Configuration Options**
Update the constructor options in the integration manager:

```javascript
constructor(options = {}) {
    this.options = {
        enableWebTMA: options.enableWebTMA !== false,
        enableMaximo: options.enableMaximo !== false,
        enableSAPPM: options.enableSAPPM !== false,
        enableGeneric: options.enableGeneric !== false,
        enable[YourVendor]: options.enable[YourVendor] !== false, // Add this
        defaultAccessType: options.defaultAccessType || 'public',
        enableAnalytics: options.enableAnalytics !== false,
        ...options
    };
    // ... rest of constructor
}
```

### **Step 4: Implement Vendor-Specific Methods**

#### **4.1 Work Order Integration Example**
```javascript
async integrateWithWorkOrder(link, object, cmmsData, options) {
    const {
        workOrderId,
        workOrderNumber,
        description,
        priority = 'normal',
        status = 'open'
    } = cmmsData;
    
    try {
        // Generate vendor-specific link
        const workOrderLink = await this.generateWorkOrderLink(link, object, {
            workOrderId,
            workOrderNumber,
            ...options
        });
        
        // Create integration data
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
        
        // Send to vendor API if configured
        if (this.config.baseUrl && this.config.apiKey) {
            await this.sendToVendor('work_orders', integrationData);
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
```

#### **4.2 Link Generation Example**
```javascript
async generateWorkOrderLink(link, object, options) {
    const {
        workOrderId,
        workOrderNumber,
        includeDescription = true,
        includeLocation = true
    } = options;
    
    // Create vendor-specific link format
    const vendorLink = new URL(link.url);
    
    // Add vendor-specific parameters
    vendorLink.searchParams.set('cmms_type', '[vendor-name]');
    vendorLink.searchParams.set('integration_type', 'work_order');
    
    if (workOrderId) {
        vendorLink.searchParams.set('work_order_id', workOrderId);
    }
    
    if (workOrderNumber) {
        vendorLink.searchParams.set('work_order_number', workOrderNumber);
    }
    
    // Add object context
    vendorLink.searchParams.set('object_context', JSON.stringify({
        id: object.id,
        type: object.object_type,
        building: object.building_id,
        floor: object.floor_id,
        description: includeDescription ? `${object.object_type} ${object.id}` : '',
        location: includeLocation ? `${object.building_id} - ${object.floor_id}` : ''
    }));
    
    return vendorLink.toString();
}
```

#### **4.3 API Communication Example**
```javascript
async sendToVendor(endpoint, data) {
    if (!this.config.baseUrl || !this.config.apiKey) {
        throw new Error('[Vendor Name] API not configured');
    }
    
    try {
        const response = await fetch(`${this.config.baseUrl}/api/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.config.apiKey}`,
                'X-Organization-ID': this.config.organizationId,
                // Add vendor-specific headers
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`[Vendor Name] API error: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Failed to send data to [Vendor Name]:', error);
        throw error;
    }
}
```

### **Step 5: Testing & Validation**

#### **5.1 Unit Testing**
Create test file: `tests/cmms/[vendor-name]-adapter.test.js`

```javascript
import { [VendorName]Adapter } from '../../frontend/web/static/js/modules/cmms/[vendor-name]-adapter.js';

describe('[Vendor Name] Adapter', () => {
    let adapter;
    
    beforeEach(() => {
        adapter = new [VendorName]Adapter({
            baseUrl: 'https://test-api.vendor.com',
            apiKey: 'test-api-key'
        });
    });
    
    test('should generate work order link', async () => {
        const link = await adapter.generateWorkOrderLink(
            { url: 'https://app.arxos.io/viewer' },
            { id: 'test-object', object_type: 'AHU', building_id: 'building-1', floor_id: 'floor-1' },
            { workOrderId: 'WO-123' }
        );
        
        expect(link).toContain('cmms_type=[vendor-name]');
        expect(link).toContain('work_order_id=WO-123');
    });
    
    test('should test connection', async () => {
        const result = await adapter.testConnection({
            baseUrl: 'https://test-api.vendor.com',
            apiKey: 'test-api-key'
        });
        
        expect(result.success).toBe(true);
    });
});
```

#### **5.2 Integration Testing**
```javascript
// Test with real vendor API
async function testVendorIntegration() {
    const adapter = new [VendorName]Adapter({
        baseUrl: 'https://api.vendor.com',
        apiKey: 'your-api-key'
    });
    
    // Test connection
    const connectionResult = await adapter.testConnection();
    console.log('Connection test:', connectionResult);
    
    // Test link generation
    const link = await adapter.generateWorkOrderLink(
        { url: 'https://app.arxos.io/viewer' },
        { id: 'test-object', object_type: 'AHU', building_id: 'building-1', floor_id: 'floor-1' },
        { workOrderId: 'WO-123' }
    );
    console.log('Generated link:', link);
    
    // Test integration
    const integrationResult = await adapter.integrate({
        link: { url: 'https://app.arxos.io/viewer' },
        object: { id: 'test-object', object_type: 'AHU', building_id: 'building-1', floor_id: 'floor-1' },
        integrationType: 'work_order',
        cmmsData: { workOrderId: 'WO-123', workOrderNumber: 'WO-123-001' }
    });
    console.log('Integration result:', integrationResult);
}
```

### **Step 6: Documentation**

#### **6.1 Create Vendor Documentation**
Create: `docs/cmms/[vendor-name]-integration.md`

```markdown
# [Vendor Name] Integration Guide

## Overview
[Brief description of the vendor and integration]

## Configuration
```javascript
const config = {
    baseUrl: 'https://api.vendor.com',
    apiKey: 'your-api-key',
    organizationId: 'your-org-id'
};
```

## Supported Features
- ✅ Work Order Integration
- ✅ Asset Integration
- ✅ PM Schedule Integration
- ❌ [Unsupported features]

## Usage Examples

### Work Order Integration
```javascript
const result = await cmmsManager.integrateWith[VendorName]({
    objectId: 'ahu-3',
    integrationType: 'work_order',
    cmmsData: {
        workOrderId: 'WO-123',
        workOrderNumber: 'WO-123-001',
        description: 'AHU-3 Maintenance'
    }
});
```

### Link Generation
```javascript
const link = await cmmsManager.generateCMMSLink({
    cmmsType: '[vendor-name]',
    objectId: 'ahu-3',
    linkType: 'work_order',
    options: {
        workOrderId: 'WO-123'
    }
});
```

## API Reference
[Document vendor-specific API endpoints and parameters]

## Troubleshooting
[Common issues and solutions]
```

#### **6.2 Update Main Documentation**
Update `docs/DEVELOPMENT/cmms-integration-implementation-summary.md` to include your new vendor.

### **Step 7: Deployment**

#### **7.1 Add to Integration Manager**
Ensure your adapter is properly registered in the integration manager.

#### **7.2 Configuration Management**
Add vendor configuration to the database:

```sql
INSERT INTO cmms_integration_config (
    id, cmms_type, organization_id, config_data, is_active
) VALUES (
    '[vendor-name]-prod',
    '[vendor-name]',
    'org-123',
    '{"baseUrl": "https://api.vendor.com", "apiKey": "your-api-key"}',
    true
);
```

#### **7.3 Enable in Application**
```javascript
// In your application initialization
const cmmsManager = new CMMSIntegrationManager({
    enable[YourVendor]: true,
    // other options...
});
```

## 🧪 **Testing Checklist**

### **Unit Tests**
- [ ] Adapter instantiation
- [ ] Link generation for each type
- [ ] Integration methods
- [ ] Configuration management
- [ ] Error handling

### **Integration Tests**
- [ ] Connection testing
- [ ] API communication
- [ ] Link consumption
- [ ] End-to-end workflows

### **Performance Tests**
- [ ] Link generation speed
- [ ] API response times
- [ ] Memory usage
- [ ] Error recovery

## 📚 **Reference Implementations**

### **WebTMA Adapter**
- **File**: `frontend/web/static/js/modules/cmms/webtma-adapter.js`
- **Features**: Work orders, equipment, PM schedules
- **Use as**: Reference for complex integrations

### **Generic Adapter**
- **File**: `frontend/web/static/js/modules/cmms/generic-adapter.js`
- **Features**: Template support, custom fields
- **Use as**: Reference for flexible integrations

## 🚨 **Common Pitfalls**

### **1. Not Following the Interface**
- **Problem**: Adapter doesn't implement required methods
- **Solution**: Ensure all interface methods are implemented

### **2. Poor Error Handling**
- **Problem**: Errors not properly caught and reported
- **Solution**: Wrap all async operations in try-catch blocks

### **3. Missing Event Handling**
- **Problem**: Adapter doesn't trigger events
- **Solution**: Use `triggerEvent()` for important operations

### **4. Hardcoded Values**
- **Problem**: Vendor-specific values hardcoded
- **Solution**: Use configuration options for flexibility

### **5. No Testing**
- **Problem**: Adapter not tested before deployment
- **Solution**: Create comprehensive tests

## 🎯 **Success Criteria**

Your adapter is ready for production when:

- [ ] All required interface methods implemented
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Error handling comprehensive
- [ ] Performance acceptable
- [ ] Security reviewed
- [ ] Code reviewed by team

## 📞 **Getting Help**

### **Internal Resources**
- **Team Lead**: [Contact info]
- **Senior Developers**: [Contact info]
- **Architecture Team**: [Contact info]

### **External Resources**
- **Vendor Documentation**: [Links]
- **API Support**: [Contact info]
- **Community Forums**: [Links]

This guide provides everything needed to add a new CMMS vendor to the Arxos integration system. Follow the steps carefully and don't hesitate to ask for help when needed! 