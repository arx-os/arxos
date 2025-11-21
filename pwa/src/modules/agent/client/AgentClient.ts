/**
 * Persistent WebSocket client for ArxOS desktop agent
 *
 * Manages connection lifecycle, reconnection, request/response handling,
 * and streaming for long-running operations.
 */

import { nanoid } from "nanoid";
import type {
  AgentAction,
  AgentConnectionState,
  AgentMessage,
  AgentRequest,
  AgentResponse,
  AgentStreamMessage,
  ConnectionStatus,
  PendingRequest,
  RequestOptions,
  StreamCallback,
} from "./types";
import {
  ReconnectManager,
  calculateConnectionQuality,
  withTimeout,
} from "./reconnect";

const DEFAULT_ENDPOINT = "ws://127.0.0.1:8787/ws";
const DEFAULT_TIMEOUT = 30000; // 30 seconds
const PING_INTERVAL = 15000; // 15 seconds
const PONG_TIMEOUT = 5000; // 5 seconds

export interface AgentClientConfig {
  endpoint?: string;
  token: string;
  autoReconnect?: boolean;
  debug?: boolean;
}

export class AgentClient {
  private static instance: AgentClient | null = null;

  private config: Required<AgentClientConfig>;
  private ws: WebSocket | null = null;
  private connectionState: AgentConnectionState;
  private pendingRequests = new Map<string, PendingRequest>();
  private streamCallbacks = new Map<string, StreamCallback>();
  private reconnectManager: ReconnectManager;
  private pingInterval?: NodeJS.Timeout;
  private pongTimeout?: NodeJS.Timeout;
  private lastPingTime?: number;
  private listeners = new Set<(state: AgentConnectionState) => void>();

  private constructor(config: AgentClientConfig) {
    this.config = {
      endpoint: config.endpoint || DEFAULT_ENDPOINT,
      token: config.token,
      autoReconnect: config.autoReconnect ?? true,
      debug: config.debug ?? false,
    };

    this.connectionState = {
      status: "disconnected",
      quality: "offline",
      reconnectAttempts: 0,
    };

    this.reconnectManager = new ReconnectManager();
  }

  /**
   * Get or create the singleton instance
   */
  static getInstance(config?: AgentClientConfig): AgentClient {
    if (!AgentClient.instance && !config) {
      throw new Error("AgentClient not initialized. Provide config on first call.");
    }

    if (config) {
      if (AgentClient.instance) {
        // Reconnect with new config
        AgentClient.instance.disconnect();
      }
      AgentClient.instance = new AgentClient(config);
    }

    return AgentClient.instance!;
  }

  /**
   * Reset the singleton instance (mainly for testing)
   */
  static reset(): void {
    if (AgentClient.instance) {
      AgentClient.instance.disconnect();
      AgentClient.instance = null;
    }
  }

  /**
   * Connect to the agent
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      // Wait for connection
      return new Promise((resolve, reject) => {
        const checkConnection = () => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            resolve();
          } else if (
            this.ws?.readyState === WebSocket.CLOSED ||
            this.ws?.readyState === WebSocket.CLOSING
          ) {
            reject(new Error("Connection failed"));
          } else {
            setTimeout(checkConnection, 100);
          }
        };
        checkConnection();
      });
    }

    this.updateConnectionState({ status: "connecting" });

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.config.endpoint}?token=${encodeURIComponent(
          this.config.token
        )}`;
        this.ws = new WebSocket(url);

        this.ws.addEventListener("open", () => {
          this.handleOpen();
          resolve();
        });

        this.ws.addEventListener("message", (event) => {
          this.handleMessage(event);
        });

        this.ws.addEventListener("error", (event) => {
          this.handleError(event);
        });

        this.ws.addEventListener("close", (event) => {
          this.handleClose(event);
        });

        // Timeout connection attempt
        setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error("Connection timeout"));
          }
        }, 10000);
      } catch (error) {
        this.updateConnectionState({
          status: "error",
          lastError:
            error instanceof Error ? error.message : "Connection failed",
        });
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the agent
   */
  disconnect(): void {
    this.stopPingPong();
    this.reconnectManager.cancel();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    // Reject all pending requests
    for (const [id, pending] of this.pendingRequests.entries()) {
      pending.reject(new Error("Client disconnected"));
      this.pendingRequests.delete(id);
    }

    this.updateConnectionState({
      status: "disconnected",
      quality: "offline",
    });
  }

  /**
   * Send a request to the agent
   */
  async send<T = unknown>(
    action: AgentAction,
    payload?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    // Ensure connected
    if (this.ws?.readyState !== WebSocket.OPEN) {
      await this.connect();
    }

    const requestId = nanoid(12);
    const timeout = options.timeout || DEFAULT_TIMEOUT;

    const request: AgentRequest = {
      id: requestId,
      type: "request",
      action,
      payload,
      timestamp: Date.now(),
    };

    // Create promise for response
    const responsePromise = new Promise<T>((resolve, reject) => {
      const timeoutHandle = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`Request timeout: ${action}`));
      }, timeout);

      this.pendingRequests.set(requestId, {
        id: requestId,
        action,
        payload,
        resolve: (value) => {
          clearTimeout(timeoutHandle);
          resolve(value as T);
        },
        reject: (error) => {
          clearTimeout(timeoutHandle);
          reject(error);
        },
        timestamp: Date.now(),
        timeout: timeoutHandle,
      });
    });

    // Send request
    this.ws!.send(JSON.stringify(request));

    if (this.config.debug) {
    }

    return withTimeout(responsePromise, timeout, `Request timeout: ${action}`);
  }

  /**
   * Subscribe to streaming updates for a request
   */
  onStream(requestId: string, callback: StreamCallback): () => void {
    this.streamCallbacks.set(requestId, callback);

    // Return unsubscribe function
    return () => {
      this.streamCallbacks.delete(requestId);
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionStateChange(
    listener: (state: AgentConnectionState) => void
  ): () => void {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get current connection state
   */
  getConnectionState(): AgentConnectionState {
    return { ...this.connectionState };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Private methods

  private handleOpen(): void {
    this.log("Connected to agent");

    this.reconnectManager.reset();
    this.updateConnectionState({
      status: "connected",
      quality: "excellent",
      lastConnected: new Date(),
      reconnectAttempts: 0,
    });

    this.startPingPong();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: AgentMessage = JSON.parse(event.data);

      if (this.config.debug) {
      }

      switch (message.type) {
        case "response":
          this.handleResponse(message as AgentResponse);
          break;

        case "stream":
          this.handleStream(message as AgentStreamMessage);
          break;

        case "error":
          this.handleErrorMessage(message);
          break;

        case "pong":
          this.handlePong();
          break;

        default:
          this.log("Unknown message type:", message.type);
      }
    } catch (error) {
      this.log("Failed to parse message:", error);
    }
  }

  private handleResponse(message: AgentResponse): void {
    const pending = this.pendingRequests.get(message.id);
    if (!pending) {
      this.log("Received response for unknown request:", message.id);
      return;
    }

    this.pendingRequests.delete(message.id);

    if (message.payload.status === "ok") {
      pending.resolve(message.payload.data);
    } else {
      pending.reject(
        new Error(message.payload.error || "Request failed")
      );
    }
  }

  private handleStream(message: AgentStreamMessage): void {
    const callback = this.streamCallbacks.get(message.payload.requestId);
    if (callback) {
      callback(message.payload.chunk, message.payload.progress);

      if (message.payload.isLast) {
        this.streamCallbacks.delete(message.payload.requestId);
      }
    }
  }

  private handleErrorMessage(message: AgentMessage): void {
    const error = (message.payload as { error: string }).error;
    this.log("Agent error:", error);

    // If this is an error for a specific request, reject it
    if (message.id) {
      const pending = this.pendingRequests.get(message.id);
      if (pending) {
        this.pendingRequests.delete(message.id);
        pending.reject(new Error(error));
      }
    }
  }

  private handleError(event: Event): void {
    this.log("WebSocket error:", event);
    this.updateConnectionState({
      status: "error",
      lastError: "WebSocket error occurred",
    });
  }

  private handleClose(event: CloseEvent): void {
    this.log("WebSocket closed:", event.code, event.reason);

    this.stopPingPong();
    this.ws = null;

    this.updateConnectionState({
      status: "disconnected",
      quality: "offline",
    });

    // Attempt reconnect if enabled
    if (this.config.autoReconnect && !this.reconnectManager.isMaxed()) {
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    this.updateConnectionState({
      status: "reconnecting",
      reconnectAttempts: this.reconnectManager.getAttempts() + 1,
    });

    try {
      this.reconnectManager.scheduleReconnect(() => {
        this.log("Attempting reconnect...");
        this.connect().catch((error) => {
          this.log("Reconnect failed:", error);
        });
      });
    } catch (error) {
      this.log("Max reconnect attempts reached");
      this.updateConnectionState({
        status: "error",
        lastError: "Max reconnect attempts reached",
      });
    }
  }

  private startPingPong(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now();

        this.ws.send(
          JSON.stringify({
            id: nanoid(12),
            type: "ping",
            timestamp: Date.now(),
          })
        );

        // Expect pong within PONG_TIMEOUT
        this.pongTimeout = setTimeout(() => {
          this.log("Pong timeout - connection may be dead");
          this.ws?.close();
        }, PONG_TIMEOUT);
      }
    }, PING_INTERVAL);
  }

  private stopPingPong(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = undefined;
    }

    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = undefined;
    }
  }

  private handlePong(): void {
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = undefined;
    }

    if (this.lastPingTime) {
      const latency = Date.now() - this.lastPingTime;
      const quality = calculateConnectionQuality(latency);

      this.updateConnectionState({
        latency,
        quality,
      });
    }
  }

  private updateConnectionState(
    updates: Partial<AgentConnectionState>
  ): void {
    this.connectionState = {
      ...this.connectionState,
      ...updates,
    };

    // Notify listeners
    for (const listener of this.listeners) {
      listener(this.connectionState);
    }
  }

  private log(...args: unknown[]): void {
    if (this.config.debug) {
    }
  }
}
