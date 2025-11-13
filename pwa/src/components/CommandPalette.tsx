import { useEffect, useMemo, useRef, useState } from "react";
import { useCommandPaletteStore } from "../state/commandPalette";

export default function CommandPalette() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const listRef = useRef<HTMLUListElement | null>(null);
  const [open, setOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { query, setQuery, clearQuery, filteredCommands, recordUse } =
    useCommandPaletteStore();

  const results = useMemo(() => filteredCommands(query), [filteredCommands, query]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [results]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      clearQuery();
      setSelectedIndex(0);
    }
  }, [open, clearQuery]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (event.key === "Enter" && results[selectedIndex]) {
      event.preventDefault();
      const command = results[selectedIndex];
      if (command.availability.pwa) {
        recordUse(command.id);
        command.onSelect();
        setOpen(false);
      }
    }
  };

  useEffect(() => {
    if (!open || !listRef.current) return;

    const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [selectedIndex, open]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300 shadow-sm transition hover:border-slate-500 hover:text-slate-100"
      >
        <span>Command Palette</span>
        <kbd className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
          ⌘K / Ctrl+K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 px-3 py-16 backdrop-blur-sm">
          <div className="w-full max-w-lg overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl shadow-black/60">
            <div className="flex items-center border-b border-slate-800 bg-slate-900/80 px-4">
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a command..."
                className="h-12 w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
              />
              <button
                onClick={() => setOpen(false)}
                className="text-xs text-slate-400 transition hover:text-slate-100"
              >
                ESC
              </button>
            </div>

            <ul ref={listRef} className="max-h-72 overflow-y-auto bg-slate-900/90">
              {results.length === 0 && (
                <li className="px-4 py-6 text-center text-xs text-slate-500">
                  No commands match &ldquo;{query}&rdquo; yet.
                </li>
              )}
              {results.map((command, index) => {
                const isPwaAvailable = command.availability.pwa;
                const isSelected = index === selectedIndex;
                return (
                  <li
                    key={command.id}
                    className="border-b border-slate-800/50 last:border-b-0"
                  >
                    <button
                      onClick={() => {
                        if (!isPwaAvailable) {
                          // Command not available in PWA - button is disabled
                          return;
                        }
                        recordUse(command.id);
                        command.onSelect();
                        setOpen(false);
                      }}
                      disabled={!isPwaAvailable}
                      className={`flex w-full items-start justify-between gap-4 px-4 py-3 text-left text-sm transition ${
                        isPwaAvailable
                          ? isSelected
                            ? "bg-slate-800/80 text-slate-200"
                            : "text-slate-200 hover:bg-slate-800/60"
                          : "cursor-not-allowed bg-slate-900/80 text-slate-500 opacity-60"
                      }`}
                    >
                      <span className="flex-1">
                        <span className="flex items-center gap-2 text-[11px] uppercase tracking-wide text-slate-500">
                          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-300">
                            {command.categoryLabel}
                          </span>
                        </span>
                        <span className="mt-1 block font-medium text-slate-100">{command.title}</span>
                        <span className="mt-1 block text-xs text-slate-400">{command.description}</span>
                        <span className="mt-1 block text-[11px] text-slate-500">{command.command}</span>
                        {command.tags.length > 0 && (
                          <span className="mt-2 flex flex-wrap gap-1">
                            {command.tags.map((tag) => (
                              <span
                                key={tag}
                                className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-300"
                              >
                                #{tag}
                              </span>
                            ))}
                          </span>
                        )}
                        <span className="mt-2 flex gap-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                          <AvailabilityBadge label="CLI" active={command.availability.cli} />
                          <AvailabilityBadge label="PWA" active={command.availability.pwa} />
                          <AvailabilityBadge label="Agent" active={command.availability.agent} />
                        </span>
                      </span>
                      {command.shortcut && (
                        <kbd className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                          {command.shortcut}
                        </kbd>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

type AvailabilityBadgeProps = {
  label: "CLI" | "PWA" | "Agent";
  active: boolean;
};

function AvailabilityBadge({ label, active }: AvailabilityBadgeProps) {
  return (
    <span
      className={`rounded px-1.5 py-0.5 ${
        active
          ? "border border-slate-600 bg-slate-700/70 text-slate-200"
          : "border border-slate-800 bg-slate-900 text-slate-600 line-through"
      }`}
    >
      {label}
    </span>
  );
}

