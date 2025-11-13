/**
 * Storage types for offline persistence
 */

import type { AgentAction } from "../../modules/agent/client/types";
import type { AnyEditOperation } from "../../modules/floor/edit/operations";

/**
 * Queued command waiting to be sent to agent
 */
export interface QueuedCommand {
  id: string;
  command: AgentAction;
  payload: unknown;
  timestamp: number;
  retryCount: number;
  status: "pending" | "retrying" | "failed";
  sessionId: string;
}

/**
 * Offline session information
 */
export interface Session {
  id: string; // UUID
  branchName: string; // arxos/session-{uuid}
  createdAt: number;
  lastSyncAt: number | null;
  status: "active" | "syncing" | "merged" | "conflicted";
  commandCount: number;
}

/**
 * Persisted floor edit operation
 */
export interface PersistedEdit {
  id: string;
  operation: AnyEditOperation;
  timestamp: number;
  sessionId: string;
  synced: boolean;
}

/**
 * Git merge conflict
 */
export interface GitConflict {
  filePath: string;
  base: string; // Common ancestor
  theirs: string; // Server version
  mine: string; // Local version
}

/**
 * Conflict resolution strategy
 */
export interface ConflictResolution {
  mode: "accept-mine" | "accept-theirs" | "manual";
  manualResolutions?: Map<string, string>; // filePath -> resolved content
}

/**
 * Merge result from agent
 */
export interface MergeResult {
  success: boolean;
  conflicts?: GitConflict[];
  commitHash?: string;
  message?: string;
}

/**
 * Sync progress information
 */
export interface SyncProgress {
  total: number;
  completed: number;
  failed: number;
  currentCommand?: string;
}

/**
 * Storage keys
 */
export const STORAGE_KEYS = {
  COMMAND_QUEUE: "arxos:command-queue",
  FLOOR_EDITS: "arxos:floor-edits",
  SESSION: "arxos:session",
  SYNC_STATE: "arxos:sync-state",
} as const;
