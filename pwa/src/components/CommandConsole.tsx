import { useEffect, useRef, useState } from "react";
import { useCommandExecutionStore } from "../state/commandExecution";

export default function CommandConsole() {
  const { logs, clearLogs, executionState } = useCommandExecutionStore();
  const consoleEndRef = useRef<HTMLDivElement | null>(null);
  const [height, setHeight] = useState(200);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newHeight = window.innerHeight - e.clientY;
      setHeight(Math.max(100, Math.min(600, newHeight)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "text-red-400";
      case "warn":
        return "text-yellow-400";
      case "success":
        return "text-green-400";
      default:
        return "text-slate-300";
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case "error":
        return "ERROR";
      case "warn":
        return "WARN";
      case "success":
        return "OK";
      default:
        return "INFO";
    }
  };

  return (
    <div
      className="flex flex-col border-t border-slate-800 bg-slate-950"
      style={{ height: `${height}px` }}
    >
      <div
        className="h-1 cursor-ns-resize bg-slate-800 hover:bg-slate-700 transition"
        onMouseDown={handleResizeStart}
      />

      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Console
          </span>
          {executionState === "running" && (
            <span className="animate-pulse text-[10px] font-medium uppercase tracking-wide text-amber-400">
              Running...
            </span>
          )}
        </div>
        <button
          onClick={clearLogs}
          className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300 transition hover:border-slate-600 hover:bg-slate-700"
        >
          Clear
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-slate-950 p-3 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="flex h-full items-center justify-center text-slate-600">
            No output yet. Execute a command to see results here.
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log) => {
              const timestamp = new Date(log.timestamp).toLocaleTimeString();
              return (
                <div key={log.id} className="flex gap-2">
                  <span className="text-slate-600">{timestamp}</span>
                  <span
                    className={`w-12 text-right font-semibold ${getLevelColor(log.level)}`}
                  >
                    {getLevelLabel(log.level)}
                  </span>
                  {log.command && (
                    <span className="text-cyan-400">$ {log.command}</span>
                  )}
                  <span className={getLevelColor(log.level)}>{log.message}</span>
                </div>
              );
            })}
            <div ref={consoleEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
