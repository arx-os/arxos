/**
 * Conflict Hunk Viewer - displays a single conflict with resolution options
 */

import { useState } from "react";
import { DiffPanel } from "./DiffPanel";
import type { ConflictHunk, HunkResolution } from "./types";
import { CheckCircle, AlertCircle } from "lucide-react";

interface ConflictHunkViewerProps {
  hunk: ConflictHunk;
  fileNumber: number;
  hunkNumber: number;
  onResolve: (hunkId: string, resolution: HunkResolution) => void;
}

export function ConflictHunkViewer({
  hunk,
  fileNumber,
  hunkNumber,
  onResolve,
}: ConflictHunkViewerProps) {
  const [selectedSide, setSelectedSide] = useState<HunkResolution | null>(
    hunk.resolution
  );

  const handleSelect = (resolution: HunkResolution) => {
    setSelectedSide(resolution);
    onResolve(hunk.id, resolution);
  };

  const isResolved = hunk.resolution !== null;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
      {/* Hunk Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {isResolved ? (
              <CheckCircle className="h-5 w-5 text-emerald-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-amber-500" />
            )}
            <h4 className="text-sm font-semibold text-slate-200">
              Conflict #{fileNumber}.{hunkNumber}
            </h4>
          </div>
          <div className="text-xs text-slate-500">
            Lines {hunk.startLine}-{hunk.endLine}
          </div>
        </div>
        {isResolved && (
          <div className="rounded-md bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-400">
            Resolved: {hunk.resolution}
          </div>
        )}
      </div>

      {/* Three-way diff panels */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        <DiffPanel
          title="Base (Original)"
          side="base"
          lines={hunk.base}
          isSelected={selectedSide === "base"}
          onSelect={() => handleSelect("base")}
        />
        <DiffPanel
          title="Theirs (Server)"
          side="theirs"
          lines={hunk.theirs}
          isSelected={selectedSide === "theirs"}
          onSelect={() => handleSelect("theirs")}
        />
        <DiffPanel
          title="Mine (Offline)"
          side="mine"
          lines={hunk.mine}
          isSelected={selectedSide === "mine"}
          onSelect={() => handleSelect("mine")}
        />
      </div>

      {/* Resolution Options */}
      <div className="grid grid-cols-5 gap-2">
        <button
          onClick={() => handleSelect("base")}
          className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${
            selectedSide === "base"
              ? "border-blue-500 bg-blue-500/20 text-blue-300"
              : "border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500"
          }`}
        >
          Use Base
        </button>
        <button
          onClick={() => handleSelect("theirs")}
          className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${
            selectedSide === "theirs"
              ? "border-purple-500 bg-purple-500/20 text-purple-300"
              : "border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500"
          }`}
        >
          Use Theirs
        </button>
        <button
          onClick={() => handleSelect("mine")}
          className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${
            selectedSide === "mine"
              ? "border-emerald-500 bg-emerald-500/20 text-emerald-300"
              : "border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500"
          }`}
        >
          Use Mine
        </button>
        <button
          onClick={() => handleSelect("both")}
          className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${
            selectedSide === "both"
              ? "border-cyan-500 bg-cyan-500/20 text-cyan-300"
              : "border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500"
          }`}
        >
          Use Both
        </button>
        <button
          onClick={() => handleSelect("neither")}
          className={`rounded-md border px-3 py-2 text-xs font-semibold transition-colors ${
            selectedSide === "neither"
              ? "border-slate-500 bg-slate-500/20 text-slate-300"
              : "border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500"
          }`}
        >
          Use Neither
        </button>
      </div>

      {/* Help Text */}
      {!isResolved && (
        <div className="mt-3 rounded-md bg-blue-500/10 px-3 py-2 text-xs text-blue-300">
          <strong>Tip:</strong> Click a panel or button to select which version
          to keep for this conflict.
        </div>
      )}
    </div>
  );
}
