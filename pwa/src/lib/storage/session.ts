/**
 * Session storage operations
 */

import { v4 as uuidv4 } from "uuid";
import { getItem, setItem, deleteItem } from "./db";
import type { Session, STORAGE_KEYS } from "./types";

const SESSION_KEY: (typeof STORAGE_KEYS)["SESSION"] = "arxos:session";

/**
 * Get the current active session
 */
export async function getActiveSession(): Promise<Session | null> {
  const session = await getItem<Session>(SESSION_KEY);
  return session;
}

/**
 * Create a new session
 */
export async function createSession(): Promise<Session> {
  const sessionId = uuidv4();
  const session: Session = {
    id: sessionId,
    branchName: `arxos/session-${sessionId}`,
    createdAt: Date.now(),
    lastSyncAt: null,
    status: "active",
    commandCount: 0,
  };

  await setItem(SESSION_KEY, session);
  return session;
}

/**
 * Update session
 */
export async function updateSession(
  updates: Partial<Session>
): Promise<Session | null> {
  const session = await getActiveSession();
  if (!session) return null;

  const updatedSession = { ...session, ...updates };
  await setItem(SESSION_KEY, updatedSession);
  return updatedSession;
}

/**
 * Increment command count for session
 */
export async function incrementCommandCount(): Promise<void> {
  const session = await getActiveSession();
  if (session) {
    session.commandCount++;
    await setItem(SESSION_KEY, session);
  }
}

/**
 * Mark session as syncing
 */
export async function markSyncing(): Promise<void> {
  await updateSession({ status: "syncing" });
}

/**
 * Mark session as merged
 */
export async function markMerged(): Promise<void> {
  await updateSession({
    status: "merged",
    lastSyncAt: Date.now(),
  });
}

/**
 * Mark session as conflicted
 */
export async function markConflicted(): Promise<void> {
  await updateSession({ status: "conflicted" });
}

/**
 * Clear session (after successful merge)
 */
export async function clearSession(): Promise<void> {
  await deleteItem(SESSION_KEY);
}

/**
 * Check if there's an active session
 */
export async function hasActiveSession(): Promise<boolean> {
  const session = await getActiveSession();
  return session !== null && session.status === "active";
}
