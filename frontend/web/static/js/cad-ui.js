/**
 * Arxos CAD UI Manager
 * Handles user interface interactions and integrates all CAD components
 * 
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class CadApplication {
    constructor() {
        this.cadEngine = null;
        this.arxObjectSystem = null;
        this.aiAssistant = null;
        this.apiClient = null;
        this.isInitialized = false;
        
        // UI state
        this.currentTool = 'select';
        this.selectedObjects = new Set();
        this.previewMode = false;
        
        // Project management
        this.currentProject = null;
        this.currentBuilding = null;
        this.currentFloor = null;
        
        // Performance tracking
        this.lastRenderTime = 0;
        this.frameCount = 0;
        this.fps = 60;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Auto-save interval
        this.autoSaveInterval = null;
        this.autoSaveEnabled = true;
    }
    
    /**
     * Initialize the CAD application
     */
    async initialize() {
        try {
            console.log('Initializing Arxos CAD Application...');
            
            // Initialize CAD Engine
            this.cadEngine = new CadEngine();
            await this.cadEngine.initialize();
            
            // Initialize ArxObject System
            this.arxObjectSystem = new ArxObjectSystem();
            
            // Initialize AI Assistant
            this.aiAssistant = new AiAssistant();
            
            // Initialize API Client
            this.apiClient = new CadApiClient();
            
            // Initialize Collaboration System
            this.collaboration = new CadCollaboration(this, this.apiClient);
            
            // Initialize AI Integration System
            this.aiIntegration = new CadAiIntegration(this, this.apiClient);
            
            // Initialize UI components
            this.initializeUI();
            
            // Initialize event handlers
            this.initializeEventHandlers();
            
            // Load ArxObjects library
            this.loadArxObjectsLibrary();
            
            // Initialize project management
            this.initializeProjectManagement();
            
            // Start auto-save
            this.startAutoSave();
            
            // Initialize collaboration if project is loaded
            if (this.currentProject) {
                this.initializeCollaboration();
            }
            
            // Initialize AI integration
            this.initializeAiIntegration();
            
            this.isInitialized = true;
            console.log('Arxos CAD Application initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize CAD Application:', error);
            throw error;
        }
    }
    
    /**
     * Initialize UI components
     */
    initializeUI() {
        // Initialize tool buttons
        this.initializeToolButtons();
        
        // Initialize precision controls
        this.initializePrecisionControls();
        
                    // Initialize save/export buttons
            this.initializeActionButtons();
            
            // Initialize project management buttons
            this.initializeProjectButtons();
        
        // Initialize AI assistant
        this.initializeAiAssistant();
        
        // Initialize properties panel
        this.initializePropertiesPanel();
        
        console.log('UI components initialized');
    }
    
    /**
     * Initialize tool buttons
     */
    initializeToolButtons() {
        const toolButtons = document.querySelectorAll('.cad-tool-btn');
        toolButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tool = button.dataset.tool;
                this.setCurrentTool(tool);
                
                // Update active state
                toolButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update cursor
                this.updateCursor(tool);
            });
        });
    }
    
    /**
     * Initialize precision controls
     */
    initializePrecisionControls() {
        const precisionSelect = document.getElementById('precision-select');
        if (precisionSelect) {
            precisionSelect.addEventListener('change', (e) => {
                const precision = parseFloat(e.target.value);
                this.setPrecision(precision);
            });
        }
    }
    
    /**
     * Initialize action buttons
     */
    initializeActionButtons() {
        // Save project button
        const saveButton = document.getElementById('save-project');
        if (saveButton) {
            saveButton.addEventListener('click', () => {
                this.saveProject();
            });
        }
        
                    // Export drawing button
            const exportButton = document.getElementById('export-drawing');
            if (exportButton) {
                exportButton.addEventListener('click', () => {
                    this.exportToSVGX();
                });
            }
        }
        
        /**
         * Initialize project management buttons
         */
        initializeProjectButtons() {
            // New project button
            const newProjectButton = document.getElementById('new-project');
            if (newProjectButton) {
                newProjectButton.addEventListener('click', () => {
                    this.showNewProjectModal();
                });
            }
            
            // Save project button
            const saveButton = document.getElementById('save-project');
            if (saveButton) {
                saveButton.addEventListener('click', () => {
                    this.saveProject();
                });
            }
        }
        
        /**
         * Initialize collaboration chat
         */
        initializeCollaborationChat() {
            const chatInput = document.getElementById('chat-input');
            const sendChatButton = document.getElementById('send-chat');
            
            if (sendChatButton) {
                sendChatButton.addEventListener('click', () => {
                    this.sendCollaborationMessage();
                });
            }
            
            if (chatInput) {
                chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendCollaborationMessage();
                    }
                });
            }
        }
        
        /**
         * Send collaboration chat message
         */
        sendCollaborationMessage() {
            const chatInput = document.getElementById('chat-input');
            if (!chatInput || !this.collaboration) return;
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            this.collaboration.sendChatMessage(message);
            chatInput.value = '';
        }
    
    /**
     * Initialize AI assistant
     */
    initializeAiAssistant() {
        const aiButton = document.getElementById('ai-assistant');
        const aiModal = document.getElementById('ai-modal');
        const closeButton = document.getElementById('close-ai-modal');
        const aiInput = document.getElementById('ai-input');
        const aiSend = document.getElementById('ai-send');
        
        if (aiButton) {
            aiButton.addEventListener('click', () => {
                this.openAiAssistant();
            });
        }
        
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.closeAiAssistant();
            });
        }
        
        if (aiSend) {
            aiSend.addEventListener('click', () => {
                this.sendAiMessage();
            });
        }
        
        if (aiInput) {
            aiInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendAiMessage();
                }
            });
        }
    }
    
    /**
     * Initialize properties panel
     */
    initializePropertiesPanel() {
        // Properties panel will be updated dynamically
        // based on selected objects
    }
    
    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcut(e);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
        
        // Selection changes - we'll handle this manually for now
        // this.cadEngine.addEventListener('selectionChanged', (e) => {
        //     this.handleSelectionChanged(e);
        // });
        
        // Object creation - we'll handle this manually for now
        // this.cadEngine.addEventListener('objectCreated', (e) => {
        //     this.handleObjectCreated(e);
        // });
        
        // Object deletion - we'll handle this manually for now
        // this.cadEngine.addEventListener('objectDeleted', (e) => {
        //     this.handleObjectDeleted(e);
        // });
    }
    
    /**
     * Load ArxObjects library
     */
    loadArxObjectsLibrary() {
        const arxObjectsList = document.getElementById('arx-objects-list');
        if (!arxObjectsList) return;
        
        // Clear existing list
        arxObjectsList.innerHTML = '';
        
        // Get all object types
        const objectTypes = this.arxObjectSystem.objectTypes;
        
        // Group by category
        const categories = {};
        for (const [type, objectType] of objectTypes) {
            if (!categories[objectType.category]) {
                categories[objectType.category] = [];
            }
            categories[objectType.category].push({ type, ...objectType });
        }
        
        // Create UI for each category
        for (const [category, objects] of Object.entries(categories)) {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'mb-4';
            
            const categoryTitle = document.createElement('h4');
            categoryTitle.className = 'text-sm font-semibold text-gray-300 mb-2';
            categoryTitle.textContent = this.capitalizeFirst(category);
            categoryDiv.appendChild(categoryTitle);
            
            // Create object buttons
            for (const object of objects) {
                const objectButton = document.createElement('button');
                objectButton.className = 'w-full text-left p-2 rounded hover:bg-gray-700 text-sm';
                objectButton.textContent = object.name;
                objectButton.dataset.objectType = object.type;
                
                objectButton.addEventListener('click', () => {
                    this.selectArxObjectType(object.type);
                });
                
                categoryDiv.appendChild(objectButton);
            }
            
            arxObjectsList.appendChild(categoryDiv);
        }
    }
    
    /**
     * Set current drawing tool
     */
    setCurrentTool(tool) {
        this.currentTool = tool;
        this.cadEngine.setCurrentTool(tool);
        
        // Update UI state
        this.updateToolUI(tool);
        
        console.log('Current tool set to:', tool);
    }
    
    /**
     * Set precision level
     */
    setPrecision(precision) {
        this.cadEngine.setPrecision(precision);
        console.log('Precision set to:', precision);
    }
    
    /**
     * Update cursor based on current tool
     */
    updateCursor(tool) {
        const canvas = document.getElementById('cad-canvas');
        if (!canvas) return;
        
        const cursors = {
            select: 'default',
            line: 'crosshair',
            rectangle: 'crosshair',
            circle: 'crosshair'
        };
        
        canvas.style.cursor = cursors[tool] || 'default';
    }
    
    /**
     * Update tool UI
     */
    updateToolUI(tool) {
        // Update any tool-specific UI elements
        const toolInfo = document.getElementById('tool-info');
        if (toolInfo) {
            toolInfo.textContent = `Current Tool: ${this.capitalizeFirst(tool)}`;
        }
    }
    
    /**
     * Select ArxObject type for creation
     */
    selectArxObjectType(objectType) {
        // This would switch to object creation mode
        // and set the current ArxObject type
        console.log('Selected ArxObject type:', objectType);
        
        // Update UI to show object creation mode
        this.setCurrentTool('arxobject');
        this.currentArxObjectType = objectType;
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcut(event) {
        switch (event.key) {
            case 'Escape':
                this.cancelCurrentOperation();
                break;
            case 'Delete':
            case 'Backspace':
                this.deleteSelectedObjects();
                break;
            case 's':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.saveProject();
                }
                break;
            case 'e':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.exportDrawing();
                }
                break;
            case 'a':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.selectAllObjects();
                }
                break;
        }
    }
    
    /**
     * Handle window resize
     */
    handleWindowResize() {
        // Resize canvas
        this.cadEngine.resizeCanvas();
        
        // Update UI layout if needed
        this.updateUILayout();
    }
    
    /**
     * Handle selection changes
     */
    handleSelectionChanged(event) {
        this.selectedObjects = event.selectedObjects;
        this.updatePropertiesPanel();
        this.updateSelectionUI();
    }
    
    /**
     * Handle object creation
     */
    handleObjectCreated(event) {
        const arxObject = event.object;
        
        // Add to ArxObject system
        this.arxObjectSystem.arxObjects.set(arxObject.id, arxObject);
        
        // Update UI
        this.updateArxObjectsList();
        this.updateStatistics();
        
        console.log('Object created:', arxObject);
    }
    
    /**
     * Handle object deletion
     */
    handleObjectDeleted(event) {
        const objectId = event.objectId;
        
        // Remove from ArxObject system
        this.arxObjectSystem.deleteArxObject(objectId);
        
        // Update UI
        this.updateArxObjectsList();
        this.updateStatistics();
        
        console.log('Object deleted:', objectId);
    }
    
    /**
     * Update properties panel
     */
    updatePropertiesPanel() {
        const propertiesContent = document.getElementById('properties-content');
        if (!propertiesContent) return;
        
        if (this.selectedObjects.size === 0) {
            propertiesContent.innerHTML = '<div class="text-gray-400 text-sm">Select an object to view properties</div>';
            return;
        }
        
        if (this.selectedObjects.size === 1) {
            // Show properties for single selected object
            const objectId = Array.from(this.selectedObjects)[0];
            const arxObject = this.arxObjectSystem.getArxObject(objectId);
            
            if (arxObject) {
                propertiesContent.innerHTML = this.generateObjectPropertiesHTML(arxObject);
            }
        } else {
            // Show properties for multiple selected objects
            propertiesContent.innerHTML = this.generateMultiSelectionPropertiesHTML();
        }
    }
    
    /**
     * Generate HTML for object properties
     */
    generateObjectPropertiesHTML(arxObject) {
        const objectType = this.arxObjectSystem.objectTypes.get(arxObject.type);
        
        let html = `
            <div class="space-y-3">
                <div class="border-b border-gray-600 pb-2">
                    <h4 class="font-semibold text-white">${objectType ? objectType.name : arxObject.type}</h4>
                    <p class="text-sm text-gray-400">ID: ${arxObject.id}</p>
                </div>
                
                <div>
                    <h5 class="font-medium text-gray-300 mb-2">Properties</h5>
                    <div class="space-y-1">
        `;
        
        // Add properties
        for (const [key, value] of Object.entries(arxObject.properties)) {
            html += `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-400">${this.capitalizeFirst(key)}:</span>
                    <span class="text-white">${value}</span>
                </div>
            `;
        }
        
        html += `
                    </div>
                </div>
                
                <div>
                    <h5 class="font-medium text-gray-300 mb-2">Measurements</h5>
                    <div class="space-y-1">
        `;
        
        // Add measurements
        for (const measurement of arxObject.measurements) {
            html += `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-400">${this.capitalizeFirst(measurement.type)}:</span>
                    <span class="text-white">${measurement.value.toFixed(3)} ${measurement.unit}</span>
                </div>
            `;
        }
        
        html += `
                    </div>
                </div>
                
                <div>
                    <h5 class="font-medium text-gray-300 mb-2">Constraints</h5>
                    <div class="space-y-1">
        `;
        
        // Add constraints
        for (const constraint of arxObject.constraints) {
            html += `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-400">${this.capitalizeFirst(constraint.type)}:</span>
                    <span class="text-white">${constraint.parameters.value || 'N/A'}</span>
                </div>
            `;
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Generate HTML for multi-selection properties
     */
    generateMultiSelectionPropertiesHTML() {
        return `
            <div class="space-y-3">
                <div class="border-b border-gray-600 pb-2">
                    <h4 class="font-semibold text-white">Multiple Selection</h4>
                    <p class="text-sm text-gray-400">${this.selectedObjects.size} objects selected</p>
                </div>
                
                <div>
                    <h5 class="font-medium text-gray-300 mb-2">Actions</h5>
                    <div class="space-y-2">
                        <button class="w-full bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-sm">
                            Delete Selected
                        </button>
                        <button class="w-full bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm">
                            Group Selected
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Update selection UI
     */
    updateSelectionUI() {
        // Update any selection-related UI elements
        const selectionInfo = document.getElementById('selection-info');
        if (selectionInfo) {
            selectionInfo.textContent = `${this.selectedObjects.size} object(s) selected`;
        }
    }
    
    /**
     * Update ArxObjects list
     */
    updateArxObjectsList() {
        // This would update the ArxObjects library panel
        // to reflect current objects in the drawing
    }
    
    /**
     * Update statistics
     */
    updateStatistics() {
        const stats = this.arxObjectSystem.getStatistics();
        
        // Update statistics display
        const statsElement = document.getElementById('drawing-statistics');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="text-sm text-gray-400">
                    Objects: ${stats.totalObjects} | 
                    Relationships: ${stats.totalRelationships} | 
                    Area: ${(stats.totalArea / 144).toFixed(1)} sq ft
                </div>
            `;
        }
    }
    
    /**
     * Open AI assistant
     */
    openAiAssistant() {
        const aiModal = document.getElementById('ai-modal');
        if (aiModal) {
            aiModal.classList.remove('hidden');
        }
    }
    
    /**
     * Close AI assistant
     */
    closeAiAssistant() {
        const aiModal = document.getElementById('ai-modal');
        if (aiModal) {
            aiModal.classList.add('hidden');
        }
    }
    
    /**
     * Send AI message
     */
    sendAiMessage() {
        const aiInput = document.getElementById('ai-input');
        const aiChat = document.getElementById('ai-chat');
        
        if (!aiInput || !aiChat) return;
        
        const message = aiInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage('user', message);
        
        // Clear input
        aiInput.value = '';
        
        // Process with AI assistant
        this.aiAssistant.processMessage(message, this.arxObjectSystem)
            .then(response => {
                this.addChatMessage('assistant', response);
            })
            .catch(error => {
                console.error('AI assistant error:', error);
                this.addChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            });
    }
    
    /**
     * Add message to chat
     */
    addChatMessage(sender, message) {
        const aiChat = document.getElementById('ai-chat');
        if (!aiChat) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-3 p-2 rounded ${sender === 'user' ? 'bg-blue-600 ml-8' : 'bg-gray-700 mr-8'}`;
        messageDiv.textContent = message;
        
        aiChat.appendChild(messageDiv);
        aiChat.scrollTop = aiChat.scrollHeight;
    }
    
    /**
     * Save project
     */
    saveProject() {
        try {
            const projectData = {
                arxObjects: this.arxObjectSystem.exportToJSON(),
                metadata: {
                    saved: Date.now(),
                    version: '1.0.0',
                    name: 'Arxos Project'
                }
            };
            
            // Create download link
            const dataStr = JSON.stringify(projectData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = 'arxos-project.json';
            link.click();
            
            URL.revokeObjectURL(url);
            
            console.log('Project saved successfully');
            
        } catch (error) {
            console.error('Failed to save project:', error);
        }
    }
    
    /**
     * Export drawing
     */
    exportDrawing() {
        try {
            // Export as SVG
            const svgData = this.cadEngine.exportToSVG();
            
            // Create download link
            const dataBlob = new Blob([svgData], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = 'arxos-drawing.svg';
            link.click();
            
            URL.revokeObjectURL(url);
            
            console.log('Drawing exported successfully');
            
        } catch (error) {
            console.error('Failed to export drawing:', error);
        }
    }
    
    /**
     * Cancel current operation
     */
    cancelCurrentOperation() {
        this.cadEngine.cancelDrawing();
        this.setCurrentTool('select');
    }
    
    /**
     * Delete selected objects
     */
    deleteSelectedObjects() {
        for (const objectId of this.selectedObjects) {
            this.arxObjectSystem.deleteArxObject(objectId);
        }
        
        this.selectedObjects.clear();
        this.updatePropertiesPanel();
        this.updateSelectionUI();
        
        console.log('Selected objects deleted');
    }
    
    /**
     * Select all objects
     */
    selectAllObjects() {
        this.selectedObjects.clear();
        
        for (const [id, arxObject] of this.arxObjectSystem.arxObjects) {
            this.selectedObjects.add(id);
        }
        
        this.updatePropertiesPanel();
        this.updateSelectionUI();
        
        console.log('All objects selected');
    }
    
    /**
     * Update UI layout
     */
    updateUILayout() {
        // Update any layout-dependent UI elements
    }
    
    /**
     * Initialize collaboration for current project
     */
    async initializeCollaboration() {
        if (!this.currentProject || !this.collaboration) return;
        
        try {
            const user = await this.apiClient.getCurrentUser();
            await this.collaboration.initializeCollaboration(this.currentProject.id, user.id);
            this.updateCollaborationUI();
            console.log('Collaboration initialized');
        } catch (error) {
            console.error('Failed to initialize collaboration:', error);
        }
    }
    
    /**
     * Initialize AI integration
     */
    async initializeAiIntegration() {
        if (!this.aiIntegration) return;
        
        try {
            await this.aiIntegration.initializeAiIntegration();
            this.updateAiIntegrationUI();
            console.log('AI Integration initialized');
        } catch (error) {
            console.error('Failed to initialize AI integration:', error);
        }
    }
    
    /**
     * Update AI integration UI
     */
    updateAiIntegrationUI() {
        const aiStatus = document.getElementById('ai-status');
        if (!aiStatus || !this.aiIntegration) return;
        
        const stats = this.aiIntegration.getAiStats();
        
        aiStatus.innerHTML = `
            <div class="text-sm">
                <div class="font-semibold">AI Assistant</div>
                <div class="text-gray-400">
                    ${stats.isConnected ? 'Connected' : 'Disconnected'}
                </div>
                <div class="text-gray-500">
                    ${stats.requestCount} requests | ${Math.round(stats.successRate * 100)}% success
                </div>
            </div>
        `;
    }
    
    /**
     * Update collaboration UI
     */
    updateCollaborationUI() {
        const collaborationStatus = document.getElementById('collaboration-status');
        if (!collaborationStatus) return;
        
        const stats = this.collaboration.getCollaborationStats();
        
        collaborationStatus.innerHTML = `
            <div class="text-sm">
                <div class="font-semibold">Collaboration</div>
                <div class="text-gray-400">
                    ${stats.isCollaborating ? 'Active' : 'Inactive'}
                </div>
                <div class="text-gray-500">
                    ${stats.collaborators} collaborators
                </div>
            </div>
        `;
    }
    
    /**
     * Show new project modal
     */
    showNewProjectModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-semibold mb-4">Create New Project</h3>
                <form id="new-project-form">
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2">Project Name</label>
                        <input type="text" id="project-name" required 
                               class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white">
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2">Description</label>
                        <textarea id="project-description" rows="3"
                                  class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"></textarea>
                    </div>
                    <div class="flex space-x-2">
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
                            Create Project
                        </button>
                        <button type="button" id="cancel-new-project" class="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle form submission
        const form = modal.querySelector('#new-project-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('project-name').value;
            const description = document.getElementById('project-description').value;
            
            try {
                await this.createNewProject({ name, description });
                modal.remove();
            } catch (error) {
                this.showNotification('Failed to create project', 'error');
            }
        });
        
        // Handle cancel
        const cancelButton = modal.querySelector('#cancel-new-project');
        cancelButton.addEventListener('click', () => {
            modal.remove();
        });
    }
    
    /**
     * Project Management Methods
     */
    async initializeProjectManagement() {
        try {
            // Get current user
            const user = await this.apiClient.getCurrentUser();
            console.log('Current user:', user);
            
            // Load recent projects
            const projects = await this.apiClient.getProjects({ limit: 5 });
            this.updateProjectList(projects);
            
        } catch (error) {
            console.error('Failed to initialize project management:', error);
        }
    }
    
    async createNewProject(projectData) {
        try {
            const project = await this.apiClient.createProject(projectData);
            this.currentProject = project;
            this.updateProjectUI();
            console.log('Created new project:', project);
            return project;
        } catch (error) {
            console.error('Failed to create project:', error);
            throw error;
        }
    }
    
    async loadProject(projectId) {
        try {
            const project = await this.apiClient.getProject(projectId);
            this.currentProject = project;
            
            // Load CAD data if available
            try {
                const cadData = await this.apiClient.loadCadProject(projectId);
                this.loadCadData(cadData);
            } catch (error) {
                console.log('No existing CAD data found, starting fresh');
            }
            
            this.updateProjectUI();
            console.log('Loaded project:', project);
            return project;
        } catch (error) {
            console.error('Failed to load project:', error);
            throw error;
        }
    }
    
    async saveProject() {
        if (!this.currentProject) {
            throw new Error('No project selected');
        }
        
        try {
            const cadData = {
                arxObjects: Array.from(this.arxObjectSystem.arxObjects.values()),
                relationships: Array.from(this.arxObjectSystem.relationships.values()),
                constraints: Array.from(this.arxObjectSystem.constraints.values()),
                metadata: {
                    saved: Date.now(),
                    version: '1.0.0',
                    objectCount: this.arxObjectSystem.arxObjects.size
                }
            };
            
            await this.apiClient.saveCadProject(this.currentProject.id, cadData);
            console.log('Project saved successfully');
            this.showNotification('Project saved successfully', 'success');
            
        } catch (error) {
            console.error('Failed to save project:', error);
            this.showNotification('Failed to save project', 'error');
            throw error;
        }
    }
    
    async exportToSVGX() {
        if (!this.currentProject) {
            throw new Error('No project selected');
        }
        
        try {
            const cadData = {
                arxObjects: Array.from(this.arxObjectSystem.arxObjects.values()),
                svg: this.cadEngine.exportToSVG()
            };
            
            const svgxData = await this.apiClient.exportCadToSVGX(this.currentProject.id, cadData);
            console.log('Exported to SVGX:', svgxData);
            this.showNotification('Exported to SVGX successfully', 'success');
            return svgxData;
            
        } catch (error) {
            console.error('Failed to export to SVGX:', error);
            this.showNotification('Failed to export to SVGX', 'error');
            throw error;
        }
    }
    
    async importFromSVGX(svgxData) {
        if (!this.currentProject) {
            throw new Error('No project selected');
        }
        
        try {
            const cadData = await this.apiClient.importCadFromSVGX(this.currentProject.id, svgxData);
            this.loadCadData(cadData);
            console.log('Imported from SVGX successfully');
            this.showNotification('Imported from SVGX successfully', 'success');
            
        } catch (error) {
            console.error('Failed to import from SVGX:', error);
            this.showNotification('Failed to import from SVGX', 'error');
            throw error;
        }
    }
    
    loadCadData(cadData) {
        if (cadData.arxObjects) {
            // Clear existing objects
            this.arxObjectSystem.arxObjects.clear();
            
            // Load objects
            for (const arxObject of cadData.arxObjects) {
                this.arxObjectSystem.arxObjects.set(arxObject.id, arxObject);
            }
            
            // Load relationships
            if (cadData.relationships) {
                for (const relationship of cadData.relationships) {
                    this.arxObjectSystem.relationships.set(relationship.id, relationship);
                }
            }
            
            // Load constraints
            if (cadData.constraints) {
                for (const constraint of cadData.constraints) {
                    this.arxObjectSystem.constraints.set(constraint.id, constraint);
                }
            }
            
            // Update CAD engine
            this.cadEngine.arxObjects = this.arxObjectSystem.arxObjects;
            
            console.log('Loaded CAD data:', cadData.arxObjects.length, 'objects');
        }
    }
    
    updateProjectList(projects) {
        const projectList = document.getElementById('project-list');
        if (!projectList) return;
        
        projectList.innerHTML = '';
        
        for (const project of projects) {
            const projectItem = document.createElement('div');
            projectItem.className = 'p-2 hover:bg-gray-700 cursor-pointer rounded';
            projectItem.textContent = project.name;
            projectItem.addEventListener('click', () => {
                this.loadProject(project.id);
            });
            projectList.appendChild(projectItem);
        }
    }
    
    updateProjectUI() {
        const projectInfo = document.getElementById('project-info');
        if (!projectInfo || !this.currentProject) return;
        
        projectInfo.innerHTML = `
            <div class="text-sm">
                <div class="font-semibold">${this.currentProject.name}</div>
                <div class="text-gray-400">${this.currentProject.description || 'No description'}</div>
                <div class="text-gray-500">Objects: ${this.arxObjectSystem.arxObjects.size}</div>
            </div>
        `;
    }
    
    /**
     * Auto-save functionality
     */
    startAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        this.autoSaveInterval = setInterval(() => {
            if (this.autoSaveEnabled && this.currentProject && this.isInitialized) {
                this.saveProject().catch(error => {
                    console.warn('Auto-save failed:', error);
                });
            }
        }, 30000); // Auto-save every 30 seconds
        
        console.log('Auto-save started');
    }
    
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
            console.log('Auto-save stopped');
        }
    }
    
    toggleAutoSave() {
        this.autoSaveEnabled = !this.autoSaveEnabled;
        console.log('Auto-save:', this.autoSaveEnabled ? 'enabled' : 'disabled');
    }
    
    /**
     * Notification system
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600' :
            type === 'error' ? 'bg-red-600' :
            type === 'warning' ? 'bg-yellow-600' : 'bg-blue-600'
        } text-white`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    /**
     * Utility function to capitalize first letter
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Export for global use
window.CadApplication = CadApplication; 