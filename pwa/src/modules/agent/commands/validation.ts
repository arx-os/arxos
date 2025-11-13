/**
 * Validation command handlers
 */

import { AgentClient } from "../client/AgentClient";
import type {
  ValidationResult,
  EditOperation,
  ApplyEditsRequest,
  ApplyEditsResult,
} from "../client/types";
import type { Room, Equipment } from "../../../lib/wasm/geometry";

/**
 * Validate a room before saving
 */
export async function validateRoom(room: Room): Promise<ValidationResult> {
  const client = AgentClient.getInstance();
  return client.send<ValidationResult>("validate.room", { room });
}

/**
 * Validate equipment before saving
 */
export async function validateEquipment(equipment: Equipment): Promise<ValidationResult> {
  const client = AgentClient.getInstance();
  return client.send<ValidationResult>("validate.equipment", { equipment });
}

/**
 * Validate a batch of edit operations
 */
export async function validateBatch(
  operations: EditOperation[]
): Promise<ValidationResult[]> {
  const client = AgentClient.getInstance();
  return client.send<ValidationResult[]>("validate.batch", { operations });
}

/**
 * Apply edit operations (with optional validation)
 */
export async function applyEdits(
  request: ApplyEditsRequest,
  onProgress?: (progress: number, message: string) => void
): Promise<ApplyEditsResult> {
  const client = AgentClient.getInstance();

  const requestId = `apply-edits-${Date.now()}`;

  if (onProgress) {
    client.onStream(requestId, (chunk, progress) => {
      onProgress(progress || 0, chunk);
    });
  }

  return client.send<ApplyEditsResult>("edit.apply", {
    ...request,
    requestId,
  });
}
