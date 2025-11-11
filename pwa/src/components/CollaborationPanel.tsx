import { FormEvent, useEffect, useState } from "react";
import { useCollaborationStore } from "../state/collaboration";

export default function CollaborationPanel() {
  const {
    online,
    setOnline,
    enqueue,
    messages,
    queue,
    hydrate,
    token,
    setToken,
    agentStatus
  } = useCollaborationStore();
  const [buildingId, setBuildingId] = useState("ps-118");
  const [content, setContent] = useState("");

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

  const indicatorColor = online ? "bg-emerald-500/80" : "bg-amber-500/80";
  const indicatorText = online ? "Online" : "Offline (queued)";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-lg shadow-slate-900/40">
      <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Collaboration & Offline Queue</h3>
          <p className="text-xs text-slate-400">
            Messages sync through the desktop agent when connectivity is available.
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
        </div>
      </div>

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
          <span>Queued messages: {queue.length}</span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void hydrate()}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1 font-medium text-slate-100 transition hover:border-slate-500 hover:bg-slate-700"
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
              <footer className="mt-1 text-[10px] text-slate-500">
                {new Date(message.timestamp).toLocaleTimeString()}
              </footer>
            </article>
          ))
        )}
      </div>
    </div>
  );
}

