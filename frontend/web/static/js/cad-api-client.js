/**
 * Arxos CAD API Client
 * Integrates CAD system with existing Arxos backend infrastructure
 *
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class CadApiClient {
    constructor() {
        this.baseUrl = '/api';
        this.authToken = this.getAuthToken();
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`
        };

        // API endpoints mapping
        this.endpoints = {
            // Project management
            projects: '/projects',
            project: (id) => `/projects/${id}`,

            // Building management
            buildings: '/buildings',
            building: (id) => `/buildings/${id}`,
            buildingFloors: (id) => `/buildings/${id}/floors`,
            buildingStatistics: (id) => `/buildings/${id}/statistics`,

            // Room management
            rooms: '/rooms',
            room: (id) => `/rooms/${id}`,
            roomDevices: (id) => `/rooms/${id}/devices`,
            roomStatistics: (id) => `/rooms/${id}/statistics`,

            // Device management
            devices: '/devices',
            device: (id) => `/devices/${id}`,
            deviceStatistics: (id) => `/devices/${id}/statistics`,

            // Floor management
            floors: '/floors',
            floor: (id) => `/floors/${id}`,
            floorRooms: (id) => `/floors/${id}/rooms`,
            floorStatistics: (id) => `/floors/${id}/statistics`,

            // User management
            users: '/users',
            user: (id) => `/users/${id}`,
            me: '/me',

            // SVGX operations
            svgObjects: '/svg-objects',
            objectTypes: '/api/object-types',
            behaviorProfiles: '/api/behavior-profiles',

            // Symbol library
            symbols: '/symbols',
            symbol: (id) => `/symbols/${id}`,
            symbolSearch: '/symbols/search',
            symbolCategories: '/symbols/categories',

            // Health and status
            health: '/health',
            healthDetailed: '/health/detailed',
            healthMetrics: '/health/metrics'
        };
    }

    /**
     * Get authentication token from localStorage
     */
    getAuthToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }

    /**
     * Update authentication token
     */
    updateAuthToken(token) {
        this.authToken = token;
        this.defaultHeaders.Authorization = `Bearer ${token}`;
        localStorage.setItem('authToken', token);
    }

    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);

            // Handle authentication errors
            if (response.status === 401) {
                this.handleAuthError();
                throw new Error('Authentication required');
            }

            // Handle other errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Handle authentication errors
     */
    handleAuthError() {
        // Clear invalid token
        localStorage.removeItem('authToken');
        sessionStorage.removeItem('authToken');

        // Redirect to login if not already there
        if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
        }
    }

    /**
     * Project Management API
     */
    async createProject(projectData) {
        return this.request(this.endpoints.projects, {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    }

    async getProjects(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.projects}?${queryString}` : this.endpoints.projects;
        return this.request(endpoint);
    }

    async getProject(projectId) {
        return this.request(this.endpoints.project(projectId));
    }

    async updateProject(projectId, projectData) {
        return this.request(this.endpoints.project(projectId), {
            method: 'PUT',
            body: JSON.stringify(projectData)
        });
    }

    async deleteProject(projectId) {
        return this.request(this.endpoints.project(projectId), {
            method: 'DELETE'
        });
    }

    /**
     * Building Management API
     */
    async createBuilding(buildingData) {
        return this.request(this.endpoints.buildings, {
            method: 'POST',
            body: JSON.stringify(buildingData)
        });
    }

    async getBuildings(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.buildings}?${queryString}` : this.endpoints.buildings;
        return this.request(endpoint);
    }

    async getBuilding(buildingId) {
        return this.request(this.endpoints.building(buildingId));
    }

    async updateBuilding(buildingId, buildingData) {
        return this.request(this.endpoints.building(buildingId), {
            method: 'PUT',
            body: JSON.stringify(buildingData)
        });
    }

    async deleteBuilding(buildingId) {
        return this.request(this.endpoints.building(buildingId), {
            method: 'DELETE'
        });
    }

    async getBuildingFloors(buildingId) {
        return this.request(this.endpoints.buildingFloors(buildingId));
    }

    async getBuildingStatistics(buildingId) {
        return this.request(this.endpoints.buildingStatistics(buildingId));
    }

    /**
     * Room Management API
     */
    async createRoom(roomData) {
        return this.request(this.endpoints.rooms, {
            method: 'POST',
            body: JSON.stringify(roomData)
        });
    }

    async getRooms(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.rooms}?${queryString}` : this.endpoints.rooms;
        return this.request(endpoint);
    }

    async getRoom(roomId) {
        return this.request(this.endpoints.room(roomId));
    }

    async updateRoom(roomId, roomData) {
        return this.request(this.endpoints.room(roomId), {
            method: 'PUT',
            body: JSON.stringify(roomData)
        });
    }

    async deleteRoom(roomId) {
        return this.request(this.endpoints.room(roomId), {
            method: 'DELETE'
        });
    }

    async getRoomDevices(roomId) {
        return this.request(this.endpoints.roomDevices(roomId));
    }

    async getRoomStatistics(roomId) {
        return this.request(this.endpoints.roomStatistics(roomId));
    }

    /**
     * Device Management API
     */
    async createDevice(deviceData) {
        return this.request(this.endpoints.devices, {
            method: 'POST',
            body: JSON.stringify(deviceData)
        });
    }

    async getDevices(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.devices}?${queryString}` : this.endpoints.devices;
        return this.request(endpoint);
    }

    async getDevice(deviceId) {
        return this.request(this.endpoints.device(deviceId));
    }

    async updateDevice(deviceId, deviceData) {
        return this.request(this.endpoints.device(deviceId), {
            method: 'PUT',
            body: JSON.stringify(deviceData)
        });
    }

    async deleteDevice(deviceId) {
        return this.request(this.endpoints.device(deviceId), {
            method: 'DELETE'
        });
    }

    async getDeviceStatistics(deviceId) {
        return this.request(this.endpoints.deviceStatistics(deviceId));
    }

    /**
     * Floor Management API
     */
    async createFloor(floorData) {
        return this.request(this.endpoints.floors, {
            method: 'POST',
            body: JSON.stringify(floorData)
        });
    }

    async getFloors(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.floors}?${queryString}` : this.endpoints.floors;
        return this.request(endpoint);
    }

    async getFloor(floorId) {
        return this.request(this.endpoints.floor(floorId));
    }

    async updateFloor(floorId, floorData) {
        return this.request(this.endpoints.floor(floorId), {
            method: 'PUT',
            body: JSON.stringify(floorData)
        });
    }

    async deleteFloor(floorId) {
        return this.request(this.endpoints.floor(floorId), {
            method: 'DELETE'
        });
    }

    async getFloorRooms(floorId) {
        return this.request(this.endpoints.floorRooms(floorId));
    }

    async getFloorStatistics(floorId) {
        return this.request(this.endpoints.floorStatistics(floorId));
    }

    /**
     * User Management API
     */
    async getUsers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.users}?${queryString}` : this.endpoints.users;
        return this.request(endpoint);
    }

    async getUser(userId) {
        return this.request(this.endpoints.user(userId));
    }

    async getCurrentUser() {
        return this.request(this.endpoints.me);
    }

    /**
     * SVGX Operations API
     */
    async getSvgObjects(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.svgObjects}?${queryString}` : this.endpoints.svgObjects;
        return this.request(endpoint);
    }

    async getObjectTypes() {
        return this.request(this.endpoints.objectTypes);
    }

    async getBehaviorProfiles() {
        return this.request(this.endpoints.behaviorProfiles);
    }

    /**
     * Symbol Library API
     */
    async getSymbols(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `${this.endpoints.symbols}?${queryString}` : this.endpoints.symbols;
        return this.request(endpoint);
    }

    async getSymbol(symbolId) {
        return this.request(this.endpoints.symbol(symbolId));
    }

    async searchSymbols(searchData) {
        return this.request(this.endpoints.symbolSearch, {
            method: 'POST',
            body: JSON.stringify(searchData)
        });
    }

    async getSymbolCategories() {
        return this.request(this.endpoints.symbolCategories);
    }

    /**
     * Health and Status API
     */
    async getHealth() {
        return this.request(this.endpoints.health);
    }

    async getDetailedHealth() {
        return this.request(this.endpoints.healthDetailed);
    }

    async getHealthMetrics() {
        return this.request(this.endpoints.healthMetrics);
    }

    /**
     * CAD-specific API methods
     */
    async saveCadProject(projectId, cadData) {
        return this.request(`${this.endpoints.project(projectId)}/cad`, {
            method: 'POST',
            body: JSON.stringify(cadData)
        });
    }

    async loadCadProject(projectId) {
        return this.request(`${this.endpoints.project(projectId)}/cad`);
    }

    async exportCadToSVGX(projectId, cadData) {
        return this.request(`${this.endpoints.project(projectId)}/export/svgx`, {
            method: 'POST',
            body: JSON.stringify(cadData)
        });
    }

    async importCadFromSVGX(projectId, svgxData) {
        return this.request(`${this.endpoints.project(projectId)}/import/svgx`, {
            method: 'POST',
            body: JSON.stringify(svgxData)
        });
    }

    /**
     * Real-time collaboration API
     */
    async joinCollaboration(projectId, userId) {
        return this.request(`${this.endpoints.project(projectId)}/collaboration/join`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    async leaveCollaboration(projectId, userId) {
        return this.request(`${this.endpoints.project(projectId)}/collaboration/leave`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    async sendCollaborationUpdate(projectId, updateData) {
        return this.request(`${this.endpoints.project(projectId)}/collaboration/update`, {
            method: 'POST',
            body: JSON.stringify(updateData)
        });
    }

    /**
     * AI Integration API
     */
    async processAiCommand(projectId, command) {
        return this.request(`${this.endpoints.project(projectId)}/ai/command`, {
            method: 'POST',
            body: JSON.stringify({ command })
        });
    }

    async getAiSuggestions(projectId, context) {
        return this.request(`${this.endpoints.project(projectId)}/ai/suggestions`, {
            method: 'POST',
            body: JSON.stringify({ context })
        });
    }

    /**
     * Utility methods
     */
    async uploadFile(projectId, file, type = 'cad') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);

        return this.request(`${this.endpoints.project(projectId)}/upload`, {
            method: 'POST',
            headers: {}, // Let browser set Content-Type for FormData
            body: formData
        });
    }

    async downloadFile(projectId, fileId) {
        const response = await fetch(`${this.baseUrl}${this.endpoints.project(projectId)}/files/${fileId}`, {
            headers: this.defaultHeaders
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        return response.blob();
    }
}

// Export for global use
window.CadApiClient = CadApiClient;
