/**
 * Collaboration Message Protocol Types
 *
 * Defines the message envelope schema and types for real-time collaboration
 * via agent-relay WebSocket transport.
 */

/**
 * User identity (DID:key from M04)
 */
export type UserDID = string;

/**
 * Message types supported by the protocol
 */
export type MessageType =
  | "chat" // Regular chat message
  | "comment" // Comment attached to building element
  | "ping" // Keepalive ping
  | "pong" // Keepalive response
  | "ack" // Delivery acknowledgment
  | "presence" // Presence update (join/leave/typing)
  | "sync" // Sync request for message history
  | "error"; // Error response

/**
 * Presence states
 */
export type PresenceState =
  | "online"
  | "offline"
  | "away"
  | "typing";

/**
 * Message status for tracking delivery
 */
export type MessageStatus =
  | "pending" // Queued locally, not sent
  | "sent" // Sent to relay
  | "delivered" // Acknowledged by relay
  | "read" // Read by recipient(s)
  | "failed"; // Failed to send

/**
 * Building element reference types
 */
export type ElementType =
  | "building"
  | "floor"
  | "room"
  | "equipment"
  | "wall"
  | "door"
  | "window";

/**
 * Reference to a building element (for context linking)
 */
export interface ElementReference {
  type: ElementType;
  id: string;
  name?: string;
  buildingPath?: string;
  floorId?: string;
}

/**
 * Attachment metadata
 */
export interface Attachment {
  type: "link" | "image" | "file" | "element";
  url?: string;
  name: string;
  mimeType?: string;
  size?: number;
  elementRef?: ElementReference;
}

/**
 * Chat message payload
 */
export interface ChatMessagePayload {
  content: string; // Markdown-formatted message
  mentions?: UserDID[]; // @mentioned users
  attachments?: Attachment[];
  replyTo?: string; // Message ID being replied to
}

/**
 * Comment message payload (attached to building element)
 */
export interface CommentMessagePayload extends ChatMessagePayload {
  elementRef: ElementReference; // Required for comments
  resolved?: boolean; // Thread resolution status
}

/**
 * Presence update payload
 */
export interface PresencePayload {
  state: PresenceState;
  roomId?: string;
  lastSeen?: number;
}

/**
 * Sync request payload
 */
export interface SyncPayload {
  roomId: string;
  since?: number; // Timestamp to sync from (undefined = all history)
  limit?: number; // Max messages to return
}

/**
 * Error payload
 */
export interface ErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

/**
 * Message payload union type
 */
export type MessagePayload =
  | ChatMessagePayload
  | CommentMessagePayload
  | PresencePayload
  | SyncPayload
  | ErrorPayload
  | null; // For ping/pong/ack

/**
 * Core message envelope (wire format)
 */
export interface MessageEnvelope<T extends MessagePayload = MessagePayload> {
  // Protocol version for evolution
  version: string; // e.g., "1.0.0"

  // Message metadata
  id: string; // Unique message ID (UUID)
  type: MessageType;
  timestamp: number; // Unix timestamp (ms)

  // Routing
  from: UserDID; // Sender DID
  to: string; // Room ID or direct user DID
  roomId?: string; // Room context (for chat/comments)

  // Payload
  payload: T;

  // Acknowledgment tracking
  ackId?: string; // ID of message being acknowledged
  requiresAck?: boolean; // Request delivery confirmation
}

/**
 * Room metadata
 */
export interface CollaborationRoom {
  id: string; // Room ID (e.g., "building:floor:room")
  name: string; // Display name
  type: "building" | "floor" | "room" | "direct"; // Room type
  buildingPath?: string;
  floorId?: string;
  roomId?: string;
  members: UserDID[]; // Subscribed users
  createdAt: number;
  lastActivity: number;
  unreadCount?: number;
}

/**
 * User profile
 */
export interface CollaborationUser {
  did: UserDID;
  displayName: string;
  avatar?: string; // Avatar URL or data URI
  presence: PresenceState;
  lastSeen: number;
}

/**
 * Message with local metadata (client-side)
 */
export interface CollaborationMessage {
  envelope: MessageEnvelope;
  status: MessageStatus;
  retryCount?: number;
  error?: string;
  localTimestamp: number; // Client timestamp for ordering
}

/**
 * Connection state
 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

/**
 * Collaboration client configuration
 */
export interface CollaborationConfig {
  agentUrl: string; // WebSocket URL (e.g., "ws://localhost:3030")
  userDID: UserDID; // Current user identity
  authToken?: string; // Optional auth token
  reconnectAttempts?: number; // Max reconnect attempts (default: 5)
  reconnectDelay?: number; // Initial reconnect delay ms (default: 1000)
  pingInterval?: number; // Keepalive ping interval ms (default: 30000)
  autoConnect?: boolean; // Connect on client creation (default: true)
}

/**
 * Collaboration event types
 */
export type CollaborationEventType =
  | "connected"
  | "disconnected"
  | "message"
  | "ack"
  | "presence"
  | "error"
  | "sync";

/**
 * Event payload for CollaborationClient listeners
 */
export interface CollaborationEvent {
  type: CollaborationEventType;
  data?: unknown;
  error?: Error;
}

/**
 * Type guard helpers
 */
export function isChatMessage(
  envelope: MessageEnvelope
): envelope is MessageEnvelope<ChatMessagePayload> {
  return envelope.type === "chat";
}

export function isCommentMessage(
  envelope: MessageEnvelope
): envelope is MessageEnvelope<CommentMessagePayload> {
  return envelope.type === "comment";
}

export function isPresenceUpdate(
  envelope: MessageEnvelope
): envelope is MessageEnvelope<PresencePayload> {
  return envelope.type === "presence";
}

export function isSyncRequest(
  envelope: MessageEnvelope
): envelope is MessageEnvelope<SyncPayload> {
  return envelope.type === "sync";
}

export function isErrorMessage(
  envelope: MessageEnvelope
): envelope is MessageEnvelope<ErrorPayload> {
  return envelope.type === "error";
}

/**
 * Protocol version constant
 */
export const PROTOCOL_VERSION = "1.0.0";

/**
 * Default configuration values
 */
export const DEFAULT_CONFIG: Partial<CollaborationConfig> = {
  reconnectAttempts: 5,
  reconnectDelay: 1000,
  pingInterval: 30000,
  autoConnect: true,
};
