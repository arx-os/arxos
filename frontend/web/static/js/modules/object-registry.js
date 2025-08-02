/**
 * Object Registry
 * Maintains mapping of object_id to spatial coordinates, metadata, and relationships
 */

export class ObjectRegistry {
    constructor(options = {}) {
        this.options = {
            enableCaching: options.enableCaching !== false,
            cacheExpiry: options.cacheExpiry || 300000, // 5 minutes
            maxCacheSize: options.maxCacheSize || 1000,
            enableIndexing: options.enableIndexing !== false,
            ...options
        };
        
        // Registry storage
        this.objects = new Map();
        this.spatialIndex = new Map();
        this.metadataIndex = new Map();
        this.relationshipIndex = new Map();
        
        // Cache management
        this.cache = new Map();
        this.cacheTimestamps = new Map();
        
        // Search index
        this.searchIndex = new Map();
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Listen for object updates
        document.addEventListener('objectUpdated', (event) => {
            this.handleObjectUpdate(event.detail);
        });
        
        // Listen for object creation
        document.addEventListener('objectCreated', (event) => {
            this.handleObjectCreation(event.detail);
        });
        
        // Listen for object deletion
        document.addEventListener('objectDeleted', (event) => {
            this.handleObjectDeletion(event.detail);
        });
    }

    async loadInitialData() {
        try {
            // Load objects from API
            const objects = await this.fetchObjects();
            objects.forEach(object => {
                this.registerObject(object);
            });
            
            this.triggerEvent('registryLoaded', { objectCount: this.objects.size });
            
        } catch (error) {
            console.error('Failed to load initial object data:', error);
            this.triggerEvent('registryLoadFailed', { error });
        }
    }

    // Object registration and management
    registerObject(object) {
        const { id, building_id, floor_id, object_type, spatial_coordinates, metadata } = object;
        
        // Store object data
        this.objects.set(id, {
            id,
            building_id,
            floor_id,
            object_type,
            spatial_coordinates,
            metadata,
            registered_at: Date.now(),
            updated_at: Date.now()
        });
        
        // Update spatial index
        if (spatial_coordinates) {
            this.updateSpatialIndex(id, spatial_coordinates);
        }
        
        // Update metadata index
        if (metadata) {
            this.updateMetadataIndex(id, metadata);
        }
        
        // Update search index
        this.updateSearchIndex(id, object);
        
        // Update relationship index
        if (metadata && metadata.relationships) {
            this.updateRelationshipIndex(id, metadata.relationships);
        }
        
        this.triggerEvent('objectRegistered', { object });
    }

    updateObject(objectId, updates) {
        const object = this.objects.get(objectId);
        if (!object) {
            throw new Error(`Object '${objectId}' not found in registry`);
        }
        
        // Update object data
        const updatedObject = {
            ...object,
            ...updates,
            updated_at: Date.now()
        };
        
        this.objects.set(objectId, updatedObject);
        
        // Update indexes
        if (updates.spatial_coordinates) {
            this.updateSpatialIndex(objectId, updates.spatial_coordinates);
        }
        
        if (updates.metadata) {
            this.updateMetadataIndex(objectId, updates.metadata);
            this.updateSearchIndex(objectId, updatedObject);
            
            if (updates.metadata.relationships) {
                this.updateRelationshipIndex(objectId, updates.metadata.relationships);
            }
        }
        
        // Clear cache for this object
        this.clearCache(objectId);
        
        this.triggerEvent('objectUpdated', { object: updatedObject, updates });
    }

    unregisterObject(objectId) {
        const object = this.objects.get(objectId);
        if (!object) {
            return false;
        }
        
        // Remove from all indexes
        this.removeFromSpatialIndex(objectId);
        this.removeFromMetadataIndex(objectId);
        this.removeFromSearchIndex(objectId);
        this.removeFromRelationshipIndex(objectId);
        
        // Remove from main registry
        this.objects.delete(objectId);
        
        // Clear cache
        this.clearCache(objectId);
        
        this.triggerEvent('objectUnregistered', { object });
        return true;
    }

    // Spatial indexing
    updateSpatialIndex(objectId, coordinates) {
        const key = this.generateSpatialKey(coordinates);
        
        if (!this.spatialIndex.has(key)) {
            this.spatialIndex.set(key, new Set());
        }
        
        this.spatialIndex.get(key).add(objectId);
    }

    removeFromSpatialIndex(objectId) {
        for (const [key, objectIds] of this.spatialIndex.entries()) {
            if (objectIds.has(objectId)) {
                objectIds.delete(objectId);
                if (objectIds.size === 0) {
                    this.spatialIndex.delete(key);
                }
                break;
            }
        }
    }

    generateSpatialKey(coordinates) {
        // Generate a spatial key based on coordinates
        if (coordinates.bounds) {
            const { x1, y1, x2, y2 } = coordinates.bounds;
            return `${Math.floor(x1/100)},${Math.floor(y1/100)},${Math.floor(x2/100)},${Math.floor(y2/100)}`;
        }
        
        if (coordinates.center) {
            const { x, y } = coordinates.center;
            return `${Math.floor(x/100)},${Math.floor(y/100)}`;
        }
        
        if (coordinates.position) {
            const { x, y } = coordinates.position;
            return `${Math.floor(x/100)},${Math.floor(y/100)}`;
        }
        
        return 'unknown';
    }

    // Metadata indexing
    updateMetadataIndex(objectId, metadata) {
        Object.entries(metadata).forEach(([key, value]) => {
            const indexKey = `${key}:${value}`;
            
            if (!this.metadataIndex.has(indexKey)) {
                this.metadataIndex.set(indexKey, new Set());
            }
            
            this.metadataIndex.get(indexKey).add(objectId);
        });
    }

    removeFromMetadataIndex(objectId) {
        for (const [key, objectIds] of this.metadataIndex.entries()) {
            if (objectIds.has(objectId)) {
                objectIds.delete(objectId);
                if (objectIds.size === 0) {
                    this.metadataIndex.delete(key);
                }
            }
        }
    }

    // Search indexing
    updateSearchIndex(objectId, object) {
        const searchTerms = this.extractSearchTerms(object);
        
        searchTerms.forEach(term => {
            if (!this.searchIndex.has(term)) {
                this.searchIndex.set(term, new Set());
            }
            
            this.searchIndex.get(term).add(objectId);
        });
    }

    removeFromSearchIndex(objectId) {
        for (const [term, objectIds] of this.searchIndex.entries()) {
            if (objectIds.has(objectId)) {
                objectIds.delete(objectId);
                if (objectIds.size === 0) {
                    this.searchIndex.delete(term);
                }
            }
        }
    }

    extractSearchTerms(object) {
        const terms = new Set();
        
        // Add object ID
        terms.add(object.id.toLowerCase());
        
        // Add object type
        if (object.object_type) {
            terms.add(object.object_type.toLowerCase());
        }
        
        // Add building and floor IDs
        if (object.building_id) {
            terms.add(object.building_id.toLowerCase());
        }
        
        if (object.floor_id) {
            terms.add(object.floor_id.toLowerCase());
        }
        
        // Add metadata terms
        if (object.metadata) {
            Object.values(object.metadata).forEach(value => {
                if (typeof value === 'string') {
                    terms.add(value.toLowerCase());
                }
            });
        }
        
        return Array.from(terms);
    }

    // Relationship indexing
    updateRelationshipIndex(objectId, relationships) {
        Object.entries(relationships).forEach(([type, relatedIds]) => {
            const relationshipKey = `${type}:${objectId}`;
            
            if (!this.relationshipIndex.has(relationshipKey)) {
                this.relationshipIndex.set(relationshipKey, new Set());
            }
            
            const relatedIdArray = Array.isArray(relatedIds) ? relatedIds : [relatedIds];
            relatedIdArray.forEach(relatedId => {
                this.relationshipIndex.get(relationshipKey).add(relatedId);
            });
        });
    }

    removeFromRelationshipIndex(objectId) {
        for (const [key, relatedIds] of this.relationshipIndex.entries()) {
            if (key.includes(`:${objectId}`)) {
                this.relationshipIndex.delete(key);
            } else if (relatedIds.has(objectId)) {
                relatedIds.delete(objectId);
                if (relatedIds.size === 0) {
                    this.relationshipIndex.delete(key);
                }
            }
        }
    }

    // Object retrieval
    getObject(objectId) {
        // Check cache first
        if (this.options.enableCaching) {
            const cached = this.getFromCache(objectId);
            if (cached) {
                return cached;
            }
        }
        
        const object = this.objects.get(objectId);
        
        if (object && this.options.enableCaching) {
            this.setCache(objectId, object);
        }
        
        return object;
    }

    getObjectsByBuilding(buildingId) {
        const objects = [];
        
        for (const object of this.objects.values()) {
            if (object.building_id === buildingId) {
                objects.push(object);
            }
        }
        
        return objects;
    }

    getObjectsByFloor(buildingId, floorId) {
        const objects = [];
        
        for (const object of this.objects.values()) {
            if (object.building_id === buildingId && object.floor_id === floorId) {
                objects.push(object);
            }
        }
        
        return objects;
    }

    getObjectsByType(objectType) {
        const objects = [];
        
        for (const object of this.objects.values()) {
            if (object.object_type === objectType) {
                objects.push(object);
            }
        }
        
        return objects;
    }

    // Spatial queries
    getObjectsInArea(bounds) {
        const objects = new Set();
        const spatialKey = this.generateSpatialKey({ bounds });
        
        if (this.spatialIndex.has(spatialKey)) {
            this.spatialIndex.get(spatialKey).forEach(objectId => {
                objects.add(this.getObject(objectId));
            });
        }
        
        return Array.from(objects).filter(Boolean);
    }

    getObjectsNearPoint(point, radius = 100) {
        const objects = [];
        
        for (const object of this.objects.values()) {
            if (object.spatial_coordinates) {
                const distance = this.calculateDistance(point, object.spatial_coordinates);
                if (distance <= radius) {
                    objects.push({ ...object, distance });
                }
            }
        }
        
        return objects.sort((a, b) => a.distance - b.distance);
    }

    calculateDistance(point, coordinates) {
        let objectPoint;
        
        if (coordinates.center) {
            objectPoint = coordinates.center;
        } else if (coordinates.position) {
            objectPoint = coordinates.position;
        } else if (coordinates.bounds) {
            const { x1, y1, x2, y2 } = coordinates.bounds;
            objectPoint = { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
        } else {
            return Infinity;
        }
        
        const dx = point.x - objectPoint.x;
        const dy = point.y - objectPoint.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // Search functionality
    searchObjects(query, options = {}) {
        const {
            buildingId = null,
            floorId = null,
            objectType = null,
            limit = 50,
            fuzzy = true
        } = options;
        
        const searchTerms = this.tokenizeQuery(query);
        const results = new Map(); // objectId -> score
        
        searchTerms.forEach(term => {
            const matchingObjects = this.searchIndex.get(term.toLowerCase());
            if (matchingObjects) {
                matchingObjects.forEach(objectId => {
                    const currentScore = results.get(objectId) || 0;
                    results.set(objectId, currentScore + 1);
                });
            }
        });
        
        // Convert to array and filter
        let searchResults = Array.from(results.entries())
            .map(([objectId, score]) => ({
                object: this.getObject(objectId),
                score
            }))
            .filter(result => result.object)
            .sort((a, b) => b.score - a.score);
        
        // Apply filters
        if (buildingId) {
            searchResults = searchResults.filter(result => 
                result.object.building_id === buildingId
            );
        }
        
        if (floorId) {
            searchResults = searchResults.filter(result => 
                result.object.floor_id === floorId
            );
        }
        
        if (objectType) {
            searchResults = searchResults.filter(result => 
                result.object.object_type === objectType
            );
        }
        
        return searchResults.slice(0, limit);
    }

    tokenizeQuery(query) {
        return query.toLowerCase()
            .split(/\s+/)
            .filter(term => term.length > 0);
    }

    // Relationship queries
    getRelatedObjects(objectId, relationshipType = null) {
        const relatedObjects = [];
        
        if (relationshipType) {
            const key = `${relationshipType}:${objectId}`;
            const relatedIds = this.relationshipIndex.get(key);
            if (relatedIds) {
                relatedIds.forEach(relatedId => {
                    const object = this.getObject(relatedId);
                    if (object) {
                        relatedObjects.push(object);
                    }
                });
            }
        } else {
            // Get all relationships
            for (const [key, relatedIds] of this.relationshipIndex.entries()) {
                if (key.includes(`:${objectId}`)) {
                    const relationshipType = key.split(':')[0];
                    relatedIds.forEach(relatedId => {
                        const object = this.getObject(relatedId);
                        if (object) {
                            relatedObjects.push({ ...object, relationshipType });
                        }
                    });
                }
            }
        }
        
        return relatedObjects;
    }

    // Cache management
    getFromCache(objectId) {
        const cached = this.cache.get(objectId);
        if (!cached) return null;
        
        const timestamp = this.cacheTimestamps.get(objectId);
        if (Date.now() - timestamp > this.options.cacheExpiry) {
            this.clearCache(objectId);
            return null;
        }
        
        return cached;
    }

    setCache(objectId, object) {
        this.cache.set(objectId, object);
        this.cacheTimestamps.set(objectId, Date.now());
        
        // Enforce cache size limit
        if (this.cache.size > this.options.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.clearCache(oldestKey);
        }
    }

    clearCache(objectId) {
        this.cache.delete(objectId);
        this.cacheTimestamps.delete(objectId);
    }

    clearAllCache() {
        this.cache.clear();
        this.cacheTimestamps.clear();
    }

    // Data persistence
    async fetchObjects() {
        try {
            const response = await fetch('/api/objects', {
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch objects: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to fetch objects:', error);
            return [];
        }
    }

    async saveObject(object) {
        try {
            const response = await fetch('/api/objects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(object)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save object: ${response.status}`);
            }
            
            const savedObject = await response.json();
            this.registerObject(savedObject);
            
            return savedObject;
            
        } catch (error) {
            console.error('Failed to save object:', error);
            throw error;
        }
    }

    async updateObjectOnServer(objectId, updates) {
        try {
            const response = await fetch(`/api/objects/${objectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(updates)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update object: ${response.status}`);
            }
            
            const updatedObject = await response.json();
            this.updateObject(objectId, updatedObject);
            
            return updatedObject;
            
        } catch (error) {
            console.error('Failed to update object:', error);
            throw error;
        }
    }

    // Event handlers
    handleObjectUpdate(detail) {
        const { object, updates } = detail;
        this.updateObject(object.id, updates);
    }

    handleObjectCreation(detail) {
        const { object } = detail;
        this.registerObject(object);
    }

    handleObjectDeletion(detail) {
        const { objectId } = detail;
        this.unregisterObject(objectId);
    }

    // Public API methods
    getAllObjects() {
        return Array.from(this.objects.values());
    }

    getObjectCount() {
        return this.objects.size;
    }

    getRegistryStats() {
        return {
            totalObjects: this.objects.size,
            spatialIndexSize: this.spatialIndex.size,
            metadataIndexSize: this.metadataIndex.size,
            searchIndexSize: this.searchIndex.size,
            relationshipIndexSize: this.relationshipIndex.size,
            cacheSize: this.cache.size
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
                    handler({ ...data, registry: this });
                } catch (error) {
                    console.error(`Error in object registry event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.objects.clear();
        this.spatialIndex.clear();
        this.metadataIndex.clear();
        this.relationshipIndex.clear();
        this.searchIndex.clear();
        this.cache.clear();
        this.cacheTimestamps.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 