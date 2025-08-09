/**
 * Validation Module
 * Handles data validation for export/import operations
 */

export class Validation {
    constructor(options = {}) {
        this.options = {
            strictValidation: true,
            validateSchema: true,
            maxFileSize: 50 * 1024 * 1024, // 50MB
            maxObjectCount: 10000,
            allowedObjectTypes: ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text'],
            ...options
        };

        // Validation schemas
        this.schemas = new Map();

        // Validation rules
        this.rules = new Map();

        this.initialize();
    }

    initialize() {
        this.registerSchemas();
        this.registerRules();
    }

    registerSchemas() {
        // Version schema
        this.schemas.set('version', {
            type: 'object',
            required: ['id', 'objects'],
            properties: {
                id: { type: 'string' },
                name: { type: 'string' },
                objects: { type: 'array' },
                metadata: { type: 'object' },
                timestamp: { type: 'string' }
            }
        });

        // Floor schema
        this.schemas.set('floor', {
            type: 'object',
            required: ['id', 'name'],
            properties: {
                id: { type: 'string' },
                name: { type: 'string' },
                versions: { type: 'array' },
                metadata: { type: 'object' },
                timestamp: { type: 'string' }
            }
        });

        // Object schema
        this.schemas.set('object', {
            type: 'object',
            required: ['id', 'type'],
            properties: {
                id: { type: 'string' },
                type: { type: 'string' },
                attributes: { type: 'object' },
                content: { type: 'string' }
            }
        });

        // Backup schema
        this.schemas.set('backup', {
            type: 'object',
            required: ['type', 'backupInfo'],
            properties: {
                type: { type: 'string', enum: ['version_backup', 'floor_backup'] },
                backupInfo: { type: 'object' },
                version: { type: 'object' },
                floor: { type: 'object' },
                metadata: { type: 'object' },
                assets: { type: 'array' }
            }
        });
    }

    registerRules() {
        // File size validation
        this.rules.set('fileSize', (file) => {
            if (file.size > this.options.maxFileSize) {
                throw new Error(`File size (${file.size} bytes) exceeds maximum allowed size (${this.options.maxFileSize} bytes)`);
            }
            return true;
        });

        // Object count validation
        this.rules.set('objectCount', (objects) => {
            if (objects.length > this.options.maxObjectCount) {
                throw new Error(`Object count (${objects.length}) exceeds maximum allowed count (${this.options.maxObjectCount})`);
            }
            return true;
        });

        // Object type validation
        this.rules.set('objectTypes', (objects) => {
            for (const obj of objects) {
                if (!this.options.allowedObjectTypes.includes(obj.type)) {
                    throw new Error(`Invalid object type: ${obj.type}`);
                }
            }
            return true;
        });

        // ID validation
        this.rules.set('idFormat', (id) => {
            if (!id || typeof id !== 'string' || id.length === 0) {
                throw new Error('Invalid ID format');
            }
            if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
                throw new Error('ID contains invalid characters');
            }
            return true;
        });

        // Coordinate validation
        this.rules.set('coordinates', (objects) => {
            for (const obj of objects) {
                if (obj.attributes) {
                    const x = parseFloat(obj.attributes.x);
                    const y = parseFloat(obj.attributes.y);

                    if (isNaN(x) || isNaN(y)) {
                        throw new Error(`Invalid coordinates for object ${obj.id}`);
                    }

                    if (x < -10000 || x > 10000 || y < -10000 || y > 10000) {
                        throw new Error(`Coordinates out of range for object ${obj.id}`);
                    }
                }
            }
            return true;
        });
    }

    // Main validation methods
    validateImportData(data, options = {}) {
        const { validateSchema = true, validateRules = true } = options;

        try {
            // Basic structure validation
            this.validateBasicStructure(data);

            // Schema validation
            if (validateSchema && this.options.validateSchema) {
                this.validateSchema(data);
            }

            // Rules validation
            if (validateRules) {
                this.validateRules(data);
            }

            return true;
        } catch (error) {
            throw new Error(`Import validation failed: ${error.message}`);
        }
    }

    validateExportData(data, options = {}) {
        const { validateSchema = true, validateRules = true } = options;

        try {
            // Basic structure validation
            this.validateBasicStructure(data);

            // Schema validation
            if (validateSchema && this.options.validateSchema) {
                this.validateSchema(data);
            }

            // Rules validation
            if (validateRules) {
                this.validateRules(data);
            }

            return true;
        } catch (error) {
            throw new Error(`Export validation failed: ${error.message}`);
        }
    }

    validateBackup(backupData, options = {}) {
        const { validateSchema = true, validateRules = true } = options;

        try {
            // Basic structure validation
            this.validateBasicStructure(backupData);

            // Schema validation
            if (validateSchema && this.options.validateSchema) {
                this.validateBackupSchema(backupData);
            }

            // Rules validation
            if (validateRules) {
                this.validateBackupRules(backupData);
            }

            return true;
        } catch (error) {
            throw new Error(`Backup validation failed: ${error.message}`);
        }
    }

    // Structure validation
    validateBasicStructure(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Data must be an object');
        }

        if (Array.isArray(data)) {
            throw new Error('Data must be an object, not an array');
        }
    }

    validateSchema(data) {
        // Determine schema type based on data structure
        let schemaType = null;

        if (data.version) {
            schemaType = 'version';
        } else if (data.floor) {
            schemaType = 'floor';
        } else if (data.type && data.backupInfo) {
            schemaType = 'backup';
        } else {
            throw new Error('Unable to determine data schema type');
        }

        const schema = this.schemas.get(schemaType);
        if (!schema) {
            throw new Error(`No schema found for type: ${schemaType}`);
        }

        this.validateAgainstSchema(data, schema, schemaType);
    }

    validateBackupSchema(backupData) {
        const schema = this.schemas.get('backup');
        this.validateAgainstSchema(backupData, schema, 'backup');
    }

    validateAgainstSchema(data, schema, schemaName) {
        // Check required fields
        if (schema.required) {
            for (const field of schema.required) {
                if (!(field in data)) {
                    throw new Error(`Missing required field: ${field}`);
                }
            }
        }

        // Check field types
        if (schema.properties) {
            for (const [field, value] of Object.entries(data)) {
                const propertySchema = schema.properties[field];
                if (propertySchema) {
                    this.validateFieldType(value, propertySchema, field);
                }
            }
        }

        // Check enum values
        if (schema.properties) {
            for (const [field, value] of Object.entries(data)) {
                const propertySchema = schema.properties[field];
                if (propertySchema && propertySchema.enum) {
                    if (!propertySchema.enum.includes(value)) {
                        throw new Error(`Invalid value for ${field}: ${value}`);
                    }
                }
            }
        }
    }

    validateFieldType(value, schema, fieldName) {
        const expectedType = schema.type;

        switch (expectedType) {
            case 'string':
                if (typeof value !== 'string') {
                    throw new Error(`Field ${fieldName} must be a string`);
                }
                break;
            case 'number':
                if (typeof value !== 'number' || isNaN(value)) {
                    throw new Error(`Field ${fieldName} must be a number`);
                }
                break;
            case 'boolean':
                if (typeof value !== 'boolean') {
                    throw new Error(`Field ${fieldName} must be a boolean`);
                }
                break;
            case 'object':
                if (typeof value !== 'object' || value === null || Array.isArray(value)) {
                    throw new Error(`Field ${fieldName} must be an object`);
                }
                break;
            case 'array':
                if (!Array.isArray(value)) {
                    throw new Error(`Field ${fieldName} must be an array`);
                }
                break;
            default:
                throw new Error(`Unknown schema type: ${expectedType}`);
        }
    }

    // Rules validation
    validateRules(data) {
        // Validate IDs
        this.validateIds(data);

        // Validate objects if present
        if (data.objects) {
            this.rules.get('objectCount')(data.objects);
            this.rules.get('objectTypes')(data.objects);
            this.rules.get('coordinates')(data.objects);
        }

        // Validate version objects if present
        if (data.version && data.version.objects) {
            this.rules.get('objectCount')(data.version.objects);
            this.rules.get('objectTypes')(data.version.objects);
            this.rules.get('coordinates')(data.version.objects);
        }
    }

    validateBackupRules(backupData) {
        // Validate backup-specific rules
        if (backupData.type === 'version_backup' && backupData.version) {
            if (backupData.version.objects) {
                this.rules.get('objectCount')(backupData.version.objects);
                this.rules.get('objectTypes')(backupData.version.objects);
                this.rules.get('coordinates')(backupData.version.objects);
            }
        }

        if (backupData.type === 'floor_backup' && backupData.versions) {
            for (const version of backupData.versions) {
                if (version.objects) {
                    this.rules.get('objectCount')(version.objects);
                    this.rules.get('objectTypes')(version.objects);
                    this.rules.get('coordinates')(version.objects);
                }
            }
        }
    }

    validateIds(data) {
        // Validate main ID
        if (data.id) {
            this.rules.get('idFormat')(data.id);
        }

        // Validate version ID
        if (data.version && data.version.id) {
            this.rules.get('idFormat')(data.version.id);
        }

        // Validate floor ID
        if (data.floor && data.floor.id) {
            this.rules.get('idFormat')(data.floor.id);
        }

        // Validate object IDs
        if (data.objects) {
            for (const obj of data.objects) {
                if (obj.id) {
                    this.rules.get('idFormat')(obj.id);
                }
            }
        }
    }

    // File validation
    validateFile(file, options = {}) {
        const { validateSize = true, validateType = true } = options;

        try {
            if (!file) {
                throw new Error('No file provided');
            }

            if (validateSize) {
                this.rules.get('fileSize')(file);
            }

            if (validateType) {
                this.validateFileType(file);
            }

            return true;
        } catch (error) {
            throw new Error(`File validation failed: ${error.message}`);
        }
    }

    validateFileType(file) {
        const allowedTypes = [
            'application/json',
            'image/svg+xml',
            'application/zip',
            'image/png',
            'application/pdf'
        ];

        if (!allowedTypes.includes(file.type)) {
            throw new Error(`Unsupported file type: ${file.type}`);
        }
    }

    // Specific validation methods
    validateVersionData(versionData) {
        if (!versionData.id) {
            throw new Error('Version data must contain an ID');
        }

        if (!versionData.objects || !Array.isArray(versionData.objects)) {
            throw new Error('Version data must contain objects array');
        }

        this.rules.get('idFormat')(versionData.id);
        this.rules.get('objectCount')(versionData.objects);
        this.rules.get('objectTypes')(versionData.objects);
        this.rules.get('coordinates')(versionData.objects);
    }

    validateFloorData(floorData) {
        if (!floorData.id) {
            throw new Error('Floor data must contain an ID');
        }

        if (!floorData.name) {
            throw new Error('Floor data must contain a name');
        }

        this.rules.get('idFormat')(floorData.id);

        if (floorData.versions && Array.isArray(floorData.versions)) {
            for (const version of floorData.versions) {
                this.validateVersionData(version);
            }
        }
    }

    validateObjectData(objectData) {
        if (!objectData.id) {
            throw new Error('Object data must contain an ID');
        }

        if (!objectData.type) {
            throw new Error('Object data must contain a type');
        }

        this.rules.get('idFormat')(objectData.id);

        if (!this.options.allowedObjectTypes.includes(objectData.type)) {
            throw new Error(`Invalid object type: ${objectData.type}`);
        }
    }

    // Validation utilities
    isValidId(id) {
        try {
            this.rules.get('idFormat')(id);
            return true;
        } catch {
            return false;
        }
    }

    isValidObjectType(type) {
        return this.options.allowedObjectTypes.includes(type);
    }

    isValidFileSize(size) {
        return size <= this.options.maxFileSize;
    }

    isValidObjectCount(count) {
        return count <= this.options.maxObjectCount;
    }

    // Schema utilities
    getSchema(type) {
        return this.schemas.get(type);
    }

    registerSchema(type, schema) {
        this.schemas.set(type, schema);
    }

    // Rule utilities
    getRule(name) {
        return this.rules.get(name);
    }

    registerRule(name, rule) {
        this.rules.set(name, rule);
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers) {
            this.eventHandlers = new Map();
        }
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, validation: this });
                } catch (error) {
                    console.error(`Error in validation event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.schemas.clear();
        this.rules.clear();

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
