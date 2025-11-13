/**
 * Floor edit storage operations
 */

import { v4 as uuidv4 } from "uuid";
import { getItem, setItem } from "./db";
import type { PersistedEdit, STORAGE_KEYS } from "./types";
import type { AnyEditOperation } from "../../modules/floor/edit/operations";

const EDITS_KEY: (typeof STORAGE_KEYS)["FLOOR_EDITS"] = "arxos:floor-edits";

/**
 * Get all persisted edits
 */
export async function getPersistedEdits(): Promise<PersistedEdit[]> {
  const edits = await getItem<PersistedEdit[]>(EDITS_KEY);
  return edits || [];
}

/**
 * Persist a floor edit operation
 */
export async function persistEdit(
  operation: AnyEditOperation,
  sessionId: string
): Promise<PersistedEdit> {
  const edits = await getPersistedEdits();

  const edit: PersistedEdit = {
    id: uuidv4(),
    operation,
    timestamp: Date.now(),
    sessionId,
    synced: false,
  };

  edits.push(edit);
  await setItem(EDITS_KEY, edits);

  return edit;
}

/**
 * Mark an edit as synced
 */
export async function markEditSynced(editId: string): Promise<void> {
  const edits = await getPersistedEdits();
  const edit = edits.find((e) => e.id === editId);

  if (edit) {
    edit.synced = true;
    await setItem(EDITS_KEY, edits);
  }
}

/**
 * Get unsynced edits
 */
export async function getUnsyncedEdits(): Promise<PersistedEdit[]> {
  const edits = await getPersistedEdits();
  return edits.filter((edit) => !edit.synced);
}

/**
 * Get edits for a specific session
 */
export async function getSessionEdits(
  sessionId: string
): Promise<PersistedEdit[]> {
  const edits = await getPersistedEdits();
  return edits.filter((edit) => edit.sessionId === sessionId);
}

/**
 * Clear edits for a session
 */
export async function clearSessionEdits(sessionId: string): Promise<void> {
  const edits = await getPersistedEdits();
  const filteredEdits = edits.filter((edit) => edit.sessionId !== sessionId);
  await setItem(EDITS_KEY, filteredEdits);
}

/**
 * Clear all persisted edits
 */
export async function clearAllEdits(): Promise<void> {
  await setItem(EDITS_KEY, []);
}

/**
 * Get unsynced edits count
 */
export async function getUnsyncedCount(): Promise<number> {
  const unsynced = await getUnsyncedEdits();
  return unsynced.length;
}
