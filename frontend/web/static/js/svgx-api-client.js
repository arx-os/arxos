/**
 * SVGX Engine API Client
 * 
 * Provides a JavaScript client for connecting Browser CAD and ArxIDE
 * to the SVGX Engine API with real-time collaboration support.
 * 
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class SVGXApiClient {
    constructor(baseUrl = 'http://localhost:8000/api/v1/svgx') {
        this.baseUrl = baseUrl;
        this.websocket = null;
        this.sessionId = null;
        this.clientId = null;
        this.isConnected = false;
        this.eventHandlers = new Map();
        
        // Generate unique client ID
        this.clientId = 'client-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Create a new drawing session
     */
    async createDrawingSession(name, precisionLevel = '0.001', collaborationEnabled = true) {
        try {
            const response = await fetch(`${this.baseUrl}/session/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    precision_level: precisionLevel,
                    collaboration_enabled: collaborationEnabled
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const session = await response.json();
            this.sessionId = session.session_id;
            
            console.log('Created drawing session:', session);
            return session;
            
        } catch (error) {
            console.error('Failed to create drawing session:', error);
            throw error;
        }
    }

    /**
     * Join an existing drawing session
     */
    async joinDrawingSession(sessionId, clientId = this.clientId) {
        try {
            const response = await fetch(`${this.baseUrl}/session/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    client_id: clientId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const session = await response.json();
            this.sessionId = sessionId;
            this.clientId = clientId;
            
            console.log('Joined drawing session:', session);
            return session;
            
        } catch (error) {
            console.error('Failed to join drawing session:', error);
            throw error;
        }
    }

    /**
     * Connect to WebSocket for real-time collaboration
     */
    connectWebSocket(sessionId = this.sessionId, clientId = this.clientId) {
        if (!sessionId || !clientId) {
            throw new Error('Session ID and Client ID are required for WebSocket connection');
        }

        const wsUrl = `ws://localhost:8000/api/v1/svgx/ws/${sessionId}/${clientId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('Connected to SVGX Engine WebSocket');
            this.isConnected = true;
            this.dispatchEvent('connected', { sessionId, clientId });
        };

        this.websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.websocket.onclose = () => {
            console.log('Disconnected from SVGX Engine WebSocket');
            this.isConnected = false;
            this.dispatchEvent('disconnected', { sessionId, clientId });
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnected = false;
            this.dispatchEvent('error', { error, sessionId, clientId });
        };
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(message) {
        console.log('Received WebSocket message:', message);

        switch (message.type) {
            case 'drawing_operation':
                this.dispatchEvent('drawing_operation', message);
                break;
                
            case 'chat_message':
                this.dispatchEvent('chat_message', message);
                break;
                
            case 'cursor_update':
                this.dispatchEvent('cursor_update', message);
                break;
                
            case 'real_time_update':
                this.dispatchEvent('real_time_update', message);
                break;
                
            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    /**
     * Send drawing operation to all clients in session
     */
    sendDrawingOperation(operation) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected');
            return;
        }

        const message = {
            type: 'drawing_operation',
            sessionId: this.sessionId,
            clientId: this.clientId,
            operation: operation
        };

        this.websocket.send(JSON.stringify(message));
    }

    /**
     * Send chat message to all clients in session
     */
    sendChatMessage(text, sender = this.clientId) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected');
            return;
        }

        const message = {
            type: 'chat_message',
            sessionId: this.sessionId,
            clientId: this.clientId,
            sender: sender,
            text: text,
            timestamp: new Date().toISOString()
        };

        this.websocket.send(JSON.stringify(message));
    }

    /**
     * Send cursor position update
     */
    sendCursorUpdate(x, y) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }

        const message = {
            type: 'cursor_update',
            sessionId: this.sessionId,
            clientId: this.clientId,
            position: { x, y },
            timestamp: new Date().toISOString()
        };

        this.websocket.send(JSON.stringify(message));
    }

    /**
     * Send real-time update to API
     */
    async sendRealTimeUpdate(operationType, data) {
        try {
            const response = await fetch(`${this.baseUrl}/session/${this.sessionId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    client_id: this.clientId,
                    operation_type: operationType,
                    data: data
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Real-time update sent:', result);
            return result;
            
        } catch (error) {
            console.error('Failed to send real-time update:', error);
            throw error;
        }
    }

    /**
     * Export drawing session
     */
    async exportDrawingSession(format = 'svgx') {
        try {
            const response = await fetch(`${this.baseUrl}/session/${this.sessionId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    format: format
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Drawing exported:', result);
            return result;
            
        } catch (error) {
            console.error('Failed to export drawing:', error);
            throw error;
        }
    }

    /**
     * Get session information
     */
    async getSessionInfo(sessionId = this.sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/session/${sessionId}/info`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Session info:', result);
            return result;
            
        } catch (error) {
            console.error('Failed to get session info:', error);
            throw error;
        }
    }

    /**
     * Check SVGX Engine health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('SVGX Engine health:', result);
            return result;
            
        } catch (error) {
            console.error('Failed to check SVGX Engine health:', error);
            throw error;
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.sessionId = null;
    }

    /**
     * Add event listener
     */
    addEventListener(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(handler);
    }

    /**
     * Remove event listener
     */
    removeEventListener(eventType, handler) {
        if (this.eventHandlers.has(eventType)) {
            const handlers = this.eventHandlers.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Dispatch event to all listeners
     */
    dispatchEvent(eventType, data) {
        if (this.eventHandlers.has(eventType)) {
            this.eventHandlers.get(eventType).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventType}:`, error);
                }
            });
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            sessionId: this.sessionId,
            clientId: this.clientId,
            websocketReadyState: this.websocket ? this.websocket.readyState : null
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SVGXApiClient;
} else {
    window.SVGXApiClient = SVGXApiClient;
} 