/**
 * Main Application - ArxOS Layer 4 ASCII-BIM PWA
 * Coordinates renderer, WebSocket client, and UI interactions
 */

class ArxOSASCIIApp {
    constructor() {
        this.renderer = null;
        this.wsClient = null;
        this.currentBuilding = null;
        this.currentFloor = 'f1';
        this.selectedObject = null;
        this.isLoading = false;
        this.isMobile = window.innerWidth <= 768;
        this.sidebarVisible = true;
        
        this.init();
    }
    
    async init() {
        console.log('Initializing ArxOS ASCII-BIM PWA...');
        
        // Show loading screen
        this.showLoading('Initializing application...');
        
        try {
            // Initialize components
            await this.initializeRenderer();
            await this.initializeWebSocket();
            this.setupEventHandlers();
            this.handleResponsiveDesign();
            
            // Load demo data if offline or no WebSocket connection
            setTimeout(() => {
                if (!this.wsClient?.isConnected) {
                    this.loadDemoData();
                }
            }, 3000);
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize application');
        } finally {
            this.hideLoading();
        }
        
        console.log('ArxOS ASCII-BIM PWA initialized successfully');
    }
    
    async initializeRenderer() {
        const canvasElement = document.getElementById('asciiCanvas');
        if (!canvasElement) {
            throw new Error('ASCII canvas element not found');
        }
        
        this.renderer = new ASCIIRenderer(canvasElement);
        console.log('ASCII renderer initialized');
    }
    
    async initializeWebSocket() {
        this.wsClient = new ArxOSWebSocketClient();
        
        // Set up event handlers
        this.wsClient.on('connect', () => {
            console.log('WebSocket connected');
        });
        
        this.wsClient.on('disconnect', () => {
            console.log('WebSocket disconnected');
            // Try to load cached data
            this.loadCachedData();
        });
        
        this.wsClient.on('object_update', (objects) => {
            this.handleObjectUpdate(objects);
        });
        
        this.wsClient.on('object_selected', (object) => {
            this.renderer.selectObject(object);
        });
        
        this.wsClient.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.showError('Connection error occurred');
        });
        
        console.log('WebSocket client initialized');
    }
    
    setupEventHandlers() {
        // Building selector
        const buildingSelect = document.getElementById('buildingSelect');
        if (buildingSelect) {
            buildingSelect.addEventListener('change', (e) => {
                this.selectBuilding(e.target.value);
            });
        }
        
        // Floor selector
        const floorSelect = document.getElementById('floorSelect');
        if (floorSelect) {
            floorSelect.addEventListener('change', (e) => {
                this.selectFloor(e.target.value);
            });
        }
        
        // Zoom slider
        const zoomSlider = document.getElementById('zoomSlider');
        if (zoomSlider) {
            zoomSlider.addEventListener('input', (e) => {
                this.renderer.setZoom(parseFloat(e.target.value));
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }
        
        // Fullscreen button
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => {
                this.toggleFullscreen();
            });
        }
        
        // Mobile menu button
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                this.toggleMobileSidebar();
            });
        }
        
        // Mobile overlay
        const mobileOverlay = document.getElementById('mobileOverlay');
        if (mobileOverlay) {
            mobileOverlay.addEventListener('click', () => {
                this.closeMobileSidebar();
            });
        }
        
        // Sidebar tabs
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchSidebarTab(e.target.dataset.tab);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcut(e);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // Viewport change detection for WebSocket updates
        let viewportUpdateTimeout = null;
        if (this.renderer) {
            const originalPanTo = this.renderer.panTo.bind(this.renderer);
            this.renderer.panTo = (x, y) => {
                originalPanTo(x, y);
                
                // Debounce viewport updates
                clearTimeout(viewportUpdateTimeout);
                viewportUpdateTimeout = setTimeout(() => {
                    this.updateServerViewport();
                }, 300);
            };
        }
    }
    
    handleResponsiveDesign() {
        this.updateMobileUI();
        
        // Update on resize
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            if (wasMobile !== this.isMobile) {
                this.updateMobileUI();
            }
        });
    }
    
    updateMobileUI() {
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const sidebar = document.getElementById('sidebar');
        
        if (this.isMobile) {
            if (mobileMenuBtn) mobileMenuBtn.style.display = 'block';
            if (sidebar) {
                sidebar.classList.remove('mobile-open');
                this.sidebarVisible = false;
            }
        } else {
            if (mobileMenuBtn) mobileMenuBtn.style.display = 'none';
            if (sidebar) {
                sidebar.classList.remove('mobile-open');
                this.sidebarVisible = true;
            }
        }
    }
    
    handleObjectUpdate(objects) {
        console.log('Received object update:', objects.length, 'objects');
        
        // Update renderer
        this.renderer.updateObjects(objects);
        
        // Cache building data for offline use
        if (this.currentBuilding && window.pwaManager) {
            pwaManager.cacheBuilding(this.currentBuilding, {
                objects: objects,
                floor: this.currentFloor,
                timestamp: Date.now()
            });
        }
        
        // Fit to objects on first load
        if (objects.length > 0 && !this.hasObjects) {
            this.hasObjects = true;
            setTimeout(() => {
                this.renderer.fitToObjects();
            }, 100);
        }
    }
    
    selectBuilding(buildingId) {
        if (!buildingId) return;
        
        console.log('Selecting building:', buildingId);
        this.currentBuilding = buildingId;
        
        // Handle cached building selection
        if (buildingId.startsWith('cached-')) {
            const buildingSelect = document.getElementById('buildingSelect');
            const option = buildingSelect.querySelector(`option[value="${buildingId}"]`);
            if (option && option.dataset.buildingData) {
                try {
                    const buildingData = JSON.parse(option.dataset.buildingData);
                    this.handleObjectUpdate(buildingData.objects || []);
                    return;
                } catch (error) {
                    console.error('Failed to parse cached building data:', error);
                }
            }
        }
        
        // Request from server
        if (this.wsClient && this.wsClient.isConnected) {
            this.showLoading('Loading building data...');
            this.wsClient.selectBuilding(buildingId);
        } else {
            this.showError('Cannot load building - not connected to server');
        }
    }
    
    selectFloor(floorId) {
        console.log('Selecting floor:', floorId);
        this.currentFloor = floorId;
        
        if (this.wsClient && this.wsClient.isConnected && this.currentBuilding) {
            this.showLoading('Loading floor data...');
            this.wsClient.selectFloor(floorId);
        }
    }
    
    refreshData() {
        if (this.currentBuilding) {
            console.log('Refreshing data for building:', this.currentBuilding);
            this.selectBuilding(this.currentBuilding);
        } else if (this.wsClient && this.wsClient.isConnected) {
            this.wsClient.requestBuildingList();
        }
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen()
                .then(() => console.log('Entered fullscreen'))
                .catch(err => console.error('Failed to enter fullscreen:', err));
        } else {
            document.exitFullscreen()
                .then(() => console.log('Exited fullscreen'))
                .catch(err => console.error('Failed to exit fullscreen:', err));
        }
    }
    
    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('mobileOverlay');
        
        if (sidebar && overlay) {
            if (this.sidebarVisible) {
                sidebar.classList.remove('mobile-open');
                overlay.classList.remove('active');
                this.sidebarVisible = false;
            } else {
                sidebar.classList.add('mobile-open');
                overlay.classList.add('active');
                this.sidebarVisible = true;
            }
        }
    }
    
    closeMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('mobileOverlay');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            this.sidebarVisible = false;
        }
    }
    
    switchSidebarTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update content panels
        document.querySelectorAll('[data-content]').forEach(panel => {
            panel.classList.toggle('active', panel.dataset.content === tabName);
        });
    }
    
    handleKeyboardShortcut(e) {
        // Only handle shortcuts when not in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch (e.key) {
            case 'f':
            case 'F':
                if (!e.ctrlKey && !e.metaKey) {
                    this.renderer.fitToObjects();
                    e.preventDefault();
                }
                break;
                
            case 'r':
            case 'R':
                if (!e.ctrlKey && !e.metaKey) {
                    this.refreshData();
                    e.preventDefault();
                }
                break;
                
            case '1':
            case '2':
            case '3':
                if (!e.ctrlKey && !e.metaKey) {
                    const tabNames = ['objects', 'properties', 'layers'];
                    const tabIndex = parseInt(e.key) - 1;
                    if (tabNames[tabIndex]) {
                        this.switchSidebarTab(tabNames[tabIndex]);
                        e.preventDefault();
                    }
                }
                break;
                
            case 'Escape':
                if (this.isMobile && this.sidebarVisible) {
                    this.closeMobileSidebar();
                    e.preventDefault();
                }
                break;
        }
    }
    
    handleResize() {
        if (this.renderer) {
            this.renderer.updateCanvasSize();
            this.renderer.render();
        }
        
        this.handleResponsiveDesign();
    }
    
    updateServerViewport() {
        if (this.wsClient && this.wsClient.isConnected && this.renderer) {
            const viewport = this.renderer.viewport;
            const canvasViewport = {
                minX: viewport.centerX - (this.renderer.width / 2) / viewport.scale,
                minY: viewport.centerY - (this.renderer.height / 2) / viewport.scale,
                maxX: viewport.centerX + (this.renderer.width / 2) / viewport.scale,
                maxY: viewport.centerY + (this.renderer.height / 2) / viewport.scale
            };
            
            this.wsClient.updateViewport(canvasViewport);
        }
    }
    
    loadDemoData() {
        console.log('Loading demo data...');
        
        // Create demo building data
        const demoObjects = [
            {
                id: 'demo/f1/room/1',
                type: 'room',
                name: 'Conference Room A',
                geometry: {
                    position: { x: 10, y: 10, z: 0 },
                    bounding_box: {
                        min: { x: 5, y: 5 },
                        max: { x: 15, y: 15 }
                    }
                },
                properties: { area_sqm: 25, room_type: 'meeting' },
                confidence: 0.95
            },
            {
                id: 'demo/f1/room/2',
                type: 'room',
                name: 'Office Space',
                geometry: {
                    position: { x: 25, y: 10, z: 0 },
                    bounding_box: {
                        min: { x: 20, y: 5 },
                        max: { x: 30, y: 15 }
                    }
                },
                properties: { area_sqm: 30, room_type: 'office' },
                confidence: 0.92
            },
            {
                id: 'demo/f1/wall/1',
                type: 'wall',
                name: 'North Wall',
                geometry: {
                    position: { x: 17.5, y: 15, z: 0 },
                    bounding_box: {
                        min: { x: 15, y: 14.8 },
                        max: { x: 20, y: 15.2 }
                    }
                },
                properties: { thickness_mm: 150, load_bearing: true },
                confidence: 0.98
            },
            {
                id: 'demo/f1/door/1',
                type: 'door',
                name: 'Main Entry',
                geometry: {
                    position: { x: 17.5, y: 5, z: 0 },
                    bounding_box: {
                        min: { x: 17, y: 4.8 },
                        max: { x: 18, y: 5.2 }
                    }
                },
                properties: { width_mm: 800, door_type: 'single' },
                confidence: 0.88
            },
            {
                id: 'demo/f1/window/1',
                type: 'window',
                name: 'Conference Window',
                geometry: {
                    position: { x: 10, y: 15, z: 0 },
                    bounding_box: {
                        min: { x: 8, y: 14.8 },
                        max: { x: 12, y: 15.2 }
                    }
                },
                properties: { width_mm: 1200, window_type: 'fixed' },
                confidence: 0.85
            }
        ];
        
        // Update building selector with demo option
        const buildingSelect = document.getElementById('buildingSelect');
        if (buildingSelect && !buildingSelect.querySelector('[value="demo"]')) {
            const option = document.createElement('option');
            option.value = 'demo';
            option.textContent = 'Demo Building (Offline)';
            buildingSelect.appendChild(option);
        }
        
        // Load demo objects
        this.handleObjectUpdate(demoObjects);
        
        console.log('Demo data loaded');
    }
    
    async loadCachedData() {
        if (window.pwaManager && this.currentBuilding) {
            try {
                const cached = await pwaManager.getCachedBuilding(this.currentBuilding);
                if (cached && cached.data && cached.data.objects) {
                    console.log('Loading cached building data');
                    this.handleObjectUpdate(cached.data.objects);
                }
            } catch (error) {
                console.error('Failed to load cached data:', error);
            }
        }
    }
    
    showLoading(message = 'Loading...') {
        this.isLoading = true;
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            const loadingText = loadingScreen.querySelector('div:last-child');
            if (loadingText) {
                loadingText.textContent = message;
            }
            loadingScreen.style.display = 'flex';
        }
    }
    
    hideLoading() {
        this.isLoading = false;
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
    }
    
    showError(message) {
        console.error('App error:', message);
        // Could implement proper error UI here
        alert(`Error: ${message}`);
    }
    
    // Cleanup
    destroy() {
        if (this.wsClient) {
            this.wsClient.destroy();
        }
        
        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('keydown', this.handleKeyboardShortcut);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.arxosApp = new ArxOSASCIIApp();
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});