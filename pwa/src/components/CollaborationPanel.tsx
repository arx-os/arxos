import { FormEvent, useEffect, useMemo, useState } from "react";
import { useCollaborationStore } from "../state/collaboration";
import type { CollabConfig } from "../lib/agent";

export default function CollaborationPanel() {
  const {
    online,
    setOnline,
    enqueue,
    messages,
    queue,
    hydrate,
    flushQueue,
    token,
    setToken,
    agentStatus,
    lastSync,
    syncTarget,
    configureTarget,
    retryMessage,
    isSyncing
  } = useCollaborationStore();

  const [buildingId, setBuildingId] = useState("ps-118");
  const [content, setContent] = useState("");
  const [owner, setOwner] = useState("" );
  const [repo, setRepo] = useState("");
  const [targetType, setTargetType] = useState<"issue" | "pull_request">("issue");
  const [targetNumber, setTargetNumber] = useState("1");
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSaving, setConfigSaving] = useState(false);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [setOnline]);

  useEffect(() => {
    if (online) {
      void hydrate();
    }
  }, [hydrate, online, queue.length]);

  useEffect(() => {
    if (syncTarget) {
      setOwner(syncTarget.owner);
      setRepo(syncTarget.repo);
      setTargetType(syncTarget.target.type);
      setTargetNumber(String(syncTarget.target.number));
    }
  }, [syncTarget]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!content.trim()) {
      return;
    }
    enqueue({
      buildingId,
      author: "field-tech@arxos",
      content: content.trim()
    });
    setContent("");
  };

  const handleConfigSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setConfigError(null);
    const parsedNumber = Number(targetNumber);
    if (!owner.trim() || !repo.trim() || Number.isNaN(parsedNumber) || parsedNumber <= 0) {
      setConfigError("Owner, repo, and positive issue/PR number are required");
      return;
    }

    const config: CollabConfig = {
      owner: owner.trim(),
      repo: repo.trim(),
      target: {
        type: targetType,
        number: parsedNumber
      }
    };

    try {
      setConfigSaving(true);
      await configureTarget(config);
    } catch (error) {
      setConfigError(error instanceof Error ? error.message : String(error));
    } finally {
      setConfigSaving(false);
    }
  };

  const indicatorColor = online ? "bg-emerald-500/80" : "bg-amber-500/80";
  const indicatorText = online ? "Online" : "Offline (queued)";

  const targetSummary = useMemo(() => {
    if (!syncTarget) {
      return "Not configured";
    }
    return `${syncTarget.owner}/${syncTarget.repo} #${syncTarget.target.number} (${syncTarget.target.type})`;
  }, [syncTarget]);

  return (
    <div
      className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-lg shadow-slate-900/40"
      data-testid="panel-collaboration"
    >
      <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Collaboration & Offline Queue</h3>
          <p className="text-xs text-slate-400">
            Messages sync to GitHub issues or PRs via the desktop agent when connectivity is available.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-slate-100">
          <span className={`flex items-center gap-1 rounded-md px-2 py-0.5 ${indicatorColor}`}>
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-white" />
            {indicatorText}
          </span>
          <span
            className={`flex items-center gap-1 rounded-md px-2 py-0.5 ${
              agentStatus === "connected"
                ? "bg-emerald-500/40"
                : agentStatus === "connecting"
                ? "bg-sky-500/40"
                : agentStatus === "error"
                ? "bg-red-500/40"
                : "bg-slate-700/60"
            }`}
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-white" />
            Agent: {agentStatus}
          </span>
          {lastSync && (
            <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-200">
              Last sync {new Date(lastSync).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <section className="mb-4 space-y-3 rounded-md border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="font-semibold text-slate-200">GitHub Target</p>
            <p className="text-slate-400">{targetSummary}</p>
          </div>
          <button
            type="button"
            onClick={() => void hydrate()}
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-[10px] uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
          >
            Refresh
          </button>
        </header>
        <form onSubmit={handleConfigSubmit} className="grid gap-2 md:grid-cols-4">
          <input
            value={owner}
            onChange={(event) => setOwner(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="owner"
          />
          <input
            value={repo}
            onChange={(event) => setRepo(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="repo"
          />
          <select
            value={targetType}
            onChange={(event) => setTargetType(event.target.value as "issue" | "pull_request")}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
          >
            <option value="issue">Issue</option>
            <option value="pull_request">Pull Request</option>
          </select>
          <input
            value={targetNumber}
            onChange={(event) => setTargetNumber(event.target.value.replace(/[^0-9]/g, ""))}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="#"
          />
          <div className="md:col-span-4 flex items-center justify-between">
            {configError && <span className="text-[11px] text-red-400">{configError}</span>}
            <button
              type="submit"
              disabled={configSaving}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1 text-[10px] font-medium uppercase tracking-wide text-slate-100 transition hover:border-slate-500 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {configSaving ? "Saving…" : "Save Target"}
            </button>
          </div>
        </form>
      </section>

      <form onSubmit={handleSubmit} className="mb-4 space-y-2">
        <div className="flex flex-wrap gap-2">
          <input
            value={buildingId}
            onChange={(event) => setBuildingId(event.target.value)}
            className="w-32 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="Building ID"
          />
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            className="h-16 flex-1 min-w-[200px] resize-none rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-100 focus:border-slate-500 focus:outline-none"
            placeholder="Share an update (equipment notes, reminders, AR scan issues...)"
          />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <span>
            Queued messages: {queue.length}
            {isSyncing && " (syncing…)"}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void flushQueue()}
              disabled={isSyncing}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1 font-medium text-slate-100 transition hover:border-slate-500 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Sync Now
            </button>
            <button
              type="submit"
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1 font-medium text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
            >
              Send
            </button>
          </div>
        </div>
      </form>

      <div className="mb-4 space-y-2 rounded-md border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300">
        <p className="font-semibold text-slate-200">Agent Authentication</p>
        <p className="text-slate-400">
          Enter the DID:key token printed by `arxos-agent`. The token never leaves your device; it is
          used to sign WebSocket requests over the loopback interface.
        </p>
        <input
          value={token}
          onChange={(event) => setToken(event.target.value)}
          placeholder="did:key:z..."
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-[11px] text-slate-100 focus:border-slate-500 focus:outline-none"
        />
      </div>

      <div className="space-y-2">
        {messages.length === 0 ? (
          <div className="rounded-md border border-slate-800 bg-slate-950/60 px-3 py-4 text-xs text-slate-400">
            Collaboration history will appear here once you queue or receive updates.
          </div>
        ) : (
          messages.slice(0, 6).map((message) => (
            <article
              key={message.id}
              className="rounded-md border border-slate-800 bg-slate-950/70 px-3 py-2 text-xs leading-relaxed text-slate-200"
            >
              <header className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide text-slate-400">
                <span>{message.buildingId}</span>
                <span className="flex items-center gap-1">
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full ${
                      message.status === "sent"
                        ? "bg-emerald-400"
                        : message.status === "pending"
                        ? "bg-amber-400"
                        : "bg-red-400"
                    }`}
                  />
                  {message.status}
                </span>
              </header>
              <p>{message.content}</p>
              <footer className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500">
                <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                <div className="flex flex-wrap items-center gap-2">
                  {message.remoteUrl && (
                    <a
                      href={message.remoteUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-md border border-slate-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-200 hover:border-slate-500"
                    >
                      View on GitHub
                    </a>
                  )}
                  {message.status === "error" && (
                    <button
                      type="button"
                      onClick={() => retryMessage(message.id)}
                      className="rounded-md border border-red-500/60 px-2 py-0.5 text-[10px] uppercase tracking-wide text-red-200 hover:border-red-400"
                    >
                      Retry
                    </button>
                  )}
                </div>
              </footer>
              {message.errorReason && (
                <p className="mt-1 text-[10px] text-red-400">{message.errorReason}</p>
              )}
            </article>
          ))
        )}
      </div>
    </div>
  );
}

