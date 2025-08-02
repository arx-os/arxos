/**
 * Arxos CAD Real-time Collaboration System
 * Integrates with existing WebSocket infrastructure for multi-user CAD editing
 * 
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class CadCollaboration {
    constructor(cadApplication, apiClient) {
        this.cadApplication = cadApplication;
        this.apiClient = apiClient;
        this.websocket = null;
        this.isConnected = false;
        this.sessionId = null;
        this.userId = null;
        this.collaborators = new Map();
        this.cursorPositions = new Map();
        this.operationQueue = [];
        this.lastOperationId = 0;
        
        // Collaboration state
        this.isCollaborating = false;
        this.currentProjectId = null;
        this.userColor = this.generateUserColor();
        this.userName = 'Anonymous';
        
        // Conflict resolution
        this.pendingOperations = new Map();
        this.resolvedConflicts = new Set();
        
        // Performance tracking
        this.messageCount = 0;
        this.lastMessageTime = 0;
        this.connectionRetries = 0;
        this.maxRetries = 5;
        
        console.log('CAD Collaboration system initialized');
    }
    
    /**
     * Initialize collaboration for a project
     */
    async initializeCollaboration(projectId, userId) {
        try {
            this.currentProjectId = projectId;
            this.userId = userId;
            
            // Join collaboration session
            const session = await this.apiClient.joinCollaboration(projectId, userId);
            this.sessionId = session.session_id;
            
            // Connect WebSocket
            await this.connectWebSocket();
            
            // Set up event listeners
            this.setupEventListeners();
            
            this.isCollaborating = true;
            console.log('Collaboration initialized for project:', projectId);
            
            return session;
            
        } catch (error) {
            console.error('Failed to initialize collaboration:', error);
            throw error;
        }
    }
    
    /**
     * Connect to WebSocket for real-time communication
     */
    async connectWebSocket() {
        const wsUrl = this.getWebSocketUrl();
        
        return new Promise((resolve, reject) => {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.connectionRetries = 0;
                console.log('WebSocket connected for collaboration');
                
                // Send join message
                this.sendMessage({
                    type: 'join',
                    sessionId: this.sessionId,
                    userId: this.userId,
                    userName: this.userName,
                    userColor: this.userColor
                });
                
                resolve();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };
            
            this.websocket.onclose = (event) => {
                this.isConnected = false;
                console.log('WebSocket disconnected:', event.code, event.reason);
                
                if (this.connectionRetries < this.maxRetries) {
                    this.connectionRetries++;
                    setTimeout(() => {
                        this.connectWebSocket();
                    }, 1000 * this.connectionRetries);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
        });
    }
    
    /**
     * Get WebSocket URL based on current location
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/collaboration/${this.sessionId}`;
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            this.messageCount++;
            this.lastMessageTime = Date.now();
            
            switch (message.type) {
                case 'user_joined':
                    this.handleUserJoined(message);
                    break;
                    
                case 'user_left':
                    this.handleUserLeft(message);
                    break;
                    
                case 'cursor_update':
                    this.handleCursorUpdate(message);
                    break;
                    
                case 'object_created':
                    this.handleObjectCreated(message);
                    break;
                    
                case 'object_updated':
                    this.handleObjectUpdated(message);
                    break;
                    
                case 'object_deleted':
                    this.handleObjectDeleted(message);
                    break;
                    
                case 'constraint_added':
                    this.handleConstraintAdded(message);
                    break;
                    
                case 'constraint_removed':
                    this.handleConstraintRemoved(message);
                    break;
                    
                case 'operation_conflict':
                    this.handleOperationConflict(message);
                    break;
                    
                case 'operation_resolved':
                    this.handleOperationResolved(message);
                    break;
                    
                case 'chat_message':
                    this.handleChatMessage(message);
                    break;
                    
                default:
                    console.warn('Unknown message type:', message.type);
            }
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    /**
     * Send message through WebSocket
     */
    sendMessage(message) {
        if (this.websocket && this.isConnected) {
            message.timestamp = Date.now();
            message.userId = this.userId;
            message.sessionId = this.sessionId;
            
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, queuing message');
            this.operationQueue.push(message);
        }
    }
    
    /**
     * Handle user joined event
     */
    handleUserJoined(message) {
        const user = {
            id: message.userId,
            name: message.userName,
            color: message.userColor,
            joinedAt: message.timestamp
        };
        
        this.collaborators.set(user.id, user);
        this.updateCollaboratorsUI();
        
        console.log('User joined:', user.name);
        this.cadApplication.showNotification(`${user.name} joined the session`, 'info');
    }
    
    /**
     * Handle user left event
     */
    handleUserLeft(message) {
        const userId = message.userId;
        const user = this.collaborators.get(userId);
        
        if (user) {
            this.collaborators.delete(userId);
            this.cursorPositions.delete(userId);
            this.updateCollaboratorsUI();
            
            console.log('User left:', user.name);
            this.cadApplication.showNotification(`${user.name} left the session`, 'info');
        }
    }
    
    /**
     * Handle cursor update from other users
     */
    handleCursorUpdate(message) {
        if (message.userId === this.userId) return;
        
        const cursorData = {
            x: message.x,
            y: message.y,
            timestamp: message.timestamp
        };
        
        this.cursorPositions.set(message.userId, cursorData);
        this.updateCursorPositions();
    }
    
    /**
     * Handle object created by other users
     */
    handleObjectCreated(message) {
        if (message.userId === this.userId) return;
        
        try {
            const arxObject = message.object;
            this.cadApplication.arxObjectSystem.arxObjects.set(arxObject.id, arxObject);
            
            // Update CAD engine
            this.cadApplication.cadEngine.arxObjects = this.cadApplication.arxObjectSystem.arxObjects;
            
            console.log('Object created by collaborator:', arxObject.id);
            
        } catch (error) {
            console.error('Failed to handle object creation:', error);
        }
    }
    
    /**
     * Handle object updated by other users
     */
    handleObjectUpdated(message) {
        if (message.userId === this.userId) return;
        
        try {
            const updates = message.updates;
            const objectId = updates.id;
            
            const existingObject = this.cadApplication.arxObjectSystem.arxObjects.get(objectId);
            if (existingObject) {
                // Merge updates
                Object.assign(existingObject, updates);
                
                // Update CAD engine
                this.cadApplication.cadEngine.updateArxObject(objectId, updates);
                
                console.log('Object updated by collaborator:', objectId);
            }
            
        } catch (error) {
            console.error('Failed to handle object update:', error);
        }
    }
    
    /**
     * Handle object deleted by other users
     */
    handleObjectDeleted(message) {
        if (message.userId === this.userId) return;
        
        try {
            const objectId = message.objectId;
            this.cadApplication.arxObjectSystem.arxObjects.delete(objectId);
            
            // Update CAD engine
            this.cadApplication.cadEngine.arxObjects = this.cadApplication.arxObjectSystem.arxObjects;
            
            console.log('Object deleted by collaborator:', objectId);
            
        } catch (error) {
            console.error('Failed to handle object deletion:', error);
        }
    }
    
    /**
     * Handle constraint added by other users
     */
    handleConstraintAdded(message) {
        if (message.userId === this.userId) return;
        
        try {
            const constraint = message.constraint;
            this.cadApplication.arxObjectSystem.constraints.set(constraint.id, constraint);
            
            console.log('Constraint added by collaborator:', constraint.id);
            
        } catch (error) {
            console.error('Failed to handle constraint addition:', error);
        }
    }
    
    /**
     * Handle constraint removed by other users
     */
    handleConstraintRemoved(message) {
        if (message.userId === this.userId) return;
        
        try {
            const constraintId = message.constraintId;
            this.cadApplication.arxObjectSystem.constraints.delete(constraintId);
            
            console.log('Constraint removed by collaborator:', constraintId);
            
        } catch (error) {
            console.error('Failed to handle constraint removal:', error);
        }
    }
    
    /**
     * Handle operation conflict
     */
    handleOperationConflict(message) {
        const conflictId = message.conflictId;
        const conflictingOperation = message.conflictingOperation;
        
        this.pendingOperations.set(conflictId, conflictingOperation);
        
        console.log('Operation conflict detected:', conflictId);
        this.cadApplication.showNotification('Operation conflict detected, resolving...', 'warning');
        
        // Attempt to resolve conflict
        this.resolveConflict(conflictId, conflictingOperation);
    }
    
    /**
     * Handle operation resolved
     */
    handleOperationResolved(message) {
        const conflictId = message.conflictId;
        const resolution = message.resolution;
        
        this.resolvedConflicts.add(conflictId);
        this.pendingOperations.delete(conflictId);
        
        console.log('Operation conflict resolved:', conflictId);
        this.cadApplication.showNotification('Operation conflict resolved', 'success');
    }
    
    /**
     * Handle chat message
     */
    handleChatMessage(message) {
        if (message.userId === this.userId) return;
        
        const chatMessage = {
            user: message.userName,
            message: message.message,
            timestamp: message.timestamp
        };
        
        this.addChatMessage(chatMessage);
    }
    
    /**
     * Set up event listeners for collaboration
     */
    setupEventListeners() {
        // Mouse movement for cursor sharing
        const canvas = this.cadApplication.cadEngine.canvas;
        if (canvas) {
            canvas.addEventListener('mousemove', (e) => {
                this.sendCursorUpdate(e.clientX, e.clientY);
            });
        }
        
        // Listen for CAD engine events
        this.cadApplication.cadEngine.addEventListener('objectCreated', (e) => {
            this.sendObjectCreated(e.detail);
        });
        
        this.cadApplication.cadEngine.addEventListener('objectUpdated', (e) => {
            this.sendObjectUpdated(e.detail);
        });
        
        this.cadApplication.cadEngine.addEventListener('objectDeleted', (e) => {
            this.sendObjectDeleted(e.detail);
        });
    }
    
    /**
     * Send cursor update to other users
     */
    sendCursorUpdate(x, y) {
        this.sendMessage({
            type: 'cursor_update',
            x: x,
            y: y
        });
    }
    
    /**
     * Send object created event
     */
    sendObjectCreated(object) {
        this.sendMessage({
            type: 'object_created',
            object: object
        });
    }
    
    /**
     * Send object updated event
     */
    sendObjectUpdated(updates) {
        this.sendMessage({
            type: 'object_updated',
            updates: updates
        });
    }
    
    /**
     * Send object deleted event
     */
    sendObjectDeleted(objectId) {
        this.sendMessage({
            type: 'object_deleted',
            objectId: objectId
        });
    }
    
    /**
     * Send constraint added event
     */
    sendConstraintAdded(constraint) {
        this.sendMessage({
            type: 'constraint_added',
            constraint: constraint
        });
    }
    
    /**
     * Send constraint removed event
     */
    sendConstraintRemoved(constraintId) {
        this.sendMessage({
            type: 'constraint_removed',
            constraintId: constraintId
        });
    }
    
    /**
     * Send chat message
     */
    sendChatMessage(message) {
        this.sendMessage({
            type: 'chat_message',
            message: message
        });
    }
    
    /**
     * Resolve operation conflict
     */
    resolveConflict(conflictId, conflictingOperation) {
        // Simple conflict resolution: accept the most recent operation
        const currentTime = Date.now();
        const conflictTime = conflictingOperation.timestamp || 0;
        
        if (currentTime > conflictTime) {
            // Accept our operation
            this.sendMessage({
                type: 'operation_resolved',
                conflictId: conflictId,
                resolution: 'accepted_local'
            });
        } else {
            // Accept their operation
            this.sendMessage({
                type: 'operation_resolved',
                conflictId: conflictId,
                resolution: 'accepted_remote'
            });
        }
    }
    
    /**
     * Update collaborators UI
     */
    updateCollaboratorsUI() {
        const collaboratorsList = document.getElementById('collaborators-list');
        if (!collaboratorsList) return;
        
        collaboratorsList.innerHTML = '';
        
        for (const [userId, user] of this.collaborators) {
            const userElement = document.createElement('div');
            userElement.className = 'flex items-center space-x-2 p-2 rounded';
            userElement.style.backgroundColor = user.color + '20';
            
            userElement.innerHTML = `
                <div class="w-3 h-3 rounded-full" style="background-color: ${user.color}"></div>
                <span class="text-sm">${user.name}</span>
            `;
            
            collaboratorsList.appendChild(userElement);
        }
    }
    
    /**
     * Update cursor positions on canvas
     */
    updateCursorPositions() {
        const canvas = this.cadApplication.cadEngine.canvas;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Clear previous cursors
        this.cadApplication.cadEngine.render();
        
        // Draw current cursors
        for (const [userId, cursorData] of this.cursorPositions) {
            const user = this.collaborators.get(userId);
            if (!user) continue;
            
            // Only show cursors from last 5 seconds
            if (Date.now() - cursorData.timestamp > 5000) {
                this.cursorPositions.delete(userId);
                continue;
            }
            
            ctx.save();
            ctx.strokeStyle = user.color;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            
            // Draw crosshair
            ctx.beginPath();
            ctx.moveTo(cursorData.x - 10, cursorData.y);
            ctx.lineTo(cursorData.x + 10, cursorData.y);
            ctx.moveTo(cursorData.x, cursorData.y - 10);
            ctx.lineTo(cursorData.x, cursorData.y + 10);
            ctx.stroke();
            
            // Draw user name
            ctx.fillStyle = user.color;
            ctx.font = '12px Arial';
            ctx.fillText(user.name, cursorData.x + 15, cursorData.y - 5);
            
            ctx.restore();
        }
    }
    
    /**
     * Add chat message to UI
     */
    addChatMessage(chatMessage) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'p-2 border-b border-gray-700';
        messageElement.innerHTML = `
            <div class="flex justify-between">
                <span class="font-semibold">${chatMessage.user}</span>
                <span class="text-gray-500 text-xs">${new Date(chatMessage.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="text-sm mt-1">${chatMessage.message}</div>
        `;
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    /**
     * Generate unique user color
     */
    generateUserColor() {
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    /**
     * Set user name
     */
    setUserName(name) {
        this.userName = name;
        if (this.isConnected) {
            this.sendMessage({
                type: 'user_name_update',
                userName: name
            });
        }
    }
    
    /**
     * Leave collaboration session
     */
    async leaveCollaboration() {
        if (!this.isCollaborating) return;
        
        try {
            // Send leave message
            this.sendMessage({
                type: 'leave',
                sessionId: this.sessionId,
                userId: this.userId
            });
            
            // Close WebSocket
            if (this.websocket) {
                this.websocket.close();
            }
            
            // Leave session via API
            await this.apiClient.leaveCollaboration(this.currentProjectId, this.userId);
            
            // Reset state
            this.isCollaborating = false;
            this.isConnected = false;
            this.currentProjectId = null;
            this.collaborators.clear();
            this.cursorPositions.clear();
            
            console.log('Left collaboration session');
            
        } catch (error) {
            console.error('Failed to leave collaboration:', error);
        }
    }
    
    /**
     * Get collaboration statistics
     */
    getCollaborationStats() {
        return {
            isConnected: this.isConnected,
            isCollaborating: this.isCollaborating,
            collaborators: this.collaborators.size,
            messageCount: this.messageCount,
            lastMessageTime: this.lastMessageTime,
            connectionRetries: this.connectionRetries,
            pendingOperations: this.pendingOperations.size,
            resolvedConflicts: this.resolvedConflicts.size
        };
    }
}

// Export for global use
window.CadCollaboration = CadCollaboration; 