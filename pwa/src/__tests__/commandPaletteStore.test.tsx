import { act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useCommandPaletteStore } from "../state/commandPalette";

vi.mock("../lib/wasm", () => {
  return {
    initWasm: vi.fn().mockResolvedValue({ arxos_version: () => "2.0.0" }),
    fetchCommandPalette: vi.fn().mockResolvedValue([
      {
        name: "Show Version",
        command: "arxos version",
        description: "Print the active WASM version",
        category: { slug: "system", label: "System" },
        shortcut: "Shift+V",
        tags: ["system", "version"],
        availability: { cli: true, pwa: true, agent: true }
      },
      {
        name: "Run Health Check",
        command: "arxos health",
        description: "Check system health",
        category: { slug: "health", label: "Health" },
        tags: ["health", "status"],
        availability: { cli: true, pwa: true, agent: true }
      }
    ]),
    fetchCommandDetails: vi.fn().mockResolvedValue(null)
  };
});

afterEach(() => {
  useCommandPaletteStore.setState((state) => ({
    ...state,
    commands: [],
    query: ""
  }));
  vi.clearAllMocks();
});

describe("command palette store", () => {
  it("hydrates commands from wasm catalog", async () => {
    await act(async () => {
      await useCommandPaletteStore.getState().hydrate();
    });

    const commands = useCommandPaletteStore.getState().commands;
    expect(commands).toHaveLength(2);
    expect(commands[0]).toMatchObject({
      title: "Show Version",
      command: "arxos version",
      category: "system",
      shortcut: "Shift+V",
      tags: ["system", "version"],
      availability: { cli: true, pwa: true, agent: true }
    });
  });

  it("updates command usage timestamps", async () => {
    await act(async () => {
      await useCommandPaletteStore.getState().hydrate();
    });

    const [first] = useCommandPaletteStore.getState().commands;
    expect(first.lastUsed).toBeUndefined();

    act(() => {
      useCommandPaletteStore.getState().recordUse(first.id);
    });

    const updated = useCommandPaletteStore
      .getState()
      .commands.find((command) => command.id === first.id);
    expect(updated?.lastUsed).toBeDefined();
  });
});
