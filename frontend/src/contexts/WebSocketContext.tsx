import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

// Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  user_id?: string;
  session_id?: string;
}

export interface WebSocketEvent {
  event_type: string;
  canvas_id?: string;
  object_id?: string;
  data?: any;
  user_id?: string;
  session_id?: string;
}

export interface WebSocketContextType {
  isConnected: boolean;
  isConnecting: boolean;
  connect: (canvasId: string, sessionId: string) => Promise<void>;
  disconnect: () => void;
  sendMessage: (message: WebSocketEvent) => void;
  subscribe: (eventType: string, callback: (data: any) => void) => () => void;
  lastMessage: WebSocketMessage | null;
  connectionError: string | null;
}

// Create context
const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

// WebSocket Provider Component
export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, apiClient } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // Get WebSocket URL
  const getWebSocketUrl = useCallback((canvasId: string, sessionId: string) => {
    const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const token = localStorage.getItem('access_token');
    return `${baseUrl}/runtime/events?canvas_id=${canvasId}&session_id=${sessionId}&token=${token}`;
  }, []);

  // Handle WebSocket connection
  const connect = useCallback(async (canvasId: string, sessionId: string) => {
    if (isConnected || isConnecting) {
      return;
    }

    try {
      setIsConnecting(true);
      setConnectionError(null);

      const wsUrl = getWebSocketUrl(canvasId, sessionId);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        
        // Send handshake
        ws.send(JSON.stringify({
          event_type: 'handshake',
          canvas_id: canvasId,
          session_id: sessionId,
          user_id: user?.user_id
        }));

        toast.success('Connected to collaboration server');
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle different message types
          switch (message.type) {
            case 'handshake_ack':
              console.log('Handshake acknowledged');
              break;
            
            case 'lock_acquired':
              toast.success('Lock acquired successfully');
              break;
            
            case 'lock_released':
              toast.success('Lock released');
              break;
            
            case 'lock_failed':
              toast.error('Failed to acquire lock');
              break;
            
            case 'conflict_detected':
              toast.error('Conflict detected - please resolve');
              break;
            
            case 'user_joined':
              toast.success(`${message.data.username} joined the session`);
              break;
            
            case 'user_left':
              toast.info(`${message.data.username} left the session`);
              break;
            
            case 'error':
              toast.error(message.data.message || 'WebSocket error');
              break;
            
            default:
              // Notify subscribers
              const subscribers = subscribersRef.current.get(message.type);
              if (subscribers) {
                subscribers.forEach(callback => callback(message.data));
              }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);

        if (event.code !== 1000) { // Not a normal closure
          handleReconnect(canvasId, sessionId);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection failed');
        setIsConnecting(false);
        toast.error('Failed to connect to collaboration server');
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionError('Connection failed');
      setIsConnecting(false);
      toast.error('Failed to connect to collaboration server');
    }
  }, [isConnected, isConnecting, getWebSocketUrl, user]);

  // Handle reconnection
  const handleReconnect = useCallback((canvasId: string, sessionId: string) => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      toast.error('Failed to reconnect after multiple attempts');
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
    reconnectAttemptsRef.current++;

    toast.info(`Reconnecting... (Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect(canvasId, sessionId);
    }, delay);
  }, [connect]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setConnectionError(null);
    reconnectAttemptsRef.current = 0;
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message: WebSocketEvent) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
      toast.error('Not connected to collaboration server');
    }
  }, []);

  // Subscribe to specific event types
  const subscribe = useCallback((eventType: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(eventType)) {
      subscribersRef.current.set(eventType, new Set());
    }
    
    subscribersRef.current.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const subscribers = subscribersRef.current.get(eventType);
      if (subscribers) {
        subscribers.delete(callback);
        if (subscribers.size === 0) {
          subscribersRef.current.delete(eventType);
        }
      }
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const value: WebSocketContextType = {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    lastMessage,
    connectionError,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Custom hook to use WebSocket context
export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Hook for sending specific event types
export const useWebSocketEvent = () => {
  const { sendMessage } = useWebSocket();

  const sendLockRequest = useCallback((canvasId: string, objectId: string) => {
    sendMessage({
      event_type: 'lock_request',
      canvas_id: canvasId,
      object_id: objectId,
    });
  }, [sendMessage]);

  const sendLockRelease = useCallback((canvasId: string, objectId: string) => {
    sendMessage({
      event_type: 'lock_release',
      canvas_id: canvasId,
      object_id: objectId,
    });
  }, [sendMessage]);

  const sendEditOperation = useCallback((canvasId: string, objectId: string, operation: any) => {
    sendMessage({
      event_type: 'edit_operation',
      canvas_id: canvasId,
      object_id: objectId,
      data: operation,
    });
  }, [sendMessage]);

  const sendUserActivity = useCallback((canvasId: string, activity: string) => {
    sendMessage({
      event_type: 'user_activity',
      canvas_id: canvasId,
      data: { activity },
    });
  }, [sendMessage]);

  const sendNavigation = useCallback((canvasId: string, navigation: any) => {
    sendMessage({
      event_type: 'navigation',
      canvas_id: canvasId,
      data: navigation,
    });
  }, [sendMessage]);

  const sendAnnotation = useCallback((canvasId: string, annotation: any) => {
    sendMessage({
      event_type: 'annotation',
      canvas_id: canvasId,
      data: annotation,
    });
  }, [sendMessage]);

  return {
    sendLockRequest,
    sendLockRelease,
    sendEditOperation,
    sendUserActivity,
    sendNavigation,
    sendAnnotation,
  };
}; 