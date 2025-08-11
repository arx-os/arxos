/**
 * BIM Foundation Module
 * Foundation for Building Information Modeling integration
 * Prepares for future React/TS BIM web app integration
 */

class BIMFoundation {
    constructor() {
        this.isInitialized = false;
        this.bimMode = false;
        this.viewerContainer = null;
        this.modelData = null;
        
        this.initializeFoundation();
    }

    /**
     * Initialize BIM foundation
     */
    initializeFoundation() {
        this.createBIMInterface();
        this.setupEventListeners();
        this.prepareModelViewerContainer();
        this.initializeLoadingSystem();
        
        this.isInitialized = true;
        console.log('BIM Foundation initialized - ready for React/TS integration');
    }

    /**
     * Create BIM interface elements
     */
    createBIMInterface() {
        // Create BIM toggle button
        this.createBIMToggleButton();
        
        // Create placeholder for future BIM viewer
        this.createBIMViewerPlaceholder();
        
        // Create BIM controls interface
        this.createBIMControls();
    }

    /**
     * Create BIM toggle button
     */
    createBIMToggleButton() {
        const bimToggle = document.createElement('button');
        bimToggle.id = 'bim-toggle';
        bimToggle.className = 'fixed bottom-6 right-6 btn btn-primary btn-lg z-40 shadow-lg';
        bimToggle.innerHTML = `
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            Launch BIM Viewer
        `;
        
        bimToggle.addEventListener('click', () => {
            this.toggleBIMMode();
        });
        
        document.body.appendChild(bimToggle);
    }

    /**
     * Create BIM viewer placeholder
     */
    createBIMViewerPlaceholder() {
        const bimContainer = document.createElement('div');
        bimContainer.id = 'bim-container';
        bimContainer.className = 'fixed inset-0 bg-gray-900 z-50 hidden';
        
        bimContainer.innerHTML = `
            <div class="flex flex-col h-full">
                <!-- BIM Header -->
                <div class="bg-gray-800 border-b border-gray-700 p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <h2 class="text-white text-xl font-semibold">BIM Viewer</h2>
                            <div class="text-gray-400 text-sm">Ready for React/TypeScript Integration</div>
                        </div>
                        
                        <div class="flex items-center space-x-2">
                            <button id="bim-settings" class="text-gray-400 hover:text-white p-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                            </button>
                            
                            <button id="bim-close" class="text-gray-400 hover:text-white p-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- BIM Content Area -->
                <div class="flex flex-1 overflow-hidden">
                    <!-- Sidebar -->
                    <div class="w-80 bg-gray-800 border-r border-gray-700 overflow-y-auto">
                        <div class="p-4">
                            <h3 class="text-white font-semibold mb-4">Model Explorer</h3>
                            
                            <!-- Building Tree -->
                            <div id="building-tree" class="space-y-2">
                                <div class="text-gray-300 text-sm">Building Structure:</div>
                                <div class="ml-4 space-y-1">
                                    <div class="text-blue-400 cursor-pointer hover:text-blue-300">🏢 Office Complex</div>
                                    <div class="ml-4 space-y-1">
                                        <div class="text-green-400 cursor-pointer hover:text-green-300">📐 Floor 1</div>
                                        <div class="text-green-400 cursor-pointer hover:text-green-300">📐 Floor 2</div>
                                        <div class="text-green-400 cursor-pointer hover:text-green-300">📐 Floor 3</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Properties Panel -->
                            <div class="mt-6">
                                <h4 class="text-white font-semibold mb-2">Properties</h4>
                                <div class="bg-gray-700 rounded p-3">
                                    <div class="text-gray-300 text-sm space-y-2">
                                        <div><strong>Type:</strong> Commercial Building</div>
                                        <div><strong>Area:</strong> 4,000 m²</div>
                                        <div><strong>Floors:</strong> 3</div>
                                        <div><strong>Occupancy:</strong> 450 people</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Main Viewer Area -->
                    <div class="flex-1 flex flex-col">
                        <!-- Viewer Container -->
                        <div id="bim-viewer" class="flex-1 bg-gray-900 relative">
                            <div class="absolute inset-0 flex items-center justify-center">
                                <div class="text-center">
                                    <div class="text-6xl mb-4">🏗️</div>
                                    <h3 class="text-2xl text-white font-semibold mb-4">BIM Viewer Foundation</h3>
                                    <p class="text-gray-400 mb-6 max-w-md">
                                        This area is prepared for React/TypeScript BIM viewer integration.
                                        Future features will include 3D model rendering, real-time optimization
                                        visualization, and collaborative editing.
                                    </p>
                                    
                                    <div class="grid grid-cols-2 gap-4 text-left max-w-lg mx-auto">
                                        <div class="bg-gray-800 p-4 rounded">
                                            <div class="text-green-400 font-semibold mb-2">✓ Ready for Integration</div>
                                            <div class="text-gray-300 text-sm">Container and event system prepared</div>
                                        </div>
                                        
                                        <div class="bg-gray-800 p-4 rounded">
                                            <div class="text-blue-400 font-semibold mb-2">🔄 API Connected</div>
                                            <div class="text-gray-300 text-sm">Backend optimization data available</div>
                                        </div>
                                        
                                        <div class="bg-gray-800 p-4 rounded">
                                            <div class="text-purple-400 font-semibold mb-2">📊 Real-time Data</div>
                                            <div class="text-gray-300 text-sm">WebSocket integration for live updates</div>
                                        </div>
                                        
                                        <div class="bg-gray-800 p-4 rounded">
                                            <div class="text-yellow-400 font-semibold mb-2">🎨 UI Foundation</div>
                                            <div class="text-gray-300 text-sm">Responsive layout and controls ready</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- BIM Controls -->
                        <div id="bim-controls" class="bg-gray-800 border-t border-gray-700 p-4">
                            <!-- Controls will be populated by createBIMControls() -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(bimContainer);
        this.viewerContainer = bimContainer;
    }

    /**
     * Create BIM controls
     */
    createBIMControls() {
        const controlsContainer = document.getElementById('bim-controls');
        if (!controlsContainer) return;
        
        controlsContainer.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <!-- View Controls -->
                    <div class="flex items-center space-x-2">
                        <span class="text-gray-400 text-sm">View:</span>
                        <button class="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 active">3D</button>
                        <button class="px-3 py-1 bg-gray-700 text-gray-400 rounded hover:bg-gray-600">Floor Plan</button>
                        <button class="px-3 py-1 bg-gray-700 text-gray-400 rounded hover:bg-gray-600">Section</button>
                    </div>
                    
                    <!-- Analysis Tools -->
                    <div class="flex items-center space-x-2">
                        <span class="text-gray-400 text-sm">Analysis:</span>
                        <button class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-500">Optimization</button>
                        <button class="px-3 py-1 bg-gray-700 text-gray-400 rounded hover:bg-gray-600">Conflicts</button>
                        <button class="px-3 py-1 bg-gray-700 text-gray-400 rounded hover:bg-gray-600">Constraints</button>
                    </div>
                </div>
                
                <div class="flex items-center space-x-2">
                    <!-- Measurement Tools -->
                    <button class="p-2 bg-gray-700 text-gray-400 rounded hover:bg-gray-600" title="Measure">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM7 3V1m0 18v2m8-10h2m0 0h2m-2 0v2m0-2v-2"></path>
                        </svg>
                    </button>
                    
                    <!-- Export/Import -->
                    <button class="p-2 bg-gray-700 text-gray-400 rounded hover:bg-gray-600" title="Export">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for BIM-related events
        document.addEventListener('click', (e) => {
            if (e.target.id === 'bim-close') {
                this.closeBIMMode();
            }
            
            if (e.target.id === 'bim-settings') {
                this.showBIMSettings();
            }
        });
        
        // Listen for optimization updates when in BIM mode
        if (window.realTimeData) {
            window.realTimeData.subscribe('optimization', (data) => {
                if (this.bimMode) {
                    this.updateBIMVisualization(data);
                }
            });
        }
        
        // Listen for building data updates
        if (window.realTimeData) {
            window.realTimeData.subscribe('building:changed', (data) => {
                if (this.bimMode) {
                    this.updateBuildingModel(data);
                }
            });
        }
    }

    /**
     * Prepare model viewer container for future integration
     */
    prepareModelViewerContainer() {
        // Set up container properties that React/TS components will expect
        this.viewerConfig = {
            container: '#bim-viewer',
            dimensions: {
                width: '100%',
                height: '100%'
            },
            features: {
                optimization: true,
                collaboration: true,
                realTime: true,
                constraints: true,
                measurements: true
            },
            api: {
                client: window.arxosAPI,
                realTime: window.realTimeData
            }
        };
        
        // Expose configuration globally for React components
        window.BIMViewerConfig = this.viewerConfig;
    }

    /**
     * Initialize loading system for models
     */
    initializeLoadingSystem() {
        this.loadingStates = {
            IDLE: 'idle',
            LOADING: 'loading', 
            LOADED: 'loaded',
            ERROR: 'error'
        };
        
        this.currentLoadingState = this.loadingStates.IDLE;
    }

    /**
     * Toggle BIM mode
     */
    toggleBIMMode() {
        if (!this.bimMode) {
            this.enterBIMMode();
        } else {
            this.closeBIMMode();
        }
    }

    /**
     * Enter BIM mode
     */
    enterBIMMode() {
        this.bimMode = true;
        
        if (this.viewerContainer) {
            this.viewerContainer.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            // Trigger BIM mode event
            this.dispatchBIMEvent('bim:entered');
            
            // Load building data if available
            this.loadBuildingData();
        }
    }

    /**
     * Close BIM mode
     */
    closeBIMMode() {
        this.bimMode = false;
        
        if (this.viewerContainer) {
            this.viewerContainer.classList.add('hidden');
            document.body.style.overflow = '';
            
            // Trigger BIM mode event
            this.dispatchBIMEvent('bim:exited');
        }
    }

    /**
     * Show BIM settings modal
     */
    showBIMSettings() {
        // Create settings modal
        const settingsModal = document.createElement('div');
        settingsModal.className = 'fixed inset-0 bg-black bg-opacity-50 z-60 flex items-center justify-center';
        
        settingsModal.innerHTML = `
            <div class="bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-white text-lg font-semibold">BIM Settings</h3>
                        <button class="text-gray-400 hover:text-white" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Rendering Quality</label>
                            <select class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white">
                                <option>High (Recommended)</option>
                                <option>Medium</option>
                                <option>Low</option>
                            </select>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-gray-300">Real-time Updates</span>
                            <input type="checkbox" checked class="form-checkbox h-4 w-4 text-blue-600">
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-gray-300">Show Optimization Overlay</span>
                            <input type="checkbox" checked class="form-checkbox h-4 w-4 text-blue-600">
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-gray-300">Collaboration Mode</span>
                            <input type="checkbox" class="form-checkbox h-4 w-4 text-blue-600">
                        </div>
                    </div>
                    
                    <div class="mt-6 flex justify-end space-x-2">
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" 
                                class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500">
                            Cancel
                        </button>
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" 
                                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500">
                            Apply
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(settingsModal);
    }

    /**
     * Load building data for BIM viewer
     */
    async loadBuildingData() {
        if (!window.arxosAPI) {
            console.log('API client not available - using mock data');
            this.loadMockBuildingData();
            return;
        }
        
        try {
            this.currentLoadingState = this.loadingStates.LOADING;
            
            // Try to load buildings from API
            const response = await window.arxosAPI.getBuildings({ page_size: 1 });
            
            if (response.success && response.data.buildings.length > 0) {
                this.modelData = response.data.buildings[0];
                this.currentLoadingState = this.loadingStates.LOADED;
                this.updateBuildingProperties(this.modelData);
            } else {
                this.loadMockBuildingData();
            }
            
        } catch (error) {
            console.log('Failed to load building data from API - using mock data');
            this.loadMockBuildingData();
        }
    }

    /**
     * Load mock building data
     */
    loadMockBuildingData() {
        this.modelData = {
            id: 'mock_building_1',
            name: 'Modern Office Complex',
            type: 'Commercial Building',
            area: 4000,
            floors: 3,
            occupancy: 450,
            optimization_score: 87.3,
            floors_data: [
                { id: 'floor_1', name: 'Ground Floor', area: 1500, rooms: 15 },
                { id: 'floor_2', name: 'Second Floor', area: 1400, rooms: 18 },
                { id: 'floor_3', name: 'Third Floor', area: 1100, rooms: 12 }
            ]
        };
        
        this.currentLoadingState = this.loadingStates.LOADED;
        this.updateBuildingProperties(this.modelData);
    }

    /**
     * Update building properties in UI
     */
    updateBuildingProperties(buildingData) {
        const propertiesPanel = document.querySelector('#bim-container .bg-gray-700');
        if (propertiesPanel && buildingData) {
            propertiesPanel.innerHTML = `
                <div class="text-gray-300 text-sm space-y-2">
                    <div><strong>Name:</strong> ${buildingData.name}</div>
                    <div><strong>Type:</strong> ${buildingData.type || 'Commercial Building'}</div>
                    <div><strong>Area:</strong> ${buildingData.area?.toLocaleString()} m²</div>
                    <div><strong>Floors:</strong> ${buildingData.floors}</div>
                    <div><strong>Occupancy:</strong> ${buildingData.occupancy} people</div>
                    ${buildingData.optimization_score ? 
                        `<div><strong>Optimization:</strong> <span class="text-green-400">${buildingData.optimization_score}%</span></div>` : ''}
                </div>
            `;
        }
    }

    /**
     * Update BIM visualization with optimization data
     */
    updateBIMVisualization(optimizationData) {
        console.log('BIM visualization update:', optimizationData);
        
        // This is where React/TS components would receive the optimization data
        // For now, we just log it and update some UI elements
        
        if (optimizationData.convergence) {
            // Update optimization status in UI
            const optimizationButton = document.querySelector('#bim-controls .bg-blue-600');
            if (optimizationButton) {
                optimizationButton.textContent = `Optimization (${optimizationData.convergence}%)`;
            }
        }
        
        // Dispatch event for future React components
        this.dispatchBIMEvent('bim:optimization_update', optimizationData);
    }

    /**
     * Update building model
     */
    updateBuildingModel(buildingData) {
        console.log('Building model update:', buildingData);
        
        this.modelData = { ...this.modelData, ...buildingData };
        this.updateBuildingProperties(this.modelData);
        
        // Dispatch event for future React components
        this.dispatchBIMEvent('bim:model_update', buildingData);
    }

    /**
     * Dispatch BIM events
     */
    dispatchBIMEvent(eventType, data = null) {
        const event = new CustomEvent(eventType, { 
            detail: data,
            bubbles: true
        });
        
        document.dispatchEvent(event);
    }

    /**
     * Get BIM integration readiness status
     */
    getIntegrationReadiness() {
        return {
            foundation: this.isInitialized,
            apiClient: !!window.arxosAPI,
            realTimeData: !!window.realTimeData,
            viewerContainer: !!this.viewerContainer,
            eventSystem: true,
            configurationReady: !!window.BIMViewerConfig,
            loadingSystem: this.currentLoadingState !== this.loadingStates.ERROR
        };
    }

    /**
     * Prepare for React/TS component integration
     */
    prepareReactIntegration() {
        // This method will be called when React/TS BIM components are ready to integrate
        return {
            containerSelector: '#bim-viewer',
            configuration: this.viewerConfig,
            initialData: this.modelData,
            eventHandlers: {
                onOptimizationUpdate: (data) => this.updateBIMVisualization(data),
                onModelUpdate: (data) => this.updateBuildingModel(data),
                onViewerReady: () => this.dispatchBIMEvent('bim:viewer_ready')
            },
            apiIntegration: {
                client: window.arxosAPI,
                realTime: window.realTimeData
            }
        };
    }
}

// Initialize BIM Foundation
document.addEventListener('DOMContentLoaded', () => {
    window.bimFoundation = new BIMFoundation();
    
    // Expose integration interface for future React/TS components
    window.getBIMIntegrationInterface = () => {
        return window.bimFoundation.prepareReactIntegration();
    };
    
    // Expose readiness check
    window.checkBIMReadiness = () => {
        return window.bimFoundation.getIntegrationReadiness();
    };
    
    console.log('BIM Foundation ready for React/TypeScript integration');
    console.log('Integration interface available at: window.getBIMIntegrationInterface()');
});

// Export for external use
window.BIMFoundation = BIMFoundation;