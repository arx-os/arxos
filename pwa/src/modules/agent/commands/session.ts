/**
 * Session management commands
 *
 * These commands manage Git branches for offline sessions,
 * enabling conflict resolution when syncing offline changes.
 */

import { AgentClient } from "../client/AgentClient";
import type { MergeResult } from "../../../lib/storage/types";

export interface SessionBranchResult {
  sessionId: string;
  branchName: string;
  created: boolean;
  message?: string;
}

export interface DeleteBranchResult {
  deleted: boolean;
  branchName: string;
}

/**
 * Create a new session branch for offline work
 *
 * The agent creates a new Git branch (arxos/session-{sessionId})
 * where all offline commits will be made.
 */
export async function createSessionBranch(
  sessionId: string
): Promise<SessionBranchResult> {
  const client = AgentClient.getInstance();
  return client.send<SessionBranchResult>("git.session.create", { sessionId });
}

/**
 * Merge a session branch back into main
 *
 * Attempts to merge the session branch into the main branch.
 * Returns conflict information if the merge cannot be completed automatically.
 */
export async function mergeSessionBranch(
  sessionId: string,
  strategy?: "ours" | "theirs"
): Promise<MergeResult> {
  const client = AgentClient.getInstance();
  return client.send<MergeResult>("git.session.merge", {
    sessionId,
    strategy,
  });
}

/**
 * Delete a session branch
 *
 * Removes the session branch after successful merge or conflict resolution.
 */
export async function deleteSessionBranch(
  sessionId: string
): Promise<DeleteBranchResult> {
  const client = AgentClient.getInstance();
  return client.send<DeleteBranchResult>("git.session.delete", { sessionId });
}

/**
 * Get information about a session branch
 */
export async function getSessionInfo(sessionId: string): Promise<{
  exists: boolean;
  branchName: string;
  commitCount: number;
  lastCommitMessage?: string;
}> {
  const client = AgentClient.getInstance();
  return client.send("git.session.info", { sessionId });
}

/**
 * List all session branches
 */
export async function listSessionBranches(): Promise<Array<{
  sessionId: string;
  branchName: string;
  created: string;
  commitCount: number;
}>> {
  const client = AgentClient.getInstance();
  return client.send("git.session.list");
}
