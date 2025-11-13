/**
 * Save/Commit flow state management
 *
 * Manages the process of validating and committing floor plan changes.
 */

import { create } from "zustand";
import { validateBatch } from "../edit/validation";
import type { AnyEditOperation } from "../edit/operations";
import type { ValidationResult } from "../../agent/client/types";
import { applyEdits } from "../../agent/commands/validation";
import { gitCommit } from "../../agent/commands/git";
import { useEditStore } from "./editStore";

interface SaveStore {
  // Validation state
  isValidating: boolean;
  validationResult: ValidationResult | null;
  showValidationPanel: boolean;

  // Save state
  isSaving: boolean;
  saveError: string | null;

  // Actions
  validateChanges: (operations: AnyEditOperation[]) => Promise<void>;
  saveChanges: (message: string, operations: AnyEditOperation[]) => Promise<void>;
  dismissValidation: () => void;
  clearError: () => void;
}

/**
 * Convert our detailed operations to agent EditOperation format
 */
function toAgentEditOperations(operations: AnyEditOperation[]) {
  return operations.map((op) => {
    let type: "add" | "modify" | "delete";
    let target: "room" | "equipment";
    let before: unknown = undefined;
    let after: unknown = undefined;

    if (op.type.startsWith("add-")) {
      type = "add";
    } else if (op.type.startsWith("delete-")) {
      type = "delete";
    } else {
      type = "modify";
    }

    if (op.type.includes("room")) {
      target = "room";
    } else {
      target = "equipment";
    }

    switch (op.type) {
      case "add-room":
        after = op.room;
        break;
      case "delete-room":
        before = op.deletedRoom;
        break;
      case "move-room":
        before = { x: op.fromX, y: op.fromY };
        after = { x: op.toX, y: op.toY };
        break;
      case "resize-room":
        before = { width: op.fromWidth, height: op.fromHeight };
        after = { width: op.toWidth, height: op.toHeight };
        break;
      case "add-equipment":
        after = op.equipment;
        break;
      case "delete-equipment":
        before = op.deletedEquipment;
        break;
      case "move-equipment":
        before = { x: op.fromX, y: op.fromY, z: op.fromZ };
        after = { x: op.toX, y: op.toY, z: op.toZ };
        break;
    }

    return {
      id: op.id,
      type,
      target,
      before,
      after,
      timestamp: new Date(op.timestamp),
    };
  });
}

export const useSaveStore = create<SaveStore>((set, get) => ({
  // Validation state
  isValidating: false,
  validationResult: null,
  showValidationPanel: false,

  // Save state
  isSaving: false,
  saveError: null,

  // Actions
  validateChanges: async (operations) => {
    try {
      set({ isValidating: true, validationResult: null, showValidationPanel: true });

      // First, do client-side validation
      const clientValidation = validateBatch(operations);
      if (!clientValidation.valid) {
        // Convert our validation result format to agent format
        const agentValidation: ValidationResult = {
          valid: false,
          errors: clientValidation.errors.map((msg) => ({
            field: "operation",
            message: msg,
            severity: "error" as const,
          })),
          warnings: clientValidation.warnings.map((msg) => ({
            field: "operation",
            message: msg,
            severity: "warning" as const,
          })),
        };

        set({
          isValidating: false,
          validationResult: agentValidation,
        });
        return;
      }

      // Then, validate with the agent
      const agentOps = toAgentEditOperations(operations);
      const result = await applyEdits({
        operations: agentOps,
        validate: true,
      });

      set({
        isValidating: false,
        validationResult: result.validation || {
          valid: result.success,
          errors: result.success
            ? []
            : [{ field: "operation", message: "Validation failed", severity: "error" as const }],
          warnings: [],
        },
      });
    } catch (error) {
      set({
        isValidating: false,
        validationResult: {
          valid: false,
          errors: [
            {
              field: "validation",
              message: error instanceof Error ? error.message : String(error),
              severity: "error" as const,
            },
          ],
          warnings: [],
        },
      });
    }
  },

  saveChanges: async (message, operations) => {
    try {
      set({ isSaving: true, saveError: null });

      // Apply edits via agent
      const agentOps = toAgentEditOperations(operations);
      const result = await applyEdits({
        operations: agentOps,
        validate: false, // Already validated
      });

      if (!result.success) {
        throw new Error("Failed to apply changes");
      }

      // Commit to Git
      await gitCommit({
        message,
        files: result.filesChanged,
      });

      // Clear edit history and validation panel
      set({
        isSaving: false,
        showValidationPanel: false,
        validationResult: null,
      });

      // Reset edit store
      const editStore = useEditStore.getState();
      editStore.clearSelection();
    } catch (error) {
      set({
        isSaving: false,
        saveError: error instanceof Error ? error.message : String(error),
      });
    }
  },

  dismissValidation: () => set({ showValidationPanel: false }),
  clearError: () => set({ saveError: null }),
}));
