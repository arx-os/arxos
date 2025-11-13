/**
 * Floor plan edit state management
 */

import { create } from "zustand";
import type { EditMode } from "../components/EditToolbar";
import type { AnyEditOperation } from "../edit/operations";
import {
  createEditHistory,
  addOperation,
  canUndo,
  canRedo,
  getUndoOperation,
  getRedoOperation,
  undo as undoHistory,
  redo as redoHistory,
  getInverseOperation,
  type EditHistory,
} from "../edit/history";
import { validateOperation } from "../edit/validation";
import { applyEdits } from "../../agent/commands/validation";
import type { EditOperation } from "../../agent/client/types";

/**
 * Convert our detailed operation to the agent's EditOperation format
 */
function toAgentEditOperation(operation: AnyEditOperation): EditOperation {
  let type: "add" | "modify" | "delete";
  let target: "room" | "equipment";
  let before: unknown = undefined;
  let after: unknown = undefined;

  if (operation.type.startsWith("add-")) {
    type = "add";
  } else if (operation.type.startsWith("delete-")) {
    type = "delete";
  } else {
    type = "modify";
  }

  if (operation.type.includes("room")) {
    target = "room";
  } else {
    target = "equipment";
  }

  // Set before/after based on operation type
  switch (operation.type) {
    case "add-room":
      after = operation.room;
      break;
    case "delete-room":
      before = operation.deletedRoom;
      break;
    case "move-room":
      before = { x: operation.fromX, y: operation.fromY };
      after = { x: operation.toX, y: operation.toY };
      break;
    case "resize-room":
      before = { width: operation.fromWidth, height: operation.fromHeight };
      after = { width: operation.toWidth, height: operation.toHeight };
      break;
    case "add-equipment":
      after = operation.equipment;
      break;
    case "delete-equipment":
      before = operation.deletedEquipment;
      break;
    case "move-equipment":
      before = { x: operation.fromX, y: operation.fromY, z: operation.fromZ };
      after = { x: operation.toX, y: operation.toY, z: operation.toZ };
      break;
  }

  return {
    id: operation.id,
    type,
    target,
    before,
    after,
    timestamp: new Date(operation.timestamp),
  };
}

interface EditStore {
  // Edit mode
  mode: EditMode;
  setMode: (mode: EditMode) => void;

  // Selection
  selectedRoomId: string | null;
  selectedEquipmentId: string | null;
  setSelectedRoom: (roomId: string | null) => void;
  setSelectedEquipment: (equipmentId: string | null) => void;
  clearSelection: () => void;

  // Edit history
  history: EditHistory;
  canUndo: () => boolean;
  canRedo: () => boolean;
  undo: () => Promise<void>;
  redo: () => Promise<void>;

  // Operations
  addOperation: (operation: AnyEditOperation) => Promise<void>;
  applyOperation: (operation: AnyEditOperation) => Promise<void>;

  // State
  isApplying: boolean;
  error: string | null;
  clearError: () => void;
}

export const useEditStore = create<EditStore>((set, get) => ({
  // Edit mode
  mode: "select",
  setMode: (mode) => set({ mode }),

  // Selection
  selectedRoomId: null,
  selectedEquipmentId: null,
  setSelectedRoom: (roomId) =>
    set({ selectedRoomId: roomId, selectedEquipmentId: null }),
  setSelectedEquipment: (equipmentId) =>
    set({ selectedEquipmentId: equipmentId, selectedRoomId: null }),
  clearSelection: () => set({ selectedRoomId: null, selectedEquipmentId: null }),

  // Edit history
  history: createEditHistory(),
  canUndo: () => canUndo(get().history),
  canRedo: () => canRedo(get().history),

  undo: async () => {
    const state = get();
    if (!canUndo(state.history)) {
      return;
    }

    const operation = getUndoOperation(state.history);
    if (!operation) {
      return;
    }

    // Get the inverse operation to undo
    const inverseOp = getInverseOperation(operation);
    if (!inverseOp) {
      set({ error: "Cannot undo this operation" });
      return;
    }

    // Apply the inverse operation
    try {
      set({ isApplying: true, error: null });
      const agentOp = toAgentEditOperation(inverseOp);
      const result = await applyEdits({ operations: [agentOp], validate: false });

      if (!result.success) {
        throw new Error("Undo operation failed");
      }

      set({ history: undoHistory(state.history), isApplying: false });
    } catch (error) {
      set({
        error: `Undo failed: ${error instanceof Error ? error.message : String(error)}`,
        isApplying: false,
      });
    }
  },

  redo: async () => {
    const state = get();
    if (!canRedo(state.history)) {
      return;
    }

    const operation = getRedoOperation(state.history);
    if (!operation) {
      return;
    }

    // Apply the operation again
    try {
      set({ isApplying: true, error: null });
      const agentOp = toAgentEditOperation(operation);
      const result = await applyEdits({ operations: [agentOp], validate: false });

      if (!result.success) {
        throw new Error("Redo operation failed");
      }

      set({ history: redoHistory(state.history), isApplying: false });
    } catch (error) {
      set({
        error: `Redo failed: ${error instanceof Error ? error.message : String(error)}`,
        isApplying: false,
      });
    }
  },

  // Operations
  addOperation: async (operation) => {
    const state = get();

    // Validate the operation
    const validationResult = validateOperation(operation);
    if (!validationResult.valid) {
      set({ error: validationResult.errors.join(", ") });
      return;
    }

    // Apply the operation
    await state.applyOperation(operation);

    // Add to history
    set({ history: addOperation(state.history, operation) });
  },

  applyOperation: async (operation) => {
    try {
      set({ isApplying: true, error: null });

      // Convert to agent format and send to agent for application
      const agentOp = toAgentEditOperation(operation);
      const result = await applyEdits({ operations: [agentOp], validate: true });

      if (!result.success) {
        throw new Error("Operation failed");
      }

      set({ isApplying: false });
    } catch (error) {
      set({
        error: `Operation failed: ${error instanceof Error ? error.message : String(error)}`,
        isApplying: false,
      });
      throw error;
    }
  },

  // State
  isApplying: false,
  error: null,
  clearError: () => set({ error: null }),
}));
