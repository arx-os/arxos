/**
 * Validation Panel Component
 *
 * Displays validation results for edit operations before saving.
 * Shows errors, warnings, and allows users to fix issues or proceed.
 */

import { AlertTriangle, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import type { ValidationResult } from "../../agent/client/types";

export interface ValidationPanelProps {
  validation: ValidationResult | null;
  isValidating: boolean;
  onDismiss: () => void;
  onProceed: () => void;
  onCancel: () => void;
}

export function ValidationPanel({
  validation,
  isValidating,
  onDismiss,
  onProceed,
  onCancel,
}: ValidationPanelProps) {
  if (isValidating) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900/90 p-4 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-sky-500" />
          <span className="text-sm text-slate-300">Validating changes...</span>
        </div>
      </div>
    );
  }

  if (!validation) {
    return null;
  }

  const hasErrors = validation.errors.length > 0;
  const hasWarnings = validation.warnings.length > 0;
  const isValid = validation.valid;

  return (
    <div
      className={`rounded-lg border p-4 shadow-lg ${
        hasErrors
          ? "border-red-500/50 bg-red-900/20"
          : hasWarnings
          ? "border-yellow-500/50 bg-yellow-900/20"
          : "border-emerald-500/50 bg-emerald-900/20"
      }`}
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-2">
          {hasErrors ? (
            <XCircle className="h-5 w-5 text-red-400" />
          ) : hasWarnings ? (
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
          ) : (
            <CheckCircle className="h-5 w-5 text-emerald-400" />
          )}
          <h3 className="text-sm font-semibold text-slate-100">
            {hasErrors
              ? "Validation Failed"
              : hasWarnings
              ? "Validation Warnings"
              : "Validation Passed"}
          </h3>
        </div>
        <button
          onClick={onDismiss}
          className="text-xs text-slate-400 hover:text-slate-100"
        >
          Dismiss
        </button>
      </div>

      {/* Errors */}
      {hasErrors && (
        <div className="mb-3 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-red-300">
            Errors ({validation.errors.length})
          </div>
          <ul className="space-y-1">
            {validation.errors.map((error, index) => (
              <li
                key={index}
                className="flex items-start gap-2 rounded border border-red-500/30 bg-red-900/30 p-2 text-xs text-red-200"
              >
                <AlertCircle className="mt-0.5 h-3 w-3 flex-shrink-0" />
                <div>
                  <div className="font-medium">{error.field}</div>
                  <div className="text-red-300/80">{error.message}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {hasWarnings && (
        <div className="mb-3 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-yellow-300">
            Warnings ({validation.warnings.length})
          </div>
          <ul className="space-y-1">
            {validation.warnings.map((warning, index) => (
              <li
                key={index}
                className="flex items-start gap-2 rounded border border-yellow-500/30 bg-yellow-900/30 p-2 text-xs text-yellow-200"
              >
                <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0" />
                <div>
                  <div className="font-medium">{warning.field}</div>
                  <div className="text-yellow-300/80">{warning.message}</div>
                  {warning.autoFixAvailable && (
                    <button className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-yellow-400 hover:text-yellow-300">
                      Auto-fix available
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Success message */}
      {isValid && !hasWarnings && (
        <div className="mb-3 rounded border border-emerald-500/30 bg-emerald-900/30 p-2 text-xs text-emerald-200">
          All changes are valid and ready to save.
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-2">
        <button
          onClick={onCancel}
          className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
        >
          Cancel
        </button>
        {!hasErrors && (
          <button
            onClick={onProceed}
            className={`rounded-md border px-3 py-1.5 text-xs font-semibold uppercase tracking-wide transition ${
              hasWarnings
                ? "border-yellow-600 bg-yellow-700/50 text-yellow-100 hover:border-yellow-500 hover:bg-yellow-600/50"
                : "border-emerald-600 bg-emerald-700/50 text-emerald-100 hover:border-emerald-500 hover:bg-emerald-600/50"
            }`}
          >
            {hasWarnings ? "Proceed Anyway" : "Save Changes"}
          </button>
        )}
        {hasErrors && (
          <button
            onClick={onCancel}
            className="rounded-md border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-300 transition hover:border-slate-500 hover:bg-slate-600"
          >
            Fix Issues
          </button>
        )}
      </div>
    </div>
  );
}
