/**
 * Arxos CAD AI Integration System
 * Connects CAD system with GUS Agent for intelligent CAD assistance
 * 
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class CadAiIntegration {
    constructor(cadApplication, apiClient) {
        this.cadApplication = cadApplication;
        this.apiClient = apiClient;
        this.gusAgent = null;
        this.isConnected = false;
        this.conversationHistory = [];
        this.currentContext = null;
        this.aiSuggestions = [];
        this.lastAiResponse = null;
        
        // AI state
        this.isProcessing = false;
        this.processingQueue = [];
        this.confidenceThreshold = 0.7;
        
        // Performance tracking
        this.aiRequestCount = 0;
        this.aiResponseTime = 0;
        this.aiSuccessRate = 0;
        
        // Context management
        this.contextWindow = 10; // Keep last 10 interactions
        this.contextTimeout = 300000; // 5 minutes
        this.lastContextUpdate = Date.now();
        
        console.log('CAD AI Integration system initialized');
    }
    
    /**
     * Initialize AI integration with GUS Agent
     */
    async initializeAiIntegration() {
        try {
            // Initialize GUS Agent connection
            await this.connectToGusAgent();
            
            // Set up AI event listeners
            this.setupAiEventListeners();
            
            // Initialize context
            this.updateContext();
            
            this.isConnected = true;
            console.log('AI Integration initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize AI integration:', error);
            throw error;
        }
    }
    
    /**
     * Connect to GUS Agent
     */
    async connectToGusAgent() {
        try {
            // Test connection to GUS Agent
            const response = await this.apiClient.getHealth();
            
            if (response.status === 'healthy') {
                console.log('GUS Agent connection established');
                return true;
            } else {
                throw new Error('GUS Agent not available');
            }
            
        } catch (error) {
            console.error('Failed to connect to GUS Agent:', error);
            throw error;
        }
    }
    
    /**
     * Process AI command
     */
    async processAiCommand(command, context = null) {
        if (this.isProcessing) {
            this.processingQueue.push({ command, context });
            return { status: 'queued', message: 'Command queued for processing' };
        }
        
        this.isProcessing = true;
        this.aiRequestCount++;
        
        try {
            const startTime = Date.now();
            
            // Update context
            this.updateContext(context);
            
            // Send command to GUS Agent
            const response = await this.apiClient.processAiCommand(
                this.cadApplication.currentProject?.id || 'default',
                command
            );
            
            this.aiResponseTime = Date.now() - startTime;
            
            // Process AI response
            const processedResponse = await this.processAiResponse(response);
            
            // Update conversation history
            this.conversationHistory.push({
                type: 'user',
                command: command,
                timestamp: Date.now()
            });
            
            this.conversationHistory.push({
                type: 'ai',
                response: processedResponse,
                timestamp: Date.now()
            });
            
            // Trim conversation history
            if (this.conversationHistory.length > this.contextWindow * 2) {
                this.conversationHistory = this.conversationHistory.slice(-this.contextWindow * 2);
            }
            
            this.lastAiResponse = processedResponse;
            this.aiSuccessRate = (this.aiSuccessRate * (this.aiRequestCount - 1) + 1) / this.aiRequestCount;
            
            console.log('AI command processed successfully:', command);
            return processedResponse;
            
        } catch (error) {
            console.error('Failed to process AI command:', error);
            this.aiSuccessRate = (this.aiSuccessRate * (this.aiRequestCount - 1)) / this.aiRequestCount;
            
            return {
                status: 'error',
                message: 'Failed to process AI command',
                error: error.message
            };
            
        } finally {
            this.isProcessing = false;
            
            // Process queued commands
            if (this.processingQueue.length > 0) {
                const nextCommand = this.processingQueue.shift();
                setTimeout(() => {
                    this.processAiCommand(nextCommand.command, nextCommand.context);
                }, 100);
            }
        }
    }
    
    /**
     * Process AI response from GUS Agent
     */
    async processAiResponse(response) {
        try {
            const processedResponse = {
                status: 'success',
                message: response.message || 'Command processed successfully',
                confidence: response.confidence || 0.8,
                actions: response.actions || [],
                suggestions: response.suggestions || [],
                context: response.context || {}
            };
            
            // Execute actions if confidence is high enough
            if (processedResponse.confidence >= this.confidenceThreshold) {
                await this.executeAiActions(processedResponse.actions);
            }
            
            // Update AI suggestions
            this.aiSuggestions = processedResponse.suggestions;
            
            return processedResponse;
            
        } catch (error) {
            console.error('Failed to process AI response:', error);
            return {
                status: 'error',
                message: 'Failed to process AI response',
                error: error.message
            };
        }
    }
    
    /**
     * Execute AI actions
     */
    async executeAiActions(actions) {
        for (const action of actions) {
            try {
                await this.executeSingleAction(action);
            } catch (error) {
                console.error('Failed to execute AI action:', action, error);
            }
        }
    }
    
    /**
     * Execute single AI action
     */
    async executeSingleAction(action) {
        switch (action.type) {
            case 'create_object':
                await this.createObjectFromAi(action.data);
                break;
                
            case 'modify_object':
                await this.modifyObjectFromAi(action.data);
                break;
                
            case 'delete_object':
                await this.deleteObjectFromAi(action.data);
                break;
                
            case 'add_constraint':
                await this.addConstraintFromAi(action.data);
                break;
                
            case 'remove_constraint':
                await this.removeConstraintFromAi(action.data);
                break;
                
            case 'set_property':
                await this.setPropertyFromAi(action.data);
                break;
                
            case 'export_format':
                await this.exportToFormatFromAi(action.data);
                break;
                
            case 'import_format':
                await this.importFromFormatFromAi(action.data);
                break;
                
            case 'analyze_design':
                await this.analyzeDesignFromAi(action.data);
                break;
                
            case 'suggest_improvements':
                await this.suggestImprovementsFromAi(action.data);
                break;
                
            default:
                console.warn('Unknown AI action type:', action.type);
        }
    }
    
    /**
     * Create object from AI command
     */
    async createObjectFromAi(data) {
        const { type, properties, position } = data;
        
        try {
            // Create ArxObject
            const arxObject = this.cadApplication.arxObjectSystem.createArxObject(type, properties);
            
            // Set position if provided
            if (position) {
                arxObject.position = position;
            }
            
            // Add to CAD system
            this.cadApplication.arxObjectSystem.arxObjects.set(arxObject.id, arxObject);
            
            // Update CAD engine
            this.cadApplication.cadEngine.arxObjects = this.cadApplication.arxObjectSystem.arxObjects;
            
            console.log('AI created object:', arxObject.id);
            this.cadApplication.showNotification(`AI created ${type} object`, 'success');
            
        } catch (error) {
            console.error('Failed to create object from AI:', error);
            throw error;
        }
    }
    
    /**
     * Modify object from AI command
     */
    async modifyObjectFromAi(data) {
        const { objectId, updates } = data;
        
        try {
            const arxObject = this.cadApplication.arxObjectSystem.arxObjects.get(objectId);
            if (!arxObject) {
                throw new Error(`Object ${objectId} not found`);
            }
            
            // Apply updates
            Object.assign(arxObject, updates);
            
            // Update CAD engine
            this.cadApplication.cadEngine.updateArxObject(objectId, updates);
            
            console.log('AI modified object:', objectId);
            this.cadApplication.showNotification(`AI modified object ${objectId}`, 'success');
            
        } catch (error) {
            console.error('Failed to modify object from AI:', error);
            throw error;
        }
    }
    
    /**
     * Delete object from AI command
     */
    async deleteObjectFromAi(data) {
        const { objectId } = data;
        
        try {
            const arxObject = this.cadApplication.arxObjectSystem.arxObjects.get(objectId);
            if (!arxObject) {
                throw new Error(`Object ${objectId} not found`);
            }
            
            // Remove from CAD system
            this.cadApplication.arxObjectSystem.arxObjects.delete(objectId);
            
            // Update CAD engine
            this.cadApplication.cadEngine.arxObjects = this.cadApplication.arxObjectSystem.arxObjects;
            
            console.log('AI deleted object:', objectId);
            this.cadApplication.showNotification(`AI deleted object ${objectId}`, 'success');
            
        } catch (error) {
            console.error('Failed to delete object from AI:', error);
            throw error;
        }
    }
    
    /**
     * Add constraint from AI command
     */
    async addConstraintFromAi(data) {
        const { type, objects, parameters } = data;
        
        try {
            const constraint = this.cadApplication.arxObjectSystem.createConstraint(type, objects, parameters);
            
            // Add to CAD system
            this.cadApplication.arxObjectSystem.constraints.set(constraint.id, constraint);
            
            console.log('AI added constraint:', constraint.id);
            this.cadApplication.showNotification(`AI added ${type} constraint`, 'success');
            
        } catch (error) {
            console.error('Failed to add constraint from AI:', error);
            throw error;
        }
    }
    
    /**
     * Remove constraint from AI command
     */
    async removeConstraintFromAi(data) {
        const { constraintId } = data;
        
        try {
            const constraint = this.cadApplication.arxObjectSystem.constraints.get(constraintId);
            if (!constraint) {
                throw new Error(`Constraint ${constraintId} not found`);
            }
            
            // Remove from CAD system
            this.cadApplication.arxObjectSystem.constraints.delete(constraintId);
            
            console.log('AI removed constraint:', constraintId);
            this.cadApplication.showNotification(`AI removed constraint ${constraintId}`, 'success');
            
        } catch (error) {
            console.error('Failed to remove constraint from AI:', error);
            throw error;
        }
    }
    
    /**
     * Set property from AI command
     */
    async setPropertyFromAi(data) {
        const { objectId, property, value } = data;
        
        try {
            const arxObject = this.cadApplication.arxObjectSystem.arxObjects.get(objectId);
            if (!arxObject) {
                throw new Error(`Object ${objectId} not found`);
            }
            
            // Set property
            arxObject.properties[property] = value;
            
            // Update CAD engine
            this.cadApplication.cadEngine.updateArxObject(objectId, { properties: arxObject.properties });
            
            console.log('AI set property:', objectId, property, value);
            this.cadApplication.showNotification(`AI set ${property} to ${value}`, 'success');
            
        } catch (error) {
            console.error('Failed to set property from AI:', error);
            throw error;
        }
    }
    
    /**
     * Export to format from AI command
     */
    async exportToFormatFromAi(data) {
        const { format, filename } = data;
        
        try {
            let exportData;
            
            switch (format.toLowerCase()) {
                case 'svgx':
                    exportData = await this.cadApplication.exportToSVGX();
                    break;
                    
                case 'svg':
                    exportData = this.cadApplication.cadEngine.exportToSVG();
                    break;
                    
                case 'json':
                    exportData = JSON.stringify(Array.from(this.cadApplication.arxObjectSystem.arxObjects.values()));
                    break;
                    
                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }
            
            // Trigger download
            this.downloadFile(exportData, filename || `export.${format}`);
            
            console.log('AI exported to format:', format);
            this.cadApplication.showNotification(`AI exported to ${format} format`, 'success');
            
        } catch (error) {
            console.error('Failed to export from AI:', error);
            throw error;
        }
    }
    
    /**
     * Import from format from AI command
     */
    async importFromFormatFromAi(data) {
        const { format, content } = data;
        
        try {
            switch (format.toLowerCase()) {
                case 'svgx':
                    await this.cadApplication.importFromSVGX(content);
                    break;
                    
                case 'json':
                    const objects = JSON.parse(content);
                    for (const object of objects) {
                        this.cadApplication.arxObjectSystem.arxObjects.set(object.id, object);
                    }
                    this.cadApplication.cadEngine.arxObjects = this.cadApplication.arxObjectSystem.arxObjects;
                    break;
                    
                default:
                    throw new Error(`Unsupported import format: ${format}`);
            }
            
            console.log('AI imported from format:', format);
            this.cadApplication.showNotification(`AI imported from ${format} format`, 'success');
            
        } catch (error) {
            console.error('Failed to import from AI:', error);
            throw error;
        }
    }
    
    /**
     * Analyze design from AI command
     */
    async analyzeDesignFromAi(data) {
        try {
            const analysis = {
                objectCount: this.cadApplication.arxObjectSystem.arxObjects.size,
                constraintCount: this.cadApplication.arxObjectSystem.constraints.size,
                relationshipCount: this.cadApplication.arxObjectSystem.relationships.size,
                objectTypes: this.getObjectTypeDistribution(),
                constraints: this.getConstraintTypes(),
                relationships: this.getRelationshipTypes()
            };
            
            console.log('AI design analysis:', analysis);
            this.cadApplication.showNotification('AI completed design analysis', 'success');
            
            return analysis;
            
        } catch (error) {
            console.error('Failed to analyze design from AI:', error);
            throw error;
        }
    }
    
    /**
     * Suggest improvements from AI command
     */
    async suggestImprovementsFromAi(data) {
        try {
            const suggestions = [];
            
            // Analyze current design
            const analysis = await this.analyzeDesignFromAi(data);
            
            // Generate suggestions based on analysis
            if (analysis.objectCount === 0) {
                suggestions.push('Consider adding some basic building elements like walls or rooms');
            }
            
            if (analysis.constraintCount === 0) {
                suggestions.push('Add constraints to ensure proper object relationships');
            }
            
            if (analysis.objectTypes.structural === 0) {
                suggestions.push('Consider adding structural elements for building integrity');
            }
            
            console.log('AI suggestions:', suggestions);
            this.cadApplication.showNotification('AI generated improvement suggestions', 'success');
            
            return suggestions;
            
        } catch (error) {
            console.error('Failed to suggest improvements from AI:', error);
            throw error;
        }
    }
    
    /**
     * Get AI suggestions
     */
    async getAiSuggestions(context = null) {
        try {
            this.updateContext(context);
            
            const response = await this.apiClient.getAiSuggestions(
                this.cadApplication.currentProject?.id || 'default',
                this.currentContext
            );
            
            this.aiSuggestions = response.suggestions || [];
            return this.aiSuggestions;
            
        } catch (error) {
            console.error('Failed to get AI suggestions:', error);
            return [];
        }
    }
    
    /**
     * Update context for AI
     */
    updateContext(additionalContext = null) {
        const now = Date.now();
        
        // Check if context has expired
        if (now - this.lastContextUpdate > this.contextTimeout) {
            this.currentContext = null;
        }
        
        this.currentContext = {
            projectId: this.cadApplication.currentProject?.id,
            objectCount: this.cadApplication.arxObjectSystem.arxObjects.size,
            constraintCount: this.cadApplication.arxObjectSystem.constraints.size,
            selectedObjects: Array.from(this.cadApplication.selectedObjects),
            currentTool: this.cadApplication.currentTool,
            conversationHistory: this.conversationHistory.slice(-this.contextWindow),
            timestamp: now,
            ...additionalContext
        };
        
        this.lastContextUpdate = now;
    }
    
    /**
     * Set up AI event listeners
     */
    setupAiEventListeners() {
        // Listen for CAD engine events
        this.cadApplication.cadEngine.addEventListener('objectCreated', (e) => {
            this.updateContext({ lastAction: 'objectCreated', objectId: e.detail.id });
        });
        
        this.cadApplication.cadEngine.addEventListener('objectUpdated', (e) => {
            this.updateContext({ lastAction: 'objectUpdated', objectId: e.detail.id });
        });
        
        this.cadApplication.cadEngine.addEventListener('objectDeleted', (e) => {
            this.updateContext({ lastAction: 'objectDeleted', objectId: e.detail.id });
        });
    }
    
    /**
     * Get object type distribution
     */
    getObjectTypeDistribution() {
        const distribution = {};
        
        for (const [id, object] of this.cadApplication.arxObjectSystem.arxObjects) {
            const category = object.category || 'unknown';
            distribution[category] = (distribution[category] || 0) + 1;
        }
        
        return distribution;
    }
    
    /**
     * Get constraint types
     */
    getConstraintTypes() {
        const types = {};
        
        for (const [id, constraint] of this.cadApplication.arxObjectSystem.constraints) {
            const type = constraint.type || 'unknown';
            types[type] = (types[type] || 0) + 1;
        }
        
        return types;
    }
    
    /**
     * Get relationship types
     */
    getRelationshipTypes() {
        const types = {};
        
        for (const [id, relationship] of this.cadApplication.arxObjectSystem.relationships) {
            const type = relationship.type || 'unknown';
            types[type] = (types[type] || 0) + 1;
        }
        
        return types;
    }
    
    /**
     * Download file
     */
    downloadFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    /**
     * Get AI statistics
     */
    getAiStats() {
        return {
            isConnected: this.isConnected,
            isProcessing: this.isProcessing,
            requestCount: this.aiRequestCount,
            responseTime: this.aiResponseTime,
            successRate: this.aiSuccessRate,
            conversationHistory: this.conversationHistory.length,
            suggestions: this.aiSuggestions.length,
            contextAge: Date.now() - this.lastContextUpdate
        };
    }
}

// Export for global use
window.CadAiIntegration = CadAiIntegration; 