/**
 * Link Generator
 * Handles shareable link creation, QR code generation, and access control management
 */

export class LinkGenerator {
    constructor(options = {}) {
        this.options = {
            baseUrl: options.baseUrl || window.location.origin,
            enableQRCode: options.enableQRCode !== false,
            qrCodeSize: options.qrCodeSize || 200,
            linkExpiryDefault: options.linkExpiryDefault || 7 * 24 * 60 * 60 * 1000, // 7 days
            maxLinkLength: options.maxLinkLength || 2048,
            enableAnalytics: options.enableAnalytics !== false,
            ...options
        };
        
        // Link storage
        this.generatedLinks = new Map();
        this.linkAnalytics = new Map();
        
        // QR code library (if available)
        this.qrCodeLibrary = null;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadQRCodeLibrary();
    }

    setupEventListeners() {
        // Listen for link generation requests
        document.addEventListener('generateLink', (event) => {
            this.handleLinkGenerationRequest(event.detail);
        });
        
        // Listen for link access
        document.addEventListener('linkAccessed', (event) => {
            this.handleLinkAccess(event.detail);
        });
    }

    async loadQRCodeLibrary() {
        if (!this.options.enableQRCode) return;
        
        try {
            // Try to load QR code library dynamically
            if (typeof QRCode !== 'undefined') {
                this.qrCodeLibrary = QRCode;
            } else {
                // Load from CDN if not available
                await this.loadScript('https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js');
                this.qrCodeLibrary = window.QRCode;
            }
        } catch (error) {
            console.warn('QR code library not available:', error);
        }
    }

    async loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Link generation
    async generateLink(params) {
        const {
            objectId,
            buildingId,
            floorId,
            accessType = 'public',
            expiresAt = null,
            viewOptions = {},
            highlight = true,
            zoom = true,
            customParams = {}
        } = params;
        
        try {
            // Validate parameters
            const validationResult = this.validateLinkParams(params);
            if (!validationResult.valid) {
                throw new Error(validationResult.error);
            }
            
            // Generate unique link ID
            const linkId = this.generateLinkId();
            
            // Create link URL
            const linkUrl = this.createLinkUrl({
                linkId,
                objectId,
                buildingId,
                floorId,
                viewOptions,
                highlight,
                zoom,
                customParams
            });
            
            // Create link object
            const link = {
                id: linkId,
                url: linkUrl,
                objectId,
                buildingId,
                floorId,
                accessType,
                expiresAt: expiresAt || this.calculateDefaultExpiry(),
                viewOptions,
                highlight,
                zoom,
                customParams,
                createdAt: Date.now(),
                createdBy: this.getCurrentUserId(),
                accessCount: 0,
                lastAccessed: null
            };
            
            // Store link
            this.generatedLinks.set(linkId, link);
            
            // Save to server
            await this.saveLinkToServer(link);
            
            // Track analytics
            if (this.options.enableAnalytics) {
                this.trackLinkGeneration(link);
            }
            
            this.triggerEvent('linkGenerated', { link });
            
            return link;
            
        } catch (error) {
            console.error('Link generation failed:', error);
            this.triggerEvent('linkGenerationFailed', { params, error });
            throw error;
        }
    }

    validateLinkParams(params) {
        const errors = [];
        
        if (!params.objectId) {
            errors.push('objectId is required');
        }
        
        if (!params.buildingId) {
            errors.push('buildingId is required');
        }
        
        if (!params.floorId) {
            errors.push('floorId is required');
        }
        
        // Validate access type
        const validAccessTypes = ['public', 'private', 'expiring'];
        if (params.accessType && !validAccessTypes.includes(params.accessType)) {
            errors.push(`Invalid access type: ${params.accessType}`);
        }
        
        // Validate expiry date
        if (params.expiresAt) {
            const expiryDate = new Date(params.expiresAt);
            if (isNaN(expiryDate.getTime())) {
                errors.push('Invalid expiry date');
            } else if (expiryDate <= new Date()) {
                errors.push('Expiry date must be in the future');
            }
        }
        
        return {
            valid: errors.length === 0,
            error: errors.join(', ')
        };
    }

    generateLinkId() {
        // Generate a unique link ID
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 8);
        return `link_${timestamp}_${random}`;
    }

    createLinkUrl(params) {
        const {
            linkId,
            objectId,
            buildingId,
            floorId,
            viewOptions,
            highlight,
            zoom,
            customParams
        } = params;
        
        const url = new URL(`${this.options.baseUrl}/viewer`);
        
        // Add required parameters
        url.searchParams.set('link_id', linkId);
        url.searchParams.set('building_id', buildingId);
        url.searchParams.set('floor_id', floorId);
        url.searchParams.set('object_id', objectId);
        
        // Add view options
        if (viewOptions.zoom !== undefined) {
            url.searchParams.set('zoom', viewOptions.zoom);
        }
        
        if (viewOptions.pan) {
            url.searchParams.set('pan', JSON.stringify(viewOptions.pan));
        }
        
        if (viewOptions.rotation !== undefined) {
            url.searchParams.set('rotation', viewOptions.rotation);
        }
        
        // Add highlighting and zoom options
        if (highlight !== undefined) {
            url.searchParams.set('highlight', highlight.toString());
        }
        
        if (zoom !== undefined) {
            url.searchParams.set('zoom_to_object', zoom.toString());
        }
        
        // Add custom parameters
        Object.entries(customParams).forEach(([key, value]) => {
            url.searchParams.set(key, value.toString());
        });
        
        // Validate URL length
        if (url.toString().length > this.options.maxLinkLength) {
            throw new Error('Generated link exceeds maximum length');
        }
        
        return url.toString();
    }

    calculateDefaultExpiry() {
        return Date.now() + this.options.linkExpiryDefault;
    }

    // QR code generation
    async generateQRCode(link, options = {}) {
        if (!this.qrCodeLibrary) {
            throw new Error('QR code library not available');
        }
        
        const {
            size = this.options.qrCodeSize,
            margin = 2,
            color = '#000000',
            backgroundColor = '#FFFFFF',
            errorCorrectionLevel = 'M'
        } = options;
        
        try {
            const qrCodeDataUrl = await this.qrCodeLibrary.toDataURL(link.url, {
                width: size,
                margin: margin,
                color: {
                    dark: color,
                    light: backgroundColor
                },
                errorCorrectionLevel: errorCorrectionLevel
            });
            
            const qrCode = {
                dataUrl: qrCodeDataUrl,
                url: link.url,
                size: size,
                linkId: link.id
            };
            
            this.triggerEvent('qrCodeGenerated', { qrCode, link });
            
            return qrCode;
            
        } catch (error) {
            console.error('QR code generation failed:', error);
            this.triggerEvent('qrCodeGenerationFailed', { link, error });
            throw error;
        }
    }

    // Link access and validation
    async validateLink(linkId) {
        const link = this.generatedLinks.get(linkId);
        if (!link) {
            return { valid: false, reason: 'Link not found' };
        }
        
        // Check if link has expired
        if (link.expiresAt && Date.now() > link.expiresAt) {
            return { valid: false, reason: 'Link has expired' };
        }
        
        // Check access permissions
        const accessResult = await this.checkLinkAccess(link);
        if (!accessResult.granted) {
            return { valid: false, reason: accessResult.reason };
        }
        
        return { valid: true, link };
    }

    async checkLinkAccess(link) {
        try {
            const response = await fetch('/api/links/access', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({
                    linkId: link.id,
                    accessType: link.accessType,
                    objectId: link.objectId,
                    buildingId: link.buildingId
                })
            });
            
            if (!response.ok) {
                return { granted: false, reason: 'Access denied' };
            }
            
            const result = await response.json();
            return { granted: result.granted, reason: result.reason };
            
        } catch (error) {
            console.error('Link access check failed:', error);
            return { granted: false, reason: 'Access check failed' };
        }
    }

    async recordLinkAccess(linkId) {
        const link = this.generatedLinks.get(linkId);
        if (!link) return;
        
        // Update access count
        link.accessCount++;
        link.lastAccessed = Date.now();
        
        // Track analytics
        if (this.options.enableAnalytics) {
            this.trackLinkAccess(link);
        }
        
        // Update on server
        await this.updateLinkOnServer(link);
        
        this.triggerEvent('linkAccessed', { link });
    }

    // Link management
    async updateLink(linkId, updates) {
        const link = this.generatedLinks.get(linkId);
        if (!link) {
            throw new Error(`Link '${linkId}' not found`);
        }
        
        // Update link properties
        const updatedLink = {
            ...link,
            ...updates,
            updatedAt: Date.now()
        };
        
        this.generatedLinks.set(linkId, updatedLink);
        
        // Update on server
        await this.updateLinkOnServer(updatedLink);
        
        this.triggerEvent('linkUpdated', { link: updatedLink, updates });
        
        return updatedLink;
    }

    async deleteLink(linkId) {
        const link = this.generatedLinks.get(linkId);
        if (!link) {
            return false;
        }
        
        // Remove from local storage
        this.generatedLinks.delete(linkId);
        
        // Remove from server
        await this.deleteLinkFromServer(linkId);
        
        this.triggerEvent('linkDeleted', { link });
        
        return true;
    }

    getLink(linkId) {
        return this.generatedLinks.get(linkId);
    }

    getAllLinks() {
        return Array.from(this.generatedLinks.values());
    }

    getLinksByObject(objectId) {
        return Array.from(this.generatedLinks.values())
            .filter(link => link.objectId === objectId);
    }

    getLinksByBuilding(buildingId) {
        return Array.from(this.generatedLinks.values())
            .filter(link => link.buildingId === buildingId);
    }

    getExpiredLinks() {
        const now = Date.now();
        return Array.from(this.generatedLinks.values())
            .filter(link => link.expiresAt && link.expiresAt < now);
    }

    // Analytics
    trackLinkGeneration(link) {
        const analytics = {
            linkId: link.id,
            objectId: link.objectId,
            buildingId: link.buildingId,
            accessType: link.accessType,
            timestamp: Date.now(),
            userId: this.getCurrentUserId()
        };
        
        this.linkAnalytics.set(link.id, analytics);
        
        // Send to analytics service
        this.sendAnalytics('link_generated', analytics);
    }

    trackLinkAccess(link) {
        const analytics = {
            linkId: link.id,
            objectId: link.objectId,
            buildingId: link.buildingId,
            accessCount: link.accessCount,
            timestamp: Date.now(),
            userId: this.getCurrentUserId()
        };
        
        // Send to analytics service
        this.sendAnalytics('link_accessed', analytics);
    }

    async sendAnalytics(event, data) {
        try {
            await fetch('/api/analytics/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({
                    event,
                    data,
                    timestamp: Date.now()
                })
            });
        } catch (error) {
            console.error('Failed to send analytics:', error);
        }
    }

    // Server communication
    async saveLinkToServer(link) {
        try {
            const response = await fetch('/api/links', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(link)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save link: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to save link to server:', error);
            throw error;
        }
    }

    async updateLinkOnServer(link) {
        try {
            const response = await fetch(`/api/links/${link.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(link)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update link: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to update link on server:', error);
            throw error;
        }
    }

    async deleteLinkFromServer(linkId) {
        try {
            const response = await fetch(`/api/links/${linkId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete link: ${response.status}`);
            }
            
        } catch (error) {
            console.error('Failed to delete link from server:', error);
            throw error;
        }
    }

    // Event handlers
    handleLinkGenerationRequest(detail) {
        this.generateLink(detail);
    }

    handleLinkAccess(detail) {
        const { linkId } = detail;
        this.recordLinkAccess(linkId);
    }

    // Public API methods
    async generateLinkForObject(objectId, options = {}) {
        // Get object details
        const object = await this.getObjectDetails(objectId);
        if (!object) {
            throw new Error(`Object '${objectId}' not found`);
        }
        
        const params = {
            objectId: object.id,
            buildingId: object.building_id,
            floorId: object.floor_id,
            ...options
        };
        
        return this.generateLink(params);
    }

    async generateQRCodeForLink(linkId, options = {}) {
        const link = this.getLink(linkId);
        if (!link) {
            throw new Error(`Link '${linkId}' not found`);
        }
        
        return this.generateQRCode(link, options);
    }

    getLinkAnalytics(linkId) {
        return this.linkAnalytics.get(linkId);
    }

    getGeneratorStats() {
        return {
            totalLinks: this.generatedLinks.size,
            activeLinks: this.getAllLinks().filter(link => 
                !link.expiresAt || link.expiresAt > Date.now()
            ).length,
            expiredLinks: this.getExpiredLinks().length,
            totalAccesses: this.getAllLinks().reduce((sum, link) => sum + link.accessCount, 0)
        };
    }

    // Utility methods
    getCurrentUserId() {
        return localStorage.getItem('user_id') || 'anonymous';
    }

    getAuthHeaders() {
        const token = localStorage.getItem('arx_jwt');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    async getObjectDetails(objectId) {
        try {
            const response = await fetch(`/api/objects/${objectId}`, {
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                return null;
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Failed to get object details:', error);
            return null;
        }
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
                    handler({ ...data, generator: this });
                } catch (error) {
                    console.error(`Error in link generator event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.generatedLinks.clear();
        this.linkAnalytics.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 