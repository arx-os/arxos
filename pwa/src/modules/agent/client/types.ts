/**
 * Agent client types and protocol definitions
 */

// Agent action types (extended from existing lib/agent.ts)
export type AgentAction =
  | "git.status"
  | "git.diff"
  | "git.commit"
  | "git.log"
  | "git.session.create"
  | "git.session.merge"
  | "git.session.delete"
  | "git.session.info"
  | "git.session.list"
  | "files.read"
  | "files.write"
  | "ifc.import"
  | "ifc.export"
  | "validate.room"
  | "validate.equipment"
  | "validate.batch"
  | "edit.apply"
  | "collab.sync"
  | "collab.config.get"
  | "collab.config.set"
  | "ping"
  | "version"
  | "capabilities";

// Message types for WebSocket protocol
export type MessageType = "request" | "response" | "stream" | "error" | "ping" | "pong";

// Agent message envelope
export interface AgentMessage {
  id: string;
  type: MessageType;
  action?: AgentAction;
  payload?: unknown;
  timestamp: number;
}

// Request message
export interface AgentRequest extends AgentMessage {
  type: "request";
  action: AgentAction;
  payload?: unknown;
}

// Response message
export interface AgentResponse<T = unknown> extends AgentMessage {
  type: "response";
  payload: {
    status: "ok" | "error";
    data?: T;
    error?: string;
  };
}

// Stream message for long-running operations
export interface AgentStreamMessage extends AgentMessage {
  type: "stream";
  payload: {
    requestId: string;
    chunk: string;
    progress?: number;
    isLast: boolean;
  };
}

// Error message
export interface AgentErrorMessage extends AgentMessage {
  type: "error";
  payload: {
    error: string;
    details?: string;
  };
}

// Connection state
export type ConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export type ConnectionQuality = "excellent" | "good" | "poor" | "offline";

export interface AgentConnectionState {
  status: ConnectionStatus;
  quality: ConnectionQuality;
  lastConnected?: Date;
  lastError?: string;
  reconnectAttempts: number;
  latency?: number;
}

// Pending request tracking
export interface PendingRequest<T = unknown> {
  id: string;
  action: AgentAction;
  payload?: unknown;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
  timestamp: number;
  timeout?: NodeJS.Timeout;
}

// Stream callback
export type StreamCallback = (chunk: string, progress?: number) => void;

// Request options
export interface RequestOptions {
  timeout?: number;
  onProgress?: (progress: number) => void;
  signal?: AbortSignal;
}

// Agent capabilities
export interface AgentCapabilities {
  version: string;
  supportedActions: AgentAction[];
  features: {
    git: boolean;
    ifc: boolean;
    files: boolean;
    collaboration: boolean;
    validation: boolean;
  };
}

// Git types
export interface GitStatus {
  branch: string;
  ahead: number;
  behind: number;
  modified: string[];
  added: string[];
  deleted: string[];
  untracked: string[];
  clean: boolean;
}

export interface GitCommitOptions {
  message: string;
  files?: string[];
  push?: boolean;
}

export interface GitCommitResult {
  hash: string;
  message: string;
  timestamp: string;
  filesChanged: number;
}

// Validation types
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  field: string;
  message: string;
  severity: "error";
}

export interface ValidationWarning {
  field: string;
  message: string;
  severity: "warning";
  autoFixAvailable?: boolean;
}

// Edit operation types
export interface EditOperation {
  id: string;
  type: "add" | "modify" | "delete";
  target: "room" | "equipment";
  before?: unknown;
  after?: unknown;
  timestamp: Date;
}

export interface ApplyEditsRequest {
  operations: EditOperation[];
  validate: boolean;
}

export interface ApplyEditsResult {
  success: boolean;
  validation?: ValidationResult;
  diff?: string;
  filesChanged: string[];
}
