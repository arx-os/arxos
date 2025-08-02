# CMMS Adapter Quick Reference

## 🚀 **Quick Start: Add New CMMS Vendor**

### **1. Create Adapter File**
```bash
# Create new adapter file
touch frontend/web/static/js/modules/cmms/[vendor-name]-adapter.js
```

### **2. Copy Template Structure**
```javascript
export class [VendorName]Adapter {
    constructor(options = {}) {
        this.options = {
            name: '[Vendor Name]',
            version: '1.0.0',
            supportedLinkTypes: ['work_order', 'asset', 'pm_schedule', 'standard'],
            ...options
        };
        
        this.config = {
            baseUrl: options.baseUrl || '',
            apiKey: options.apiKey || '',
            organizationId: options.organizationId || '',
            ...options
        };
        
        this.eventHandlers = new Map();
        this.initialize();
    }

    // Required methods to implement:
    async integrate(params) { /* ... */ }
    async generateLink(params) { /* ... */ }
    async testConnection(config) { /* ... */ }
    getCapabilities() { /* ... */ }
    getConfiguration() { /* ... */ }
    updateConfiguration(newConfig) { /* ... */ }
}
```

### **3. Register in Integration Manager**
```javascript
// In cmms-integration-manager.js
async initializeAdapters() {
    // Add your adapter
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

### **4. Add Configuration Option**
```javascript
// In cmms-integration-manager.js constructor
this.options = {
    enableWebTMA: options.enableWebTMA !== false,
    enable[YourVendor]: options.enable[YourVendor] !== false, // Add this
    // ... other options
};
```

## 📋 **Required Interface Methods**

### **Core Methods**
```javascript
// Main integration method
async integrate(params) {
    const { link, object, integrationType, cmmsData, options } = params;
    // Implement vendor-specific integration
}

// Link generation method
async generateLink(params) {
    const { link, object, linkType, options } = params;
    // Implement vendor-specific link generation
}

// Connection testing
async testConnection(config = {}) {
    // Test connection to vendor API
    return { success: true/false, message: '...' };
}
```

### **Configuration Methods**
```javascript
// Get adapter capabilities
getCapabilities() {
    return {
        name: this.options.name,
        version: this.options.version,
        supportedLinkTypes: this.options.supportedLinkTypes,
        features: ['work_order_integration', 'asset_integration', ...]
    };
}

// Get current configuration
getConfiguration() {
    return { ...this.config, name: this.options.name, version: this.options.version };
}

// Update configuration
updateConfiguration(newConfig) {
    this.config = { ...this.config, ...newConfig };
    this.triggerEvent('configurationUpdated', { config: this.config });
}
```

## 🔧 **Common Implementation Patterns**

### **Work Order Integration**
```javascript
async integrateWithWorkOrder(link, object, cmmsData, options) {
    const { workOrderId, workOrderNumber, description } = cmmsData;
    
    // Generate vendor-specific link
    const workOrderLink = await this.generateWorkOrderLink(link, object, {
        workOrderId, workOrderNumber, ...options
    });
    
    // Send to vendor API
    if (this.config.baseUrl && this.config.apiKey) {
        await this.sendToVendor('work_orders', {
            workOrderId, arxosLink: workOrderLink, object
        });
    }
    
    return { success: true, type: 'work_order', workOrderId, link: workOrderLink };
}
```

### **Link Generation**
```javascript
async generateWorkOrderLink(link, object, options) {
    const vendorLink = new URL(link.url);
    vendorLink.searchParams.set('cmms_type', '[vendor-name]');
    vendorLink.searchParams.set('integration_type', 'work_order');
    
    if (options.workOrderId) {
        vendorLink.searchParams.set('work_order_id', options.workOrderId);
    }
    
    vendorLink.searchParams.set('object_context', JSON.stringify({
        id: object.id, type: object.object_type,
        building: object.building_id, floor: object.floor_id
    }));
    
    return vendorLink.toString();
}
```

### **API Communication**
```javascript
async sendToVendor(endpoint, data) {
    if (!this.config.baseUrl || !this.config.apiKey) {
        throw new Error('[Vendor Name] API not configured');
    }
    
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
        throw new Error(`[Vendor Name] API error: ${response.status}`);
    }
    
    return await response.json();
}
```

## 🧪 **Testing Checklist**

### **Unit Tests**
```javascript
// tests/cmms/[vendor-name]-adapter.test.js
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

### **Integration Tests**
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

## 📚 **Reference Files**

### **Working Examples**
- **WebTMA**: `frontend/web/static/js/modules/cmms/webtma-adapter.js`
- **Generic**: `frontend/web/static/js/modules/cmms/generic-adapter.js`

### **Documentation**
- **Full Guide**: `docs/DEVELOPMENT/cmms-adapter-development-guide.md`
- **Implementation Summary**: `docs/DEVELOPMENT/cmms-integration-implementation-summary.md`

## 🚨 **Common Issues**

### **1. Adapter Not Loading**
- Check file path: `frontend/web/static/js/modules/cmms/[vendor-name]-adapter.js`
- Verify class name matches file name
- Check import statement in integration manager

### **2. Configuration Not Working**
- Ensure all required config options are in constructor
- Check API credentials are correct
- Verify base URL is accessible

### **3. Link Generation Failing**
- Validate URL parameters
- Check object data structure
- Ensure proper error handling

### **4. API Communication Issues**
- Verify API endpoint URLs
- Check authentication headers
- Validate request/response format

## 🎯 **Success Criteria**

Your adapter is ready when:
- [ ] All required methods implemented
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Error handling comprehensive
- [ ] Performance acceptable
- [ ] Code reviewed

## 📞 **Need Help?**

1. **Check existing adapters** for reference implementation
2. **Review full development guide** for detailed instructions
3. **Ask team lead** for architecture questions
4. **Contact vendor** for API-specific issues

---

**Time Estimate**: 4-6 days for complete implementation
**Difficulty**: Medium (requires vendor API knowledge)
**Dependencies**: Vendor API access and documentation 