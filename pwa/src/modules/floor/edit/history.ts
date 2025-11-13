/**
 * Edit history with undo/redo support
 *
 * Implements the command pattern for managing edit operations
 * with undo and redo capabilities.
 */

import type { AnyEditOperation } from "./operations";

/**
 * Maximum number of operations to keep in history
 */
const MAX_HISTORY_SIZE = 100;

/**
 * Edit history state
 */
export interface EditHistory {
  operations: AnyEditOperation[];
  currentIndex: number; // Index of the last executed operation
}

/**
 * Create a new edit history
 */
export function createEditHistory(): EditHistory {
  return {
    operations: [],
    currentIndex: -1,
  };
}

/**
 * Add an operation to the history
 *
 * This clears any operations after the current index (for redo)
 * and adds the new operation to the end.
 */
export function addOperation(
  history: EditHistory,
  operation: AnyEditOperation
): EditHistory {
  // Remove all operations after the current index
  const operations = history.operations.slice(0, history.currentIndex + 1);

  // Add the new operation
  operations.push(operation);

  // Limit history size
  const trimmedOperations =
    operations.length > MAX_HISTORY_SIZE
      ? operations.slice(operations.length - MAX_HISTORY_SIZE)
      : operations;

  return {
    operations: trimmedOperations,
    currentIndex: trimmedOperations.length - 1,
  };
}

/**
 * Check if undo is available
 */
export function canUndo(history: EditHistory): boolean {
  return history.currentIndex >= 0;
}

/**
 * Check if redo is available
 */
export function canRedo(history: EditHistory): boolean {
  return history.currentIndex < history.operations.length - 1;
}

/**
 * Get the operation to undo
 */
export function getUndoOperation(
  history: EditHistory
): AnyEditOperation | null {
  if (!canUndo(history)) {
    return null;
  }
  return history.operations[history.currentIndex];
}

/**
 * Get the operation to redo
 */
export function getRedoOperation(
  history: EditHistory
): AnyEditOperation | null {
  if (!canRedo(history)) {
    return null;
  }
  return history.operations[history.currentIndex + 1];
}

/**
 * Move the history pointer backward (undo)
 */
export function undo(history: EditHistory): EditHistory {
  if (!canUndo(history)) {
    return history;
  }

  return {
    ...history,
    currentIndex: history.currentIndex - 1,
  };
}

/**
 * Move the history pointer forward (redo)
 */
export function redo(history: EditHistory): EditHistory {
  if (!canRedo(history)) {
    return history;
  }

  return {
    ...history,
    currentIndex: history.currentIndex + 1,
  };
}

/**
 * Clear all history
 */
export function clearHistory(): EditHistory {
  return createEditHistory();
}

/**
 * Get the inverse operation for undo
 *
 * This creates the opposite operation to reverse an edit.
 */
export function getInverseOperation(
  operation: AnyEditOperation
): AnyEditOperation | null {
  switch (operation.type) {
    case "add-room":
      // Inverse of add is delete
      return {
        id: `inv-${operation.id}`,
        type: "delete-room",
        timestamp: Date.now(),
        floorId: operation.floorId,
        roomId: operation.room.id || "",
      };

    case "delete-room":
      // Inverse of delete is add (if we have the deleted room)
      if (!operation.deletedRoom) {
        return null;
      }
      return {
        id: `inv-${operation.id}`,
        type: "add-room",
        timestamp: Date.now(),
        floorId: operation.floorId,
        room: operation.deletedRoom,
      };

    case "move-room":
      // Inverse of move is move back
      return {
        id: `inv-${operation.id}`,
        type: "move-room",
        timestamp: Date.now(),
        floorId: operation.floorId,
        roomId: operation.roomId,
        fromX: operation.toX,
        fromY: operation.toY,
        toX: operation.fromX,
        toY: operation.fromY,
      };

    case "resize-room":
      // Inverse of resize is resize back
      return {
        id: `inv-${operation.id}`,
        type: "resize-room",
        timestamp: Date.now(),
        floorId: operation.floorId,
        roomId: operation.roomId,
        fromWidth: operation.toWidth,
        fromHeight: operation.toHeight,
        toWidth: operation.fromWidth,
        toHeight: operation.fromHeight,
      };

    case "add-equipment":
      // Inverse of add is delete
      return {
        id: `inv-${operation.id}`,
        type: "delete-equipment",
        timestamp: Date.now(),
        floorId: operation.floorId,
        equipmentId: operation.equipment.id || "",
      };

    case "delete-equipment":
      // Inverse of delete is add (if we have the deleted equipment)
      if (!operation.deletedEquipment) {
        return null;
      }
      return {
        id: `inv-${operation.id}`,
        type: "add-equipment",
        timestamp: Date.now(),
        floorId: operation.floorId,
        equipment: operation.deletedEquipment,
      };

    case "move-equipment":
      // Inverse of move is move back
      return {
        id: `inv-${operation.id}`,
        type: "move-equipment",
        timestamp: Date.now(),
        floorId: operation.floorId,
        equipmentId: operation.equipmentId,
        fromX: operation.toX,
        fromY: operation.toY,
        fromZ: operation.toZ,
        toX: operation.fromX,
        toY: operation.fromY,
        toZ: operation.fromZ,
      };

    default:
      // Wall operations not yet implemented
      return null;
  }
}

/**
 * Get a summary of the history
 */
export function getHistorySummary(history: EditHistory): {
  totalOperations: number;
  undoCount: number;
  redoCount: number;
} {
  return {
    totalOperations: history.operations.length,
    undoCount: history.currentIndex + 1,
    redoCount: history.operations.length - history.currentIndex - 1,
  };
}
