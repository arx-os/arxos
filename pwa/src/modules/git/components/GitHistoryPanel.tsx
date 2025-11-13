/**
 * Git History Panel
 * Displays commit history with pagination
 */

import { useState, useEffect } from "react";
import { gitLog } from "../../agent/commands/git";
import { Loader2, GitCommit, User, Clock, AlertCircle, ChevronLeft, ChevronRight } from "lucide-react";

interface GitLogEntry {
  hash: string;
  message: string;
  author: string;
  timestamp: string;
}

const COMMITS_PER_PAGE = 20;

export function GitHistoryPanel() {
  const [commits, setCommits] = useState<GitLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const loadHistory = async (pageNum: number) => {
    try {
      setLoading(true);
      setError(undefined);

      const result = await gitLog({
        limit: COMMITS_PER_PAGE,
        offset: pageNum * COMMITS_PER_PAGE,
      });

      setCommits(result);
      setHasMore(result.length === COMMITS_PER_PAGE);
      setLoading(false);
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory(page);
  }, [page]);

  const goToPrevPage = () => {
    if (page > 0) {
      setPage(page - 1);
    }
  };

  const goToNextPage = () => {
    if (hasMore) {
      setPage(page + 1);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 7) {
        return date.toLocaleDateString();
      } else if (days > 0) {
        return `${days} day${days > 1 ? 's' : ''} ago`;
      } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
      } else if (minutes > 0) {
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
      } else {
        return 'Just now';
      }
    } catch {
      return timestamp;
    }
  };

  if (loading && commits.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        <span className="ml-2 text-slate-400">Loading history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-400">Error Loading History</h3>
            <p className="mt-1 text-sm text-red-300">{error}</p>
          </div>
          <button
            onClick={() => loadHistory(page)}
            className="text-red-400 hover:text-red-300 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (commits.length === 0) {
    return (
      <div className="text-center p-8 text-slate-400">
        <p>No commit history found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">Commit History</h2>
        <button
          onClick={() => loadHistory(page)}
          disabled={loading}
          className="rounded-md bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <span>Refresh</span>
          )}
        </button>
      </div>

      {/* Commit List */}
      <div className="space-y-3">
        {commits.map((commit) => (
          <div
            key={commit.hash}
            className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 hover:bg-slate-800 transition-colors"
          >
            <div className="flex items-start gap-3">
              <GitCommit className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                {/* Commit Message */}
                <div className="text-sm text-slate-200 break-words">
                  {commit.message}
                </div>

                {/* Commit Hash */}
                <div className="mt-2 flex items-center gap-2">
                  <code className="px-2 py-0.5 rounded bg-slate-900 text-xs text-slate-400 font-mono">
                    {commit.hash.substring(0, 8)}
                  </code>
                </div>

                {/* Author & Time */}
                <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <User className="h-3 w-3" />
                    <span>{commit.author}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3" />
                    <span>{formatTimestamp(commit.timestamp)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={goToPrevPage}
          disabled={page === 0 || loading}
          className="flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous</span>
        </button>

        <span className="text-sm text-slate-400">
          Page {page + 1}
        </span>

        <button
          onClick={goToNextPage}
          disabled={!hasMore || loading}
          className="flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Next</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
