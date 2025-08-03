/**
 * ArxObject System - Building Information Modeling
 * Represents every building component as data with measurements, relationships, and constraints
 * 
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class ArxObjectSystem {
    constructor() {
        this.arxObjects = new Map();
        this.objectTypes = new Map();
        this.relationships = new Map();
        this.constraints = new Map();
        this.measurements = new Map();
        
        // Initialize object types
        this.initializeObjectTypes();
        
        // Initialize relationships
        this.initializeRelationships();
        
        // Initialize constraints
        this.initializeConstraints();
    }
    
    /**
     * Initialize ArxObject types
     */
    initializeObjectTypes() {
        // Structural Elements
        this.objectTypes.set('wall', {
            name: 'Wall',
            category: 'structural',
            properties: ['thickness', 'height', 'material', 'fireRating', 'insulation'],
            measurements: ['length', 'area', 'volume'],
            constraints: ['perpendicular', 'parallel', 'distance']
        });
        
        this.objectTypes.set('floor', {
            name: 'Floor',
            category: 'structural',
            properties: ['thickness', 'material', 'finish', 'subfloor'],
            measurements: ['area', 'volume'],
            constraints: ['level', 'slope']
        });
        
        this.objectTypes.set('ceiling', {
            name: 'Ceiling',
            category: 'structural',
            properties: ['height', 'material', 'finish', 'acoustic'],
            measurements: ['area'],
            constraints: ['height', 'level']
        });
        
        this.objectTypes.set('column', {
            name: 'Column',
            category: 'structural',
            properties: ['diameter', 'material', 'fireRating', 'loadCapacity'],
            measurements: ['height', 'volume'],
            constraints: ['vertical', 'spacing']
        });
        
        this.objectTypes.set('beam', {
            name: 'Beam',
            category: 'structural',
            properties: ['width', 'height', 'material', 'loadCapacity'],
            measurements: ['length', 'volume'],
            constraints: ['horizontal', 'spacing']
        });
        
        // Openings
        this.objectTypes.set('door', {
            name: 'Door',
            category: 'opening',
            properties: ['width', 'height', 'thickness', 'material', 'type', 'hardware'],
            measurements: ['area', 'clearance'],
            constraints: ['width', 'height', 'clearance']
        });
        
        this.objectTypes.set('window', {
            name: 'Window',
            category: 'opening',
            properties: ['width', 'height', 'type', 'glazing', 'frame'],
            measurements: ['area', 'glazingArea'],
            constraints: ['width', 'height', 'sillHeight']
        });
        
        this.objectTypes.set('opening', {
            name: 'Opening',
            category: 'opening',
            properties: ['width', 'height', 'type'],
            measurements: ['area'],
            constraints: ['width', 'height']
        });
        
        // MEP Systems
        this.objectTypes.set('electrical_outlet', {
            name: 'Electrical Outlet',
            category: 'electrical',
            properties: ['type', 'voltage', 'amperage', 'circuit'],
            measurements: ['height'],
            constraints: ['height', 'spacing']
        });
        
        this.objectTypes.set('light_fixture', {
            name: 'Light Fixture',
            category: 'electrical',
            properties: ['type', 'wattage', 'color', 'mounting'],
            measurements: ['height'],
            constraints: ['height', 'spacing']
        });
        
        this.objectTypes.set('hvac_register', {
            name: 'HVAC Register',
            category: 'mechanical',
            properties: ['type', 'size', 'airflow'],
            measurements: ['area'],
            constraints: ['size', 'spacing']
        });
        
        this.objectTypes.set('plumbing_fixture', {
            name: 'Plumbing Fixture',
            category: 'plumbing',
            properties: ['type', 'size', 'material'],
            measurements: ['area'],
            constraints: ['clearance', 'spacing']
        });
        
        // Interior Elements
        this.objectTypes.set('room', {
            name: 'Room',
            category: 'interior',
            properties: ['type', 'function', 'occupancy'],
            measurements: ['area', 'perimeter', 'volume'],
            constraints: ['area', 'clearance']
        });
        
        this.objectTypes.set('furniture', {
            name: 'Furniture',
            category: 'interior',
            properties: ['type', 'material', 'finish'],
            measurements: ['area', 'volume'],
            constraints: ['clearance', 'spacing']
        });
        
        // Site Elements
        this.objectTypes.set('site_boundary', {
            name: 'Site Boundary',
            category: 'site',
            properties: ['type', 'zoning'],
            measurements: ['area', 'perimeter'],
            constraints: ['setback', 'coverage']
        });
        
        this.objectTypes.set('parking_space', {
            name: 'Parking Space',
            category: 'site',
            properties: ['type', 'size'],
            measurements: ['area'],
            constraints: ['size', 'spacing']
        });
    }
    
    /**
     * Initialize relationship types
     */
    initializeRelationships() {
        // Structural relationships
        this.relationships.set('connected', {
            name: 'Connected',
            description: 'Objects are physically connected',
            bidirectional: true
        });
        
        this.relationships.set('supported_by', {
            name: 'Supported By',
            description: 'One object supports another',
            bidirectional: false
        });
        
        this.relationships.set('contains', {
            name: 'Contains',
            description: 'One object contains another',
            bidirectional: false
        });
        
        this.relationships.set('adjacent', {
            name: 'Adjacent',
            description: 'Objects are adjacent to each other',
            bidirectional: true
        });
        
        this.relationships.set('parallel', {
            name: 'Parallel',
            description: 'Objects are parallel to each other',
            bidirectional: true
        });
        
        this.relationships.set('perpendicular', {
            name: 'Perpendicular',
            description: 'Objects are perpendicular to each other',
            bidirectional: true
        });
        
        // MEP relationships
        this.relationships.set('served_by', {
            name: 'Served By',
            description: 'One object is served by another (e.g., outlet served by panel)',
            bidirectional: false
        });
        
        this.relationships.set('connected_to', {
            name: 'Connected To',
            description: 'MEP objects are connected to each other',
            bidirectional: true
        });
        
        // Spatial relationships
        this.relationships.set('above', {
            name: 'Above',
            description: 'One object is above another',
            bidirectional: false
        });
        
        this.relationships.set('below', {
            name: 'Below',
            description: 'One object is below another',
            bidirectional: false
        });
        
        this.relationships.set('inside', {
            name: 'Inside',
            description: 'One object is inside another',
            bidirectional: false
        });
        
        this.relationships.set('outside', {
            name: 'Outside',
            description: 'One object is outside another',
            bidirectional: false
        });
    }
    
    /**
     * Initialize constraint types
     */
    initializeConstraints() {
        // Geometric constraints
        this.constraints.set('distance', {
            name: 'Distance',
            description: 'Distance between objects or points',
            parameters: ['value', 'tolerance'],
            unit: 'inches'
        });
        
        this.constraints.set('angle', {
            name: 'Angle',
            description: 'Angle between objects',
            parameters: ['value', 'tolerance'],
            unit: 'degrees'
        });
        
        this.constraints.set('parallel', {
            name: 'Parallel',
            description: 'Objects must be parallel',
            parameters: ['tolerance'],
            unit: 'degrees'
        });
        
        this.constraints.set('perpendicular', {
            name: 'Perpendicular',
            description: 'Objects must be perpendicular',
            parameters: ['tolerance'],
            unit: 'degrees'
        });
        
        // Size constraints
        this.constraints.set('width', {
            name: 'Width',
            description: 'Width constraint',
            parameters: ['value', 'tolerance'],
            unit: 'inches'
        });
        
        this.constraints.set('height', {
            name: 'Height',
            description: 'Height constraint',
            parameters: ['value', 'tolerance'],
            unit: 'inches'
        });
        
        this.constraints.set('length', {
            name: 'Length',
            description: 'Length constraint',
            parameters: ['value', 'tolerance'],
            unit: 'inches'
        });
        
        this.constraints.set('area', {
            name: 'Area',
            description: 'Area constraint',
            parameters: ['value', 'tolerance'],
            unit: 'square_inches'
        });
        
        // Code constraints
        this.constraints.set('clearance', {
            name: 'Clearance',
            description: 'Required clearance around object',
            parameters: ['value'],
            unit: 'inches'
        });
        
        this.constraints.set('spacing', {
            name: 'Spacing',
            description: 'Required spacing between objects',
            parameters: ['value'],
            unit: 'inches'
        });
        
        this.constraints.set('setback', {
            name: 'Setback',
            description: 'Required setback from property line',
            parameters: ['value'],
            unit: 'inches'
        });
        
        this.constraints.set('coverage', {
            name: 'Coverage',
            description: 'Maximum site coverage percentage',
            parameters: ['value'],
            unit: 'percentage'
        });
    }
    
    /**
     * Create a new ArxObject
     */
    createArxObject(type, geometry, properties = {}) {
        const objectType = this.objectTypes.get(type);
        if (!objectType) {
            throw new Error(`Unknown ArxObject type: ${type}`);
        }
        
        const id = this.generateObjectId();
        
        const arxObject = {
            id: id,
            type: type,
            geometry: geometry,
            properties: {
                ...this.getDefaultProperties(type),
                ...properties
            },
            relationships: [],
            constraints: [],
            measurements: [],
            metadata: {
                created: Date.now(),
                modified: Date.now(),
                version: '1.0.0'
            }
        };
        
        // Calculate initial measurements
        this.calculateMeasurements(arxObject);
        
        // Add to system
        this.arxObjects.set(id, arxObject);
        
        console.log('Created ArxObject:', arxObject);
        return arxObject;
    }
    
    /**
     * Get default properties for object type
     */
    getDefaultProperties(type) {
        const defaults = {
            wall: {
                thickness: 6,
                height: 96,
                material: 'drywall',
                fireRating: '1-hour',
                insulation: 'R-13'
            },
            door: {
                width: 36,
                height: 80,
                thickness: 1.75,
                material: 'wood',
                type: 'swing',
                hardware: 'standard'
            },
            window: {
                width: 36,
                height: 48,
                type: 'fixed',
                glazing: 'double',
                frame: 'aluminum'
            },
            electrical_outlet: {
                type: 'duplex',
                voltage: 120,
                amperage: 15,
                circuit: 'general'
            },
            light_fixture: {
                type: 'recessed',
                wattage: 60,
                color: 'warm',
                mounting: 'ceiling'
            },
            room: {
                type: 'general',
                function: 'multi-purpose',
                occupancy: 1
            }
        };
        
        return defaults[type] || {};
    }
    
    /**
     * Calculate measurements for ArxObject
     */
    calculateMeasurements(arxObject) {
        const measurements = [];
        
        switch (arxObject.type) {
            case 'wall':
                measurements.push(
                    { type: 'length', value: this.calculateLength(arxObject.geometry), unit: 'inches' },
                    { type: 'area', value: this.calculateArea(arxObject.geometry), unit: 'square_inches' },
                    { type: 'volume', value: this.calculateVolume(arxObject.geometry), unit: 'cubic_inches' }
                );
                break;
                
            case 'door':
            case 'window':
                measurements.push(
                    { type: 'area', value: this.calculateArea(arxObject.geometry), unit: 'square_inches' },
                    { type: 'clearance', value: this.calculateClearance(arxObject.geometry), unit: 'inches' }
                );
                break;
                
            case 'room':
                measurements.push(
                    { type: 'area', value: this.calculateArea(arxObject.geometry), unit: 'square_inches' },
                    { type: 'perimeter', value: this.calculatePerimeter(arxObject.geometry), unit: 'inches' },
                    { type: 'volume', value: this.calculateVolume(arxObject.geometry), unit: 'cubic_inches' }
                );
                break;
                
            case 'electrical_outlet':
            case 'light_fixture':
                measurements.push(
                    { type: 'height', value: this.calculateHeight(arxObject.geometry), unit: 'inches' }
                );
                break;
        }
        
        arxObject.measurements = measurements;
    }
    
    /**
     * Calculate length of object
     */
    calculateLength(geometry) {
        if (geometry.type === 'line') {
            return this.calculateDistance(geometry.startPoint, geometry.endPoint);
        } else if (geometry.type === 'rectangle') {
            return Math.abs(geometry.endPoint.x - geometry.startPoint.x);
        }
        return 0;
    }
    
    /**
     * Calculate area of object
     */
    calculateArea(geometry) {
        switch (geometry.type) {
            case 'rectangle':
                const width = Math.abs(geometry.endPoint.x - geometry.startPoint.x);
                const height = Math.abs(geometry.endPoint.y - geometry.startPoint.y);
                return width * height;
                
            case 'circle':
                return Math.PI * geometry.radius * geometry.radius;
                
            default:
                return 0;
        }
    }
    
    /**
     * Calculate perimeter of object
     */
    calculatePerimeter(geometry) {
        switch (geometry.type) {
            case 'rectangle':
                const width = Math.abs(geometry.endPoint.x - geometry.startPoint.x);
                const height = Math.abs(geometry.endPoint.y - geometry.startPoint.y);
                return 2 * (width + height);
                
            case 'circle':
                return 2 * Math.PI * geometry.radius;
                
            default:
                return 0;
        }
    }
    
    /**
     * Calculate volume of object
     */
    calculateVolume(geometry) {
        const area = this.calculateArea(geometry);
        const height = geometry.height || 0;
        return area * height;
    }
    
    /**
     * Calculate height of object
     */
    calculateHeight(geometry) {
        if (geometry.height) {
            return geometry.height;
        }
        
        switch (geometry.type) {
            case 'rectangle':
                return Math.abs(geometry.endPoint.y - geometry.startPoint.y);
                
            default:
                return 0;
        }
    }
    
    /**
     * Calculate clearance around object
     */
    calculateClearance(geometry) {
        // Default clearance values
        const clearances = {
            door: 36,
            window: 24,
            electrical_outlet: 18,
            light_fixture: 12
        };
        
        return clearances[geometry.objectType] || 0;
    }
    
    /**
     * Calculate distance between two points
     */
    calculateDistance(point1, point2) {
        const dx = point2.x - point1.x;
        const dy = point2.y - point1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    /**
     * Add relationship between two ArxObjects
     */
    addRelationship(objectId1, objectId2, relationshipType, properties = {}) {
        const object1 = this.arxObjects.get(objectId1);
        const object2 = this.arxObjects.get(objectId2);
        
        if (!object1 || !object2) {
            throw new Error('One or both objects not found');
        }
        
        const relationship = {
            id: this.generateRelationshipId(),
            type: relationshipType,
            object1: objectId1,
            object2: objectId2,
            properties: properties,
            metadata: {
                created: Date.now(),
                modified: Date.now()
            }
        };
        
        // Add to both objects
        object1.relationships.push(relationship);
        object2.relationships.push(relationship);
        
        // Store in relationships map
        this.relationships.set(relationship.id, relationship);
        
        console.log('Added relationship:', relationship);
        return relationship;
    }
    
    /**
     * Add constraint to ArxObject
     */
    addConstraint(objectId, constraintType, parameters = {}) {
        const arxObject = this.arxObjects.get(objectId);
        if (!arxObject) {
            throw new Error('Object not found');
        }
        
        const constraint = {
            id: this.generateConstraintId(),
            type: constraintType,
            parameters: parameters,
            metadata: {
                created: Date.now(),
                modified: Date.now()
            }
        };
        
        arxObject.constraints.push(constraint);
        
        console.log('Added constraint:', constraint);
        return constraint;
    }
    
    /**
     * Get ArxObject by ID
     */
    getArxObject(id) {
        return this.arxObjects.get(id);
    }
    
    /**
     * Get all ArxObjects of a specific type
     */
    getArxObjectsByType(type) {
        const objects = [];
        for (const [id, arxObject] of this.arxObjects) {
            if (arxObject.type === type) {
                objects.push(arxObject);
            }
        }
        return objects;
    }
    
    /**
     * Get ArxObjects by category
     */
    getArxObjectsByCategory(category) {
        const objects = [];
        for (const [id, arxObject] of this.arxObjects) {
            const objectType = this.objectTypes.get(arxObject.type);
            if (objectType && objectType.category === category) {
                objects.push(arxObject);
            }
        }
        return objects;
    }
    
    /**
     * Get related ArxObjects
     */
    getRelatedArxObjects(objectId, relationshipType = null) {
        const arxObject = this.arxObjects.get(objectId);
        if (!arxObject) return [];
        
        const relatedObjects = [];
        for (const relationship of arxObject.relationships) {
            if (!relationshipType || relationship.type === relationshipType) {
                const relatedId = relationship.object1 === objectId ? relationship.object2 : relationship.object1;
                const relatedObject = this.arxObjects.get(relatedId);
                if (relatedObject) {
                    relatedObjects.push(relatedObject);
                }
            }
        }
        
        return relatedObjects;
    }
    
    /**
     * Update ArxObject
     */
    updateArxObject(id, updates) {
        const arxObject = this.arxObjects.get(id);
        if (!arxObject) {
            throw new Error('Object not found');
        }
        
        // Update properties
        if (updates.properties) {
            arxObject.properties = { ...arxObject.properties, ...updates.properties };
        }
        
        // Update geometry
        if (updates.geometry) {
            arxObject.geometry = { ...arxObject.geometry, ...updates.geometry };
        }
        
        // Recalculate measurements
        this.calculateMeasurements(arxObject);
        
        // Update metadata
        arxObject.metadata.modified = Date.now();
        
        console.log('Updated ArxObject:', arxObject);
        return arxObject;
    }
    
    /**
     * Delete ArxObject
     */
    deleteArxObject(id) {
        const arxObject = this.arxObjects.get(id);
        if (!arxObject) {
            throw new Error('Object not found');
        }
        
        // Remove relationships
        for (const relationship of arxObject.relationships) {
            this.relationships.delete(relationship.id);
        }
        
        // Remove from system
        this.arxObjects.delete(id);
        
        console.log('Deleted ArxObject:', id);
    }
    
    /**
     * Export ArxObjects to JSON
     */
    exportToJSON() {
        const exportData = {
            arxObjects: Array.from(this.arxObjects.values()),
            relationships: Array.from(this.relationships.values()),
            metadata: {
                exported: Date.now(),
                version: '1.0.0',
                objectCount: this.arxObjects.size,
                relationshipCount: this.relationships.size
            }
        };
        
        return JSON.stringify(exportData, null, 2);
    }
    
    /**
     * Import ArxObjects from JSON
     */
    importFromJSON(jsonData) {
        const data = JSON.parse(jsonData);
        
        // Import ArxObjects
        for (const arxObject of data.arxObjects) {
            this.arxObjects.set(arxObject.id, arxObject);
        }
        
        // Import relationships
        for (const relationship of data.relationships) {
            this.relationships.set(relationship.id, relationship);
        }
        
        console.log('Imported ArxObjects:', data.arxObjects.length);
        console.log('Imported relationships:', data.relationships.length);
    }
    
    /**
     * Generate unique object ID
     */
    generateObjectId() {
        return 'arx_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Generate unique relationship ID
     */
    generateRelationshipId() {
        return 'rel_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Generate unique constraint ID
     */
    generateConstraintId() {
        return 'con_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Get statistics about ArxObjects
     */
    getStatistics() {
        const stats = {
            totalObjects: this.arxObjects.size,
            totalRelationships: this.relationships.size,
            objectsByType: {},
            objectsByCategory: {},
            totalArea: 0,
            totalVolume: 0
        };
        
        // Count by type and category
        for (const [id, arxObject] of this.arxObjects) {
            // Count by type
            stats.objectsByType[arxObject.type] = (stats.objectsByType[arxObject.type] || 0) + 1;
            
            // Count by category
            const objectType = this.objectTypes.get(arxObject.type);
            if (objectType) {
                stats.objectsByCategory[objectType.category] = (stats.objectsByCategory[objectType.category] || 0) + 1;
            }
            
            // Sum areas and volumes
            for (const measurement of arxObject.measurements) {
                if (measurement.type === 'area') {
                    stats.totalArea += measurement.value;
                } else if (measurement.type === 'volume') {
                    stats.totalVolume += measurement.value;
                }
            }
        }
        
        return stats;
    }
}

// Export for global use
window.ArxObjectSystem = ArxObjectSystem; 