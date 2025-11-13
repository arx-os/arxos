import Fuse from "fuse.js";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { executeCommand } from "../lib/commandExecutor";
import {
  fetchCommandPalette,
  initWasm,
  type WasmCommandAvailability,
  type WasmCommandEntry
} from "../lib/wasm";
import { useCommandExecutionStore } from "./commandExecution";

export type CommandAvailability = WasmCommandAvailability;

export type PaletteCommand = {
  id: string;
  title: string;
  description: string;
  command: string;
  category: string;
  categoryLabel: string;
  shortcut?: string;
  lastUsed?: number;
  onSelect: () => void;
  tags: string[];
  availability: CommandAvailability;
};

type StoreState = {
  commands: PaletteCommand[];
  query: string;
  setQuery: (value: string) => void;
  clearQuery: () => void;
  hydrate: () => Promise<void>;
  filteredCommands: (value: string) => PaletteCommand[];
  recordUse: (id: string) => void;
};

const DEFAULT_AVAILABILITY: CommandAvailability = {
  cli: true,
  pwa: true,
  agent: false
};

function mapCommand(entry: WasmCommandEntry, _version: string): PaletteCommand {
  const executeAndLog = async (command: string) => {
    const { addLog, setExecutionState, setCurrentCommand } = useCommandExecutionStore.getState();

    setExecutionState("running");
    setCurrentCommand(command);
    addLog("info", `Executing: ${command}`, command);

    try {
      const result = await executeCommand(command);

      if (result.success) {
        if (result.output) {
          addLog("success", result.output);
        }
        addLog("info", `Command completed in ${result.duration}ms`);
        setExecutionState("complete");
      } else {
        addLog("error", result.error || "Command failed");
        setExecutionState("error");
      }
    } catch (error) {
      addLog("error", error instanceof Error ? error.message : String(error));
      setExecutionState("error");
    } finally {
      setCurrentCommand(null);
    }
  };

  const overrides: Record<string, () => void> = {
    version: () => void executeAndLog("version"),
    "arxos health": () => {
      // Health checks will be routed through the desktop agent in M04
      const { addLog } = useCommandExecutionStore.getState();
      addLog("warn", "Health checks require desktop agent connection (available in M04)");
    },
    "arxos watch": () => {
      // Live watch mode will activate after the agent WebSocket handshake in M04
      const { addLog } = useCommandExecutionStore.getState();
      addLog("warn", "Watch mode requires desktop agent connection (available in M04)");
    }
  };

  return {
    id: entry.command,
    title: entry.name,
    description: entry.description,
    command: entry.command,
    category: entry.category.slug,
    categoryLabel: entry.category.label,
    shortcut: entry.shortcut,
    onSelect: overrides[entry.command] ?? (() => void executeAndLog(entry.command)),
    tags: Array.isArray(entry.tags) ? entry.tags : [],
    availability: entry.availability ?? DEFAULT_AVAILABILITY
  };
}

export const useCommandPaletteStore = create<StoreState>()(
  persist(
    (set, get) => ({
      commands: [],
      query: "",
      setQuery: (value) => set({ query: value }),
      clearQuery: () => set({ query: "" }),
      filteredCommands: (value: string) => {
        const normalized = value.trim();
        const sorted = [...get().commands].sort(
          (a, b) => (b.lastUsed ?? Number.NEGATIVE_INFINITY) - (a.lastUsed ?? Number.NEGATIVE_INFINITY)
        );

        if (!normalized) {
          return sorted.slice(0, 10);
        }

        const fuse = new Fuse(sorted, {
          keys: [
            { name: "title", weight: 0.4 },
            { name: "description", weight: 0.2 },
            { name: "command", weight: 0.3 },
            { name: "tags", weight: 0.05 },
            { name: "categoryLabel", weight: 0.05 }
          ],
          threshold: 0.4,
          includeScore: true,
          ignoreLocation: true
        });

        const results = fuse.search(normalized);
        return results.map((result) => result.item);
      },
      recordUse: (id: string) => {
        set((state) => ({
          commands: state.commands.map((command) =>
            command.id === id ? { ...command, lastUsed: Date.now() } : command
          )
        }));
      },
      hydrate: async () => {
        const wasm = await initWasm();
        const version = wasm.arxos_version();
        const entries = await fetchCommandPalette();
        const commands = entries.map((entry) => mapCommand(entry, version));
        set({ commands });
      }
    }),
    {
      name: "arxos-command-palette",
      version: 2,
      migrate: (persistedState, version) => {
        if (!persistedState || typeof persistedState !== "object") {
          return persistedState as StoreState | undefined;
        }
        const state = persistedState as StoreState;
        if (version < 2) {
          return {
            ...state,
            commands: state.commands.map((command) => ({
              ...command,
              tags: command.tags ?? [],
              availability: command.availability ?? DEFAULT_AVAILABILITY
            }))
          };
        }
        return state;
      }
    }
  )
);

