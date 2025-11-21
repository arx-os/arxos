/**
 * Collaboration Client
 *
 * WebSocket client for real-time collaboration via agent-relay.
 * Handles connection management, message sending/receiving, and reconnection logic.
 */

import { v4 as uuidv4 } from "uuid";
import {
  PROTOCOL_VERSION,
  DEFAULT_CONFIG,
} from "./types";
import type {
  CollaborationConfig,
  CollaborationEvent,
  CollaborationEventType,
  ConnectionState,
  MessageEnvelope,
  MessagePayload,
  MessageType,
} from "./types";

type EventListener = (event: CollaborationEvent) => void;

export class CollaborationClient {
  private config: Required<CollaborationConfig>;
  private ws: WebSocket | null = null;
  private connectionState: ConnectionState = "disconnected";
  private listeners: Map<CollaborationEventType, Set<EventListener>> =
    new Map();
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pendingAcks: Map<
    string,
    { resolve: () => void; reject: (error: Error) => void }
  > = new Map();
  private ackTimeout = 10000; // 10s timeout for acks

  constructor(config: CollaborationConfig) {
    // Merge with defaults
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
    } as Required<CollaborationConfig>;

    if (this.config.autoConnect) {
      this.connect();
    }
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Connect to agent-relay
   */
  public async connect(): Promise<void> {
    if (this.connectionState === "connected" || this.connectionState === "connecting") {
      return;
    }

    this.setConnectionState("connecting");

    try {
      this.ws = new WebSocket(this.config.agentUrl);

      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onerror = (event) => this.handleError(event);
      this.ws.onclose = (event) => this.handleClose(event);
    } catch (error) {
      this.setConnectionState("error");
      this.emit("error", { error: error as Error });
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from agent-relay
   */
  public disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.setConnectionState("disconnected");
  }

  /**
   * Send a message
   */
  public async send<T extends MessagePayload>(
    type: MessageType,
    to: string,
    payload: T,
    options?: {
      roomId?: string;
      requiresAck?: boolean;
      ackId?: string;
    }
  ): Promise<void> {
    if (this.connectionState !== "connected") {
      throw new Error("Not connected to agent-relay");
    }

    const envelope: MessageEnvelope<T> = {
      version: PROTOCOL_VERSION,
      id: uuidv4(),
      type,
      timestamp: Date.now(),
      from: this.config.userDID,
      to,
      payload,
      ...options,
    };

    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("WebSocket not ready"));
        return;
      }

      try {
        this.ws.send(JSON.stringify(envelope));

        if (options?.requiresAck) {
          // Wait for acknowledgment
          this.pendingAcks.set(envelope.id, { resolve, reject });

          // Set timeout
          setTimeout(() => {
            if (this.pendingAcks.has(envelope.id)) {
              this.pendingAcks.delete(envelope.id);
              reject(new Error("Acknowledgment timeout"));
            }
          }, this.ackTimeout);
        } else {
          resolve();
        }
      } catch (error) {
        reject(error as Error);
      }
    });
  }

  /**
   * Subscribe to a room
   */
  public async subscribe(roomId: string): Promise<void> {
    await this.send("sync", roomId, {
      roomId,
      limit: 100, // Get last 100 messages
    });
  }

  /**
   * Unsubscribe from a room
   */
  public async unsubscribe(roomId: string): Promise<void> {
    // Send leave presence update
    await this.send(
      "presence",
      roomId,
      {
        state: "offline",
        roomId,
      },
      { roomId }
    );
  }

  /**
   * Send a ping keepalive
   */
  private sendPing(): void {
    if (this.connectionState === "connected") {
      this.send("ping", "relay", null).catch((error) => {
        console.error("Ping failed:", error);
      });
    }
  }

  /**
   * Add event listener
   */
  public on(event: CollaborationEventType, listener: EventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
  }

  /**
   * Remove event listener
   */
  public off(event: CollaborationEventType, listener: EventListener): void {
    this.listeners.get(event)?.delete(listener);
  }

  /**
   * Emit event to listeners
   */
  private emit(
    type: CollaborationEventType,
    data?: { data?: unknown; error?: Error }
  ): void {
    const event: CollaborationEvent = {
      type,
      ...data,
    };

    this.listeners.get(type)?.forEach((listener) => listener(event));
  }

  /**
   * Handle WebSocket open
   */
  private handleOpen(): void {
    this.setConnectionState("connected");
    this.reconnectAttempt = 0;
    this.emit("connected");

    // Start keepalive ping
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
    }
    this.pingTimer = setInterval(
      () => this.sendPing(),
      this.config.pingInterval
    );
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const envelope: MessageEnvelope = JSON.parse(event.data);

      // Handle acknowledgments
      if (envelope.type === "ack" && envelope.ackId) {
        const pending = this.pendingAcks.get(envelope.ackId);
        if (pending) {
          pending.resolve();
          this.pendingAcks.delete(envelope.ackId);
        }
        this.emit("ack", { data: envelope });
        return;
      }

      // Handle pong
      if (envelope.type === "pong") {
        // Keepalive response, no action needed
        return;
      }

      // Emit message event
      this.emit("message", { data: envelope });

      // Send ack if required
      if (envelope.requiresAck) {
        this.send("ack", envelope.from, null, { ackId: envelope.id }).catch(
          (error) => {
            console.error("Failed to send ack:", error);
          }
        );
      }

      // Emit specific event types
      if (envelope.type === "presence") {
        this.emit("presence", { data: envelope });
      } else if (envelope.type === "sync") {
        this.emit("sync", { data: envelope });
      } else if (envelope.type === "error") {
        this.emit("error", { data: envelope });
      }
    } catch (error) {
      console.error("Failed to parse message:", error);
      this.emit("error", { error: error as Error });
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(event: Event): void {
    console.error("WebSocket error:", event);
    this.setConnectionState("error");
    this.emit("error", { error: new Error("WebSocket error") });
  }

  /**
   * Handle WebSocket close
   */
  private handleClose(event: CloseEvent): void {

    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }

    this.setConnectionState("disconnected");
    this.emit("disconnected");

    // Attempt reconnect if not a clean close
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempt >= this.config.reconnectAttempts) {
      console.error("Max reconnect attempts reached");
      this.setConnectionState("error");
      return;
    }

    this.setConnectionState("reconnecting");
    this.reconnectAttempt++;

    // Exponential backoff
    const delay =
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempt - 1);

      `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt}/${this.config.reconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Update connection state and emit event
   */
  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
    }
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    this.disconnect();
    this.listeners.clear();
    this.pendingAcks.clear();
  }
}
