import { FormEvent, useEffect, useMemo, useState } from "react";
import { useGitStore } from "../state/git";
import { useCollaborationStore } from "../state/collaboration";

export default function GitStatusPanel() {
  const {
    status,
    diff,
    file,
    loading,
    error,
    refreshStatus,
    loadDiff,
    commit,
    readFile,
    clearError
  } = useGitStore();
  const { agentStatus, token } = useCollaborationStore();
  const [commitMessage, setCommitMessage] = useState("Workspace sync");
  const [stageAll, setStageAll] = useState(true);
  const [filePath, setFilePath] = useState("building.yaml");

  useEffect(() => {
    if (token.startsWith("did:key:")) {
      void refreshStatus();
    }
  }, [refreshStatus, token]);

  const formattedTime = useMemo(() => {
    if (!status?.last_commit_time) {
      return "No commits";
    }
    return new Date(status.last_commit_time * 1000).toLocaleString();
  }, [status?.last_commit_time]);

  const handleCommit = async (event: FormEvent) => {
    event.preventDefault();
    await commit(commitMessage, stageAll);
    setCommitMessage("Workspace sync");
  };

  return (
    <section
      className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/40"
      data-testid="panel-git"
    >
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-100">Git Workspace</h2>
          <p className="text-xs text-slate-400">
            View repository status, diff staged changes, commit, and inspect files through the desktop agent.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-100">
          <span
            className={`rounded-md px-2 py-0.5 ${
              agentStatus === "connected"
                ? "bg-emerald-500/40"
                : agentStatus === "connecting"
                ? "bg-sky-500/40"
                : agentStatus === "error"
                ? "bg-red-500/40"
                : "bg-slate-800"
            }`}
          >
            Agent {agentStatus}
          </span>
          <button
            type="button"
            onClick={() => void refreshStatus()}
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
          >
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-500/50 bg-red-900/30 px-3 py-2 text-xs text-red-200">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => clearError()} className="text-[10px] uppercase tracking-wide">
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <h3 className="text-sm font-semibold text-slate-100">Status</h3>
          {status ? (
            <dl className="mt-2 space-y-1">
              <div className="flex justify-between">
                <dt>Branch</dt>
                <dd className="font-semibold text-slate-100">{status.branch}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Last Commit</dt>
                <dd className="text-right">
                  <div>{status.last_commit_message || "No commits"}</div>
                  <div className="text-[10px] text-slate-500">{formattedTime}</div>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt>Staged</dt>
                <dd>{status.staged_changes}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Unstaged</dt>
                <dd>{status.unstaged_changes}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Untracked</dt>
                <dd>{status.untracked}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Diff</dt>
                <dd>
                  +{status.diff_summary.insertions} / -{status.diff_summary.deletions} in {status.diff_summary.files_changed} files
                </dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-slate-500">
              {loading ? "Loading status…" : "Agent idle. Connect to a repo and refresh."}
            </p>
          )}
        </article>

        <form onSubmit={handleCommit} className="space-y-2 rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <h3 className="text-sm font-semibold text-slate-100">Commit</h3>
          <textarea
            value={commitMessage}
            onChange={(event) => setCommitMessage(event.target.value)}
            className="h-20 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="Describe your changes"
          />
          <label className="flex items-center gap-2 text-[11px]">
            <input
              type="checkbox"
              checked={stageAll}
              onChange={(event) => setStageAll(event.target.checked)}
              className="rounded border border-slate-600 bg-slate-950 text-sky-400 focus:ring-sky-500"
            />
            Stage all changes before committing
          </label>
          <button
            type="submit"
            disabled={loading || !commitMessage.trim()}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Commit
          </button>
        </form>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <article className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100">Diff</h3>
            <button
              type="button"
              disabled={loading}
              onClick={() => void loadDiff({})}
              className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-[10px] uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
            >
              Load HEAD diff
            </button>
          </div>
          {diff ? (
            <div className="space-y-2 max-h-48 overflow-y-auto rounded border border-slate-800 bg-slate-950/80 p-2 font-mono text-[11px] leading-relaxed">
              {diff.files.map((item, index) => (
                <pre key={`${item.file_path}-${index}`}>
                  <span className="text-slate-500">{item.file_path}:{item.line_number}</span>
                  <br />
                  <span
                    className={
                      item.kind === "addition"
                        ? "text-emerald-400"
                        : item.kind === "deletion"
                        ? "text-rose-400"
                        : "text-slate-300"
                    }
                  >
                    {item.content}
                  </span>
                </pre>
              ))}
            </div>
          ) : (
            <p className="text-slate-500">{loading ? "Loading diff…" : "Run a diff to view changes."}</p>
          )}
        </article>

        <article className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-100">File Viewer</h3>
            <div className="flex gap-2">
              <input
                value={filePath}
                onChange={(event) => setFilePath(event.target.value)}
                className="w-48 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-100 focus:border-slate-500 focus:outline-none"
                placeholder="relative/path.yaml"
              />
              <button
                type="button"
                disabled={loading || !filePath.trim()}
                onClick={() => void readFile(filePath)}
                className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-[10px] uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
              >
                Load
              </button>
            </div>
          </div>
          {file ? (
            <div className="max-h-48 overflow-y-auto rounded border border-slate-800 bg-slate-950/80 p-2 font-mono text-[11px] leading-relaxed">
              <p className="mb-1 text-[10px] uppercase text-slate-500">{file.path}</p>
              <pre>{file.content}</pre>
            </div>
          ) : (
            <p className="text-slate-500">Select a file to preview.</p>
          )}
        </article>
      </div>
    </section>
  );
}
