import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  fetchCommandDetails,
  fetchCommandPalette,
  initWasm,
  type WasmCommandEntry
} from "../lib/wasm";

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

function mapCommand(entry: WasmCommandEntry, version: string): PaletteCommand {
  const fallback = () => {
    void fetchCommandDetails(entry.name).then((details) => {
      console.info("Command invoked", details ?? entry);
    });
  };

  const overrides: Record<string, () => void> = {
    version: () => console.info("ArxOS WASM version:", version),
    "arxos health": () =>
      console.info("Health checks will be routed through the desktop agent once available."),
    "arxos watch": () =>
      console.info("Live watch mode will activate after the agent WebSocket handshake is built.")
  };

  return {
    id: entry.command,
    title: entry.name,
    description: entry.description,
    command: entry.command,
    category: entry.category.slug,
    categoryLabel: entry.category.label,
    shortcut: entry.shortcut,
    onSelect: overrides[entry.command] ?? fallback
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
        const normalized = value.toLowerCase().trim();
        const sorted = [...get().commands].sort(
          (a, b) => (b.lastUsed ?? Number.NEGATIVE_INFINITY) - (a.lastUsed ?? Number.NEGATIVE_INFINITY)
        );
        if (!normalized) {
          return sorted.slice(0, 10);
        }
        return sorted.filter((command) => {
          const haystack = `${command.title} ${command.description} ${command.command} ${command.categoryLabel}`.toLowerCase();
          return haystack.includes(normalized);
        });
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
      name: "arxos-command-palette"
    }
  )
);

