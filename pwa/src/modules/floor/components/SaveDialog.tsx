/**
 * Save Dialog Component
 *
 * Dialog for saving floor plan changes with validation and Git commit.
 */

import { useState } from "react";
import { Save, X } from "lucide-react";
import { ValidationPanel } from "./ValidationPanel";
import { useSaveStore } from "../state/saveStore";
import { useEditStore } from "../state/editStore";
import { getHistorySummary } from "../edit/history";

export interface SaveDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function SaveDialog({ isOpen, onClose, onSuccess }: SaveDialogProps) {
  const [commitMessage, setCommitMessage] = useState("");
  const {
    isValidating,
    validationResult,
    showValidationPanel,
    isSaving,
    saveError,
    validateChanges,
    saveChanges,
    dismissValidation,
    clearError,
  } = useSaveStore();
  const editStore = useEditStore();

  if (!isOpen) {
    return null;
  }

  const historySummary = getHistorySummary(editStore.history);
  const hasChanges = historySummary.totalOperations > 0;
  const operations = editStore.history.operations.slice(0, editStore.history.currentIndex + 1);

  const handleValidate = async () => {
    if (!hasChanges) {
      return;
    }
    await validateChanges(operations);
  };

  const handleSave = async () => {
    if (!commitMessage.trim() || !hasChanges) {
      return;
    }

    await saveChanges(commitMessage, operations);
    if (!useSaveStore.getState().saveError) {
      setCommitMessage("");
      onSuccess();
      onClose();
    }
  };

  const handleClose = () => {
    setCommitMessage("");
    dismissValidation();
    clearError();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg border border-slate-700 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-700 p-4">
          <div className="flex items-center gap-2">
            <Save className="h-5 w-5 text-slate-400" />
            <h2 className="text-lg font-semibold text-slate-100">Save Changes</h2>
          </div>
          <button
            onClick={handleClose}
            className="rounded p-1 text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-4">
          {/* Summary */}
          <div className="rounded-md border border-slate-700 bg-slate-950 p-3">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Changes Summary
            </div>
            <div className="flex gap-4 text-sm text-slate-300">
              <div>
                <span className="text-slate-400">Total operations:</span>{" "}
                <span className="font-semibold">{historySummary.totalOperations}</span>
              </div>
              <div>
                <span className="text-slate-400">Can undo:</span>{" "}
                <span className="font-semibold">{historySummary.undoCount}</span>
              </div>
            </div>
          </div>

          {/* Commit Message */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-400">
              Commit Message
            </label>
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              placeholder="Describe your changes..."
              rows={3}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-slate-500 focus:outline-none"
            />
          </div>

          {/* Validation Panel */}
          {showValidationPanel && (
            <ValidationPanel
              validation={validationResult}
              isValidating={isValidating}
              onDismiss={dismissValidation}
              onProceed={handleSave}
              onCancel={handleClose}
            />
          )}

          {/* Error */}
          {saveError && (
            <div className="rounded-md border border-red-500/50 bg-red-900/30 p-3 text-sm text-red-200">
              <div className="mb-1 font-semibold">Save Failed</div>
              <div className="text-xs text-red-300">{saveError}</div>
              <button
                onClick={clearError}
                className="mt-2 text-xs font-semibold uppercase tracking-wide text-red-400 hover:text-red-300"
              >
                Dismiss
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        {!showValidationPanel && (
          <div className="flex items-center justify-end gap-2 border-t border-slate-700 p-4">
            <button
              onClick={handleClose}
              className="rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              onClick={handleValidate}
              disabled={!hasChanges || !commitMessage.trim() || isValidating || isSaving}
              className="rounded-md border border-sky-600 bg-sky-700/50 px-4 py-2 text-sm font-semibold uppercase tracking-wide text-sky-100 transition hover:border-sky-500 hover:bg-sky-600/50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isValidating ? "Validating..." : isSaving ? "Saving..." : "Validate & Save"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
