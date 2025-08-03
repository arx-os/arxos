/**
 * Arxos CAD UI Integration
 * Handles UI interactions, precision controls, and real-time updates
 * 
 * @author Arxos Team
 * @version 1.1.0 - Enhanced Precision and Constraint UI
 * @license MIT
 */

class CadUI {
    constructor(cadEngine) {
        this.cadEngine = cadEngine;
        this.isInitialized = false;
        
        // UI state
        this.currentTool = 'select';
        this.precisionLevel = 'EDIT';
        this.gridSize = 0.1;
        this.gridSnapEnabled = true;
        
        // UI elements
        this.elements = {};
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Performance monitoring
        this.lastUpdateTime = 0;
        this.updateInterval = 16; // ~60 FPS
    }
    
    /**
     * Initialize the CAD UI
     */
    async initialize() {
        try {
            console.log('Initializing Arxos CAD UI...');
            
            // Initialize UI elements
            this.initializeElements();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize precision controls
            this.initializePrecisionControls();
            
            // Initialize constraint UI
            this.initializeConstraintUI();
            
            // Start UI update loop
            this.startUpdateLoop();
            
            this.isInitialized = true;
            console.log('Arxos CAD UI initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize CAD UI:', error);
            throw error;
        }
    }
    
    /**
     * Initialize UI elements
     */
    initializeElements() {
        // Tool buttons
        this.elements.toolButtons = {
            select: document.getElementById('select-tool'),
            line: document.getElementById('line-tool'),
            rectangle: document.getElementById('rectangle-tool'),
            circle: document.getElementById('circle-tool'),
            distanceConstraint: document.getElementById('distance-constraint'),
            parallelConstraint: document.getElementById('parallel-constraint'),
            perpendicularConstraint: document.getElementById('perpendicular-constraint')
        };
        
        // Precision controls
        this.elements.precisionLevel = document.getElementById('precision-level');
        this.elements.gridSize = document.getElementById('grid-size');
        this.elements.gridSnap = document.getElementById('grid-snap');
        
        // Status elements
        this.elements.mouseCoordinates = document.getElementById('mouse-coordinates');
        this.elements.drawingInfo = document.getElementById('drawing-info');
        this.elements.performanceInfo = document.getElementById('performance-info');
        
        // Panel elements
        this.elements.propertiesContent = document.getElementById('properties-content');
        this.elements.constraintsList = document.getElementById('constraints-list');
        this.elements.projectList = document.getElementById('project-list');
        this.elements.arxObjectsList = document.getElementById('arx-objects-list');
        
        // AI elements
        this.elements.aiModal = document.getElementById('ai-modal');
        this.elements.aiChat = document.getElementById('ai-chat');
        this.elements.aiInput = document.getElementById('ai-input');
        this.elements.aiSend = document.getElementById('ai-send');
        this.elements.aiAssistant = document.getElementById('ai-assistant');
        this.elements.closeAiModal = document.getElementById('close-ai-modal');
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Tool button events
        Object.entries(this.elements.toolButtons).forEach(([tool, element]) => {
            if (element) {
                element.addEventListener('click', () => this.setCurrentTool(tool));
            }
        });
        
        // Precision control events
        if (this.elements.precisionLevel) {
            this.elements.precisionLevel.addEventListener('change', (e) => {
                this.setPrecisionLevel(e.target.value);
            });
        }
        
        if (this.elements.gridSize) {
            this.elements.gridSize.addEventListener('change', (e) => {
                this.setGridSize(parseFloat(e.target.value));
            });
        }
        
        if (this.elements.gridSnap) {
            this.elements.gridSnap.addEventListener('change', (e) => {
                this.setGridSnap(e.target.checked);
            });
        }
        
        // AI assistant events
        if (this.elements.aiAssistant) {
            this.elements.aiAssistant.addEventListener('click', () => {
                this.showAIModal();
            });
        }
        
        if (this.elements.closeAiModal) {
            this.elements.closeAiModal.addEventListener('click', () => {
                this.hideAIModal();
            });
        }
        
        if (this.elements.aiSend) {
            this.elements.aiSend.addEventListener('click', () => {
                this.sendAIMessage();
            });
        }
        
        // Listen for CAD engine events
        this.cadEngine.addEventListener('precisionChanged', (data) => {
            this.updatePrecisionDisplay(data);
        });
        
        this.cadEngine.addEventListener('objectSelected', (data) => {
            this.updatePropertiesPanel(data.object);
        });
        
        this.cadEngine.addEventListener('constraintAdded', (data) => {
            this.updateConstraintsList();
        });
    }
    
    /**
     * Initialize precision controls
     */
    initializePrecisionControls() {
        // Set initial precision level
        this.setPrecisionLevel(this.precisionLevel);
        
        // Set initial grid size
        this.setGridSize(this.gridSize);
        
        // Set initial grid snap
        this.setGridSnap(this.gridSnapEnabled);
        
        console.log('Precision controls initialized');
    }
    
    /**
     * Initialize constraint UI
     */
    initializeConstraintUI() {
        // Set up constraint button handlers
        if (this.elements.toolButtons.distanceConstraint) {
            this.elements.toolButtons.distanceConstraint.addEventListener('click', () => {
                this.activateConstraintMode('DISTANCE');
            });
        }
        
        if (this.elements.toolButtons.parallelConstraint) {
            this.elements.toolButtons.parallelConstraint.addEventListener('click', () => {
                this.activateConstraintMode('PARALLEL');
            });
        }
        
        if (this.elements.toolButtons.perpendicularConstraint) {
            this.elements.toolButtons.perpendicularConstraint.addEventListener('click', () => {
                this.activateConstraintMode('PERPENDICULAR');
            });
        }
        
        console.log('Constraint UI initialized');
    }
    
    /**
     * Set current tool
     */
    setCurrentTool(tool) {
        // Update tool button states
        Object.entries(this.elements.toolButtons).forEach(([toolName, element]) => {
            if (element) {
                element.classList.remove('active');
                if (toolName === tool) {
                    element.classList.add('active');
                }
            }
        });
        
        // Update CAD engine
        this.cadEngine.setCurrentTool(tool);
        this.currentTool = tool;
        
        console.log(`Tool changed to: ${tool}`);
    }
    
    /**
     * Set precision level
     */
    setPrecisionLevel(level) {
        this.precisionLevel = level;
        
        // Update CAD engine
        this.cadEngine.setPrecisionLevel(level);
        
        // Update UI
        if (this.elements.precisionLevel) {
            this.elements.precisionLevel.value = level;
        }
        
        console.log(`Precision level set to: ${level}`);
    }
    
    /**
     * Set grid size
     */
    setGridSize(size) {
        this.gridSize = size;
        
        // Update CAD engine
        this.cadEngine.gridSize = size;
        
        // Update UI
        if (this.elements.gridSize) {
            this.elements.gridSize.value = size;
        }
        
        console.log(`Grid size set to: ${size}`);
    }
    
    /**
     * Set grid snap
     */
    setGridSnap(enabled) {
        this.gridSnapEnabled = enabled;
        
        // Update UI
        if (this.elements.gridSnap) {
            this.elements.gridSnap.checked = enabled;
        }
        
        console.log(`Grid snap ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Activate constraint mode
     */
    activateConstraintMode(constraintType) {
        // Set tool to select mode for constraint selection
        this.setCurrentTool('select');
        
        // Store constraint type for next selection
        this.cadEngine.constraintMode = constraintType;
        
        console.log(`Constraint mode activated: ${constraintType}`);
        
        // Show constraint mode indicator
        this.showConstraintModeIndicator(constraintType);
    }
    
    /**
     * Show constraint mode indicator
     */
    showConstraintModeIndicator(constraintType) {
        // Create or update constraint mode indicator
        let indicator = document.getElementById('constraint-mode-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'constraint-mode-indicator';
            indicator.className = 'fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow-lg z-50';
            document.body.appendChild(indicator);
        }
        
        indicator.textContent = `Constraint Mode: ${constraintType}`;
        indicator.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 3000);
    }
    
    /**
     * Update precision display
     */
    updatePrecisionDisplay(data) {
        if (this.elements.mouseCoordinates) {
            const precisionText = `(${data.level})`;
            this.elements.mouseCoordinates.textContent = `X: 0.000" Y: 0.000" ${precisionText}`;
        }
        
        if (this.elements.drawingInfo) {
            this.elements.drawingInfo.textContent = `Scale: 1:1 | Units: ${data.units} | Grid: ${this.gridSize}"`;
        }
    }
    
    /**
     * Update properties panel
     */
    updatePropertiesPanel(object) {
        if (!this.elements.propertiesContent) return;
        
        if (!object) {
            this.elements.propertiesContent.innerHTML = '<div class="text-gray-400 text-sm">Select an object to view properties</div>';
            return;
        }
        
        const propertiesHTML = this.generatePropertiesHTML(object);
        this.elements.propertiesContent.innerHTML = propertiesHTML;
    }
    
    /**
     * Generate properties HTML
     */
    generatePropertiesHTML(object) {
        return `
            <div class="space-y-4">
                <div class="border-b border-gray-700 pb-2">
                    <h4 class="text-sm font-medium text-gray-300">Object Properties</h4>
                    <div class="text-xs text-gray-400">ID: ${object.id}</div>
                    <div class="text-xs text-gray-400">Type: ${object.type}</div>
                </div>
                
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">X Position:</span>
                        <span class="text-sm text-white">${object.x?.toFixed(3) || '0.000'}"</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">Y Position:</span>
                        <span class="text-sm text-white">${object.y?.toFixed(3) || '0.000'}"</span>
                    </div>
                    ${object.width ? `
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">Width:</span>
                        <span class="text-sm text-white">${object.width.toFixed(3)}"</span>
                    </div>
                    ` : ''}
                    ${object.height ? `
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">Height:</span>
                        <span class="text-sm text-white">${object.height.toFixed(3)}"</span>
                    </div>
                    ` : ''}
                    ${object.length ? `
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">Length:</span>
                        <span class="text-sm text-white">${object.length.toFixed(3)}"</span>
                    </div>
                    ` : ''}
                    ${object.angle ? `
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-400">Angle:</span>
                        <span class="text-sm text-white">${object.angle.toFixed(1)}°</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="border-t border-gray-700 pt-2">
                    <button class="w-full bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm">
                        Edit Properties
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Update constraints list
     */
    updateConstraintsList() {
        if (!this.elements.constraintsList) return;
        
        const constraints = this.cadEngine.constraintSolver.constraints;
        const constraintsArray = Array.from(constraints.values());
        
        if (constraintsArray.length === 0) {
            this.elements.constraintsList.innerHTML = '<div class="text-gray-400 text-sm">No constraints</div>';
            return;
        }
        
        const constraintsHTML = constraintsArray.map(constraint => `
            <div class="flex items-center justify-between p-2 bg-gray-700 rounded text-sm">
                <div>
                    <div class="text-white">${constraint.type}</div>
                    <div class="text-gray-400 text-xs">${constraint.id}</div>
                </div>
                <button class="text-red-400 hover:text-red-300 text-xs" 
                        onclick="window.cadApp.cadEngine.constraintSolver.removeConstraint('${constraint.id}')">
                    Remove
                </button>
            </div>
        `).join('');
        
        this.elements.constraintsList.innerHTML = constraintsHTML;
    }
    
    /**
     * Show AI modal
     */
    showAIModal() {
        if (this.elements.aiModal) {
            this.elements.aiModal.classList.remove('hidden');
        }
    }
    
    /**
     * Hide AI modal
     */
    hideAIModal() {
        if (this.elements.aiModal) {
            this.elements.aiModal.classList.add('hidden');
        }
    }
    
    /**
     * Send AI message
     */
    sendAIMessage() {
        if (!this.elements.aiInput || !this.elements.aiChat) return;
        
        const message = this.elements.aiInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addAIMessage('user', message);
        
        // Clear input
        this.elements.aiInput.value = '';
        
        // Simulate AI response (replace with actual AI integration)
        setTimeout(() => {
            this.addAIMessage('assistant', `I understand you want to: ${message}. How can I help you with this CAD operation?`);
        }, 1000);
    }
    
    /**
     * Add AI message to chat
     */
    addAIMessage(sender, message) {
        if (!this.elements.aiChat) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${sender} mb-2 p-2 rounded`;
        messageDiv.innerHTML = `
            <div class="text-sm">
                <span class="font-medium">${sender === 'user' ? 'You' : 'GUS Assistant'}:</span>
                <span class="ml-2">${message}</span>
            </div>
        `;
        
        this.elements.aiChat.appendChild(messageDiv);
        this.elements.aiChat.scrollTop = this.elements.aiChat.scrollHeight;
    }
    
    /**
     * Start UI update loop
     */
    startUpdateLoop() {
        const update = () => {
            const currentTime = performance.now();
            
            if (currentTime - this.lastUpdateTime >= this.updateInterval) {
                this.updateUI();
                this.lastUpdateTime = currentTime;
            }
            
            requestAnimationFrame(update);
        };
        
        requestAnimationFrame(update);
    }
    
    /**
     * Update UI elements
     */
    updateUI() {
        // Update performance info
        if (this.elements.performanceInfo) {
            const fps = Math.round(1000 / this.updateInterval);
            const objectCount = this.cadEngine.arxObjects.size;
            const constraintCount = this.cadEngine.constraintSolver.constraints.size;
            
            this.elements.performanceInfo.textContent = `FPS: ${fps} | Objects: ${objectCount} | Constraints: ${constraintCount}`;
        }
        
        // Update mouse coordinates if mouse is over canvas
        if (this.cadEngine.currentPoint && this.elements.mouseCoordinates) {
            const point = this.cadEngine.currentPoint;
            const precisionText = `(${this.precisionLevel})`;
            this.elements.mouseCoordinates.textContent = `X: ${point.x.toFixed(3)}" Y: ${point.y.toFixed(3)}" ${precisionText}`;
        }
    }
    
    /**
     * Add event listener
     */
    addEventListener(eventType, callback) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(callback);
    }
    
    /**
     * Remove event listener
     */
    removeEventListener(eventType, callback) {
        if (this.eventHandlers.has(eventType)) {
            const handlers = this.eventHandlers.get(eventType);
            const index = handlers.indexOf(callback);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    /**
     * Dispatch event
     */
    dispatchEvent(eventType, data) {
        if (this.eventHandlers.has(eventType)) {
            this.eventHandlers.get(eventType).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event handler:', error);
                }
            });
        }
    }
} 