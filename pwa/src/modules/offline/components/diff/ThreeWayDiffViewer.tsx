/**
 * Three-Way Diff Viewer - main component for manual conflict resolution
 */

import { useState, useEffect } from "react";
import { ConflictHunkViewer } from "./ConflictHunkViewer";
import { parseGitConflict, calculateDiffStats } from "./parser";
import type { ConflictFile, HunkResolution, DiffStats } from "./types";
import type { GitConflict } from "../../../../lib/storage/types";
import { FileCode, CheckCircle2, AlertTriangle, X } from "lucide-react";

interface ThreeWayDiffViewerProps {
  conflicts: GitConflict[];
  onResolve: (resolutions: Map<string, string>) => void;
  onCancel: () => void;
}

export function ThreeWayDiffViewer({
  conflicts,
  onResolve,
  onCancel,
}: ThreeWayDiffViewerProps) {
  const [files, setFiles] = useState<ConflictFile[]>([]);
  const [stats, setStats] = useState<DiffStats>({
    totalConflicts: 0,
    resolvedConflicts: 0,
    filesWithConflicts: 0,
    linesAdded: 0,
    linesRemoved: 0,
  });
  const [currentFileIndex, setCurrentFileIndex] = useState(0);

  // Parse conflicts into our format
  useEffect(() => {
    const parsed = conflicts.map((conflict) =>
      parseGitConflict(
        conflict.filePath,
        conflict.base,
        conflict.theirs,
        conflict.mine
      )
    );
    setFiles(parsed);
  }, [conflicts]);

  // Update stats whenever files change
  useEffect(() => {
    if (files.length > 0) {
      const newStats = calculateDiffStats(files);
      setStats(newStats);
    }
  }, [files]);

  const handleHunkResolve = (hunkId: string, resolution: HunkResolution) => {
    setFiles((prevFiles) => {
      return prevFiles.map((file) => ({
        ...file,
        hunks: file.hunks.map((hunk) =>
          hunk.id === hunkId ? { ...hunk, resolution } : hunk
        ),
      }));
    });
  };

  const handleApplyResolutions = () => {
    // Build resolution map: filePath -> resolved content
    const resolutions = new Map<string, string>();

    for (const file of files) {
      // For now, we'll use a simple approach: concatenate resolved hunks
      // In production, you'd properly merge the content
      const resolvedContent = file.hunks
        .map((hunk) => {
          if (!hunk.resolution) return "";

          switch (hunk.resolution) {
            case "base":
              return hunk.base.map((l) => l.content).join("\n");
            case "theirs":
              return hunk.theirs.map((l) => l.content).join("\n");
            case "mine":
              return hunk.mine.map((l) => l.content).join("\n");
            case "both":
              return [
                ...hunk.mine.map((l) => l.content),
                ...hunk.theirs.map((l) => l.content),
              ].join("\n");
            case "neither":
              return hunk.base.map((l) => l.content).join("\n");
            default:
              return "";
          }
        })
        .filter(Boolean)
        .join("\n");

      resolutions.set(file.filePath, resolvedContent);
    }

    onResolve(resolutions);
  };

  const currentFile = files[currentFileIndex];
  const allResolved = stats.totalConflicts === stats.resolvedConflicts;
  const canApply = allResolved && stats.totalConflicts > 0;

  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-400">
        Loading conflicts...
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-800/50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              Manual Conflict Resolution
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              Review and resolve each conflict by selecting which version to
              keep
            </p>
          </div>
          <button
            onClick={onCancel}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Stats */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <div className="rounded-lg bg-slate-700/30 px-3 py-2">
            <div className="text-xs text-slate-400">Files</div>
            <div className="mt-1 text-lg font-semibold text-slate-200">
              {stats.filesWithConflicts}
            </div>
          </div>
          <div className="rounded-lg bg-slate-700/30 px-3 py-2">
            <div className="text-xs text-slate-400">Conflicts</div>
            <div className="mt-1 text-lg font-semibold text-slate-200">
              {stats.totalConflicts}
            </div>
          </div>
          <div className="rounded-lg bg-emerald-500/10 px-3 py-2">
            <div className="text-xs text-emerald-400">Resolved</div>
            <div className="mt-1 text-lg font-semibold text-emerald-300">
              {stats.resolvedConflicts}
            </div>
          </div>
          <div className="rounded-lg bg-blue-500/10 px-3 py-2">
            <div className="text-xs text-blue-400">Progress</div>
            <div className="mt-1 text-lg font-semibold text-blue-300">
              {stats.totalConflicts > 0
                ? Math.round(
                    (stats.resolvedConflicts / stats.totalConflicts) * 100
                  )
                : 0}
              %
            </div>
          </div>
        </div>
      </div>

      {/* File Navigation */}
      {files.length > 1 && (
        <div className="border-b border-slate-700 bg-slate-800/30 px-6 py-3">
          <div className="flex items-center gap-2">
            {files.map((file, index) => {
              const fileResolved = file.hunks.every(
                (h) => h.resolution !== null
              );
              return (
                <button
                  key={file.filePath}
                  onClick={() => setCurrentFileIndex(index)}
                  className={`flex items-center gap-2 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                    index === currentFileIndex
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500"
                      : fileResolved
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:border-emerald-500/50"
                      : "bg-slate-700/30 text-slate-300 border border-slate-600 hover:border-slate-500"
                  }`}
                >
                  {fileResolved ? (
                    <CheckCircle2 className="h-3 w-3" />
                  ) : (
                    <AlertTriangle className="h-3 w-3" />
                  )}
                  {file.filePath.split("/").pop()}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Current File */}
      {currentFile && (
        <div className="flex-1 overflow-auto bg-slate-900/30 px-6 py-4">
          {/* File Header */}
          <div className="mb-4 flex items-center gap-3 rounded-lg bg-slate-800/50 px-4 py-3">
            <FileCode className="h-5 w-5 text-slate-400" />
            <div className="flex-1">
              <div className="font-mono text-sm text-slate-200">
                {currentFile.filePath}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {currentFile.hunks.length} conflict
                {currentFile.hunks.length !== 1 ? "s" : ""} in this file
              </div>
            </div>
          </div>

          {/* Conflict Hunks */}
          <div className="space-y-4">
            {currentFile.hunks.map((hunk, index) => (
              <ConflictHunkViewer
                key={hunk.id}
                hunk={hunk}
                fileNumber={currentFileIndex + 1}
                hunkNumber={index + 1}
                onResolve={handleHunkResolve}
              />
            ))}
          </div>
        </div>
      )}

      {/* Footer Actions */}
      <div className="border-t border-slate-700 bg-slate-800/50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {allResolved ? (
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="h-5 w-5" />
                <span className="text-sm font-semibold">
                  All conflicts resolved!
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle className="h-5 w-5" />
                <span className="text-sm font-semibold">
                  {stats.totalConflicts - stats.resolvedConflicts} conflict
                  {stats.totalConflicts - stats.resolvedConflicts !== 1
                    ? "s"
                    : ""}{" "}
                  remaining
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="rounded-md border border-slate-600 bg-slate-700/30 px-4 py-2 text-sm font-semibold text-slate-300 hover:border-slate-500 hover:bg-slate-700/50"
            >
              Cancel
            </button>
            <button
              onClick={handleApplyResolutions}
              disabled={!canApply}
              className={`rounded-md px-6 py-2 text-sm font-semibold transition-colors ${
                canApply
                  ? "bg-emerald-600 text-white hover:bg-emerald-700"
                  : "bg-slate-700 text-slate-500 cursor-not-allowed"
              }`}
            >
              Apply Resolutions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
