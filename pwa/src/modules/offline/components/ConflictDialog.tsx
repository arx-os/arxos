/**
 * Conflict Resolution Dialog
 *
 * Provides UI for resolving Git conflicts when syncing offline changes.
 */

import { useState } from "react";
import { useSessionStore } from "../state/sessionStore";
import { AlertTriangle, X } from "lucide-react";
import { ThreeWayDiffViewer } from "./diff";

type ResolutionMode = "accept-mine" | "accept-theirs" | "manual";
type ViewMode = "simple" | "diff";

export function ConflictDialog() {
  const { conflicts, syncStatus, resolveConflicts, clearSession } =
    useSessionStore();
  const [resolutionMode, setResolutionMode] =
    useState<ResolutionMode>("accept-mine");
  const [viewMode, setViewMode] = useState<ViewMode>("simple");
  const [isResolving, setIsResolving] = useState(false);

  if (syncStatus !== "conflicted" || !conflicts || conflicts.length === 0) {
    return null;
  }

  const handleResolve = async () => {
    setIsResolving(true);
    try {
      if (resolutionMode === "accept-mine") {
        await resolveConflicts("ours");
      } else if (resolutionMode === "accept-theirs") {
        await resolveConflicts("theirs");
      } else if (resolutionMode === "manual") {
        // Switch to diff viewer
        setViewMode("diff");
        setIsResolving(false);
        return;
      }
    } catch (error) {
      console.error("Resolution failed:", error);
    } finally {
      setIsResolving(false);
    }
  };

  const handleManualResolve = async (resolutions: Map<string, string>) => {
    setIsResolving(true);
    try {
      // Apply manual resolutions using "ours" strategy with custom content
      await resolveConflicts("ours", resolutions);
      setViewMode("simple");
    } catch (error) {
      console.error("Manual resolution failed:", error);
    } finally {
      setIsResolving(false);
    }
  };

  const handleDiscard = async () => {
    if (
      confirm(
        "Are you sure you want to discard all offline changes? This cannot be undone."
      )
    ) {
      await clearSession();
    }
  };

  // Show diff viewer in full screen
  if (viewMode === "diff") {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950">
        <ThreeWayDiffViewer
          conflicts={conflicts}
          onResolve={handleManualResolve}
          onCancel={() => setViewMode("simple")}
        />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-lg border border-amber-500/50 bg-slate-900 p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <AlertTriangle className="h-6 w-6 text-amber-500 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-slate-100">
              Sync Conflicts Detected
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              {conflicts.length} file{conflicts.length > 1 ? "s have" : " has"}{" "}
              conflicts that need resolution.
            </p>
          </div>
        </div>

        {/* Conflict List */}
        <div className="mb-6 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">
            Conflicted Files:
          </h3>
          <ul className="space-y-1">
            {conflicts.map((conflict, index) => (
              <li
                key={index}
                className="text-sm text-slate-400 font-mono truncate"
              >
                {conflict.filePath}
              </li>
            ))}
          </ul>
        </div>

        {/* Resolution Options */}
        <div className="mb-6 space-y-3">
          <label className="flex items-start gap-3 rounded-lg border border-slate-700 p-3 cursor-pointer hover:bg-slate-800/50 transition-colors">
            <input
              type="radio"
              name="resolution"
              value="accept-mine"
              checked={resolutionMode === "accept-mine"}
              onChange={(e) =>
                setResolutionMode(e.target.value as ResolutionMode)
              }
              className="mt-1"
            />
            <div>
              <div className="font-semibold text-slate-200">
                Accept My Changes
              </div>
              <div className="text-sm text-slate-400">
                Keep your offline changes and overwrite server changes
              </div>
            </div>
          </label>

          <label className="flex items-start gap-3 rounded-lg border border-slate-700 p-3 cursor-pointer hover:bg-slate-800/50 transition-colors">
            <input
              type="radio"
              name="resolution"
              value="accept-theirs"
              checked={resolutionMode === "accept-theirs"}
              onChange={(e) =>
                setResolutionMode(e.target.value as ResolutionMode)
              }
              className="mt-1"
            />
            <div>
              <div className="font-semibold text-slate-200">
                Accept Server Changes
              </div>
              <div className="text-sm text-slate-400">
                Discard your offline changes and use server version
              </div>
            </div>
          </label>

          <label className="flex items-start gap-3 rounded-lg border border-slate-700 p-3 cursor-pointer hover:bg-slate-800/50 transition-colors">
            <input
              type="radio"
              name="resolution"
              value="manual"
              checked={resolutionMode === "manual"}
              onChange={(e) =>
                setResolutionMode(e.target.value as ResolutionMode)
              }
              className="mt-1"
            />
            <div>
              <div className="font-semibold text-slate-200">
                Manual Resolution
              </div>
              <div className="text-sm text-slate-400">
                Review and merge changes line-by-line with three-way diff viewer
              </div>
            </div>
          </label>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={handleDiscard}
            disabled={isResolving}
            className="rounded-md border border-red-500/50 bg-red-500/10 px-4 py-2 text-sm font-semibold text-red-400 hover:bg-red-500/20 disabled:opacity-50"
          >
            Discard All Changes
          </button>

          <div className="flex gap-3">
            <button
              onClick={handleResolve}
              disabled={isResolving}
              className="rounded-md bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isResolving
                ? "Resolving..."
                : resolutionMode === "manual"
                ? "Open Diff Viewer"
                : "Resolve Conflicts"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
