/**
 * Git Status Panel
 * Displays current branch, commit info, and change summary
 */

import { useEffect } from "react";
import { useGitStore } from "../../../state/git";
import { Loader2, GitBranch, GitCommit, FileText, AlertCircle } from "lucide-react";

export function GitStatusPanel() {
  const { status, loading, error, refreshStatus, clearError } = useGitStore();

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        <span className="ml-2 text-slate-400">Loading status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-400">Error Loading Status</h3>
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

  if (!status) {
    return (
      <div className="text-center p-8 text-slate-400">
        <p>No Git repository found</p>
      </div>
    );
  }

  const totalChanges = status.staged_changes + status.unstaged_changes + status.untracked;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">Repository Status</h2>
        <button
          onClick={refreshStatus}
          disabled={loading}
          className="flex items-center gap-2 rounded-md bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <span>Refresh</span>
          )}
        </button>
      </div>

      {/* Branch Info */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
        <div className="flex items-center gap-2 text-slate-200">
          <GitBranch className="h-5 w-5 text-emerald-500" />
          <span className="font-mono font-semibold">{status.branch}</span>
        </div>
      </div>

      {/* Last Commit */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
        <div className="flex items-start gap-3">
          <GitCommit className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="text-sm text-slate-400">Last Commit</div>
            <div className="mt-1 font-mono text-xs text-slate-500">
              {status.last_commit.substring(0, 8)}
            </div>
            <div className="mt-1 text-sm text-slate-200 break-words">
              {status.last_commit_message}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {new Date(status.last_commit_time * 1000).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Changes Summary */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="h-5 w-5 text-amber-500" />
          <span className="font-semibold text-slate-200">Changes</span>
        </div>

        <div className="space-y-2">
          {/* Staged */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Staged</span>
            <span className={`font-semibold ${status.staged_changes > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
              {status.staged_changes}
            </span>
          </div>

          {/* Unstaged */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Unstaged</span>
            <span className={`font-semibold ${status.unstaged_changes > 0 ? 'text-amber-400' : 'text-slate-500'}`}>
              {status.unstaged_changes}
            </span>
          </div>

          {/* Untracked */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Untracked</span>
            <span className={`font-semibold ${status.untracked > 0 ? 'text-blue-400' : 'text-slate-500'}`}>
              {status.untracked}
            </span>
          </div>

          {/* Total */}
          <div className="pt-2 border-t border-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-300">Total Changes</span>
              <span className={`font-bold ${totalChanges > 0 ? 'text-slate-200' : 'text-slate-500'}`}>
                {totalChanges}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Diff Summary */}
      {status.diff_summary && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-sm font-semibold text-slate-300 mb-2">Diff Summary</div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-slate-400">Files</div>
              <div className="mt-1 text-lg font-semibold text-slate-200">
                {status.diff_summary.files_changed}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Insertions</div>
              <div className="mt-1 text-lg font-semibold text-emerald-400">
                +{status.diff_summary.insertions}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Deletions</div>
              <div className="mt-1 text-lg font-semibold text-red-400">
                -{status.diff_summary.deletions}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
