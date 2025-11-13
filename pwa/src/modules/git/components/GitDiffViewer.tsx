/**
 * Git Diff Viewer
 * Displays file diffs with syntax highlighting
 */

import { useState, useEffect, useMemo } from "react";
import { useGitStore } from "../../../state/git";
import { Loader2, File, AlertCircle, ChevronDown, ChevronRight } from "lucide-react";

interface DiffFile {
  path: string;
  additions: number;
  deletions: number;
  lines: Array<{
    lineNumber: number;
    kind: string;
    content: string;
  }>;
}

export function GitDiffViewer() {
  const { diff, loading, error, loadDiff, clearError } = useGitStore();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadDiff();
  }, [loadDiff]);

  // Group diff lines by file
  const diffFiles = useMemo(() => {
    if (!diff) return [];

    const fileMap = new Map<string, DiffFile>();

    for (const line of diff.files) {
      if (!fileMap.has(line.file_path)) {
        fileMap.set(line.file_path, {
          path: line.file_path,
          additions: 0,
          deletions: 0,
          lines: [],
        });
      }

      const file = fileMap.get(line.file_path)!;
      file.lines.push({
        lineNumber: line.line_number,
        kind: line.kind,
        content: line.content,
      });

      if (line.kind === "addition") file.additions++;
      if (line.kind === "deletion") file.deletions++;
    }

    return Array.from(fileMap.values());
  }, [diff]);

  const toggleFile = (path: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFiles(newExpanded);
  };

  if (loading && !diff) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        <span className="ml-2 text-slate-400">Loading diff...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-400">Error Loading Diff</h3>
            <p className="mt-1 text-sm text-red-300">{error}</p>
          </div>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-300 text-sm"
          >
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  if (!diff || diffFiles.length === 0) {
    return (
      <div className="text-center p-8 text-slate-400">
        <p>No changes to display</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">Changes</h2>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-emerald-400">+{diff.insertions}</span>
          <span className="text-red-400">-{diff.deletions}</span>
          <span className="text-slate-400">{diff.files_changed} files</span>
          <button
            onClick={() => loadDiff()}
            disabled={loading}
            className="rounded-md bg-slate-800 px-3 py-1.5 text-slate-300 hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <span>Refresh</span>
            )}
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="space-y-2">
        {diffFiles.map((file) => {
          const isExpanded = expandedFiles.has(file.path);

          return (
            <div
              key={file.path}
              className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden"
            >
              {/* File Header */}
              <button
                onClick={() => toggleFile(file.path)}
                className="w-full flex items-center gap-3 p-3 hover:bg-slate-800 transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
                )}
                <File className="h-4 w-4 text-blue-400 flex-shrink-0" />
                <span className="flex-1 text-left font-mono text-sm text-slate-200 truncate">
                  {file.path}
                </span>
                <div className="flex items-center gap-3 text-xs">
                  {file.additions > 0 && (
                    <span className="text-emerald-400">+{file.additions}</span>
                  )}
                  {file.deletions > 0 && (
                    <span className="text-red-400">-{file.deletions}</span>
                  )}
                </div>
              </button>

              {/* File Diff */}
              {isExpanded && (
                <div className="border-t border-slate-700">
                  <div className="overflow-x-auto">
                    <table className="w-full font-mono text-xs">
                      <tbody>
                        {file.lines.map((line, idx) => {
                          let bgColor = "";
                          let textColor = "text-slate-300";
                          let prefix = " ";

                          if (line.kind === "addition") {
                            bgColor = "bg-emerald-500/10";
                            textColor = "text-emerald-300";
                            prefix = "+";
                          } else if (line.kind === "deletion") {
                            bgColor = "bg-red-500/10";
                            textColor = "text-red-300";
                            prefix = "-";
                          } else {
                            bgColor = "";
                            textColor = "text-slate-400";
                            prefix = " ";
                          }

                          return (
                            <tr key={idx} className={bgColor}>
                              <td className="w-12 px-2 py-0.5 text-right text-slate-500 select-none border-r border-slate-700">
                                {line.kind !== "deletion" ? line.lineNumber : ""}
                              </td>
                              <td className={`w-8 px-2 py-0.5 text-center ${textColor} select-none border-r border-slate-700`}>
                                {prefix}
                              </td>
                              <td className={`px-2 py-0.5 ${textColor} whitespace-pre`}>
                                {line.content}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
