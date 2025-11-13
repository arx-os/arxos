import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

// Mock the agent commands
vi.mock("../modules/agent/commands/ifc", () => ({
  ifcImport: vi.fn(),
  ifcExport: vi.fn(),
}));

// Mock the agent store
vi.mock("../modules/agent/state/agentStore", () => ({
  useAgentStore: {
    getState: () => ({
      isInitialized: true,
      connectionState: { status: "connected" },
    }),
  },
}));

import { ifcImport, ifcExport } from "../modules/agent/commands/ifc";
import { useIfcStore } from "../state/ifc";

beforeAll(() => {
  (globalThis as unknown as { URL: typeof URL }).URL.createObjectURL = vi
    .fn()
    .mockReturnValue("blob://test");
  (globalThis as unknown as { URL: typeof URL }).URL.revokeObjectURL = vi.fn();
});

function resetStore() {
  useIfcStore.setState({
    importing: false,
    exporting: false,
    importProgress: 0,
    exportProgress: 0,
    progressMessage: "",
    error: undefined,
    lastImport: undefined,
    lastExport: undefined,
  });
}

function createMockFile(name: string): File {
  const buffer = new TextEncoder().encode("dummy").buffer;
  const mock = {
    name,
    async arrayBuffer() {
      return buffer;
    }
  } as File;
  return mock;
}

describe("ifc store", () => {
  afterEach(() => {
    resetStore();
    vi.resetAllMocks();
  });

  it("handles successful import", async () => {
    vi.mocked(ifcImport).mockResolvedValue({
      success: true,
      buildingPath: "Sample",
      yamlPath: "sample.yaml",
      floorCount: 2,
      roomCount: 10,
      equipmentCount: 5,
    });

    const file = createMockFile("sample.ifc");
    await useIfcStore.getState().importIfc(file);

    const summary = useIfcStore.getState().lastImport;
    expect(summary?.buildingName).toBe("Sample");
    expect(summary?.floors).toBe(2);
  });

  it("captures export artifact", async () => {
    const base64Data = btoa("ifc");
    vi.mocked(ifcExport).mockResolvedValue({
      success: true,
      base64Data,
      size: 3,
      filePath: undefined,
    });

    await useIfcStore.getState().exportIfc({ filename: "building.ifc" });
    const state = useIfcStore.getState();
    expect(state.error).toBeUndefined();
    expect(state.lastExport).toBeDefined();
    expect(state.lastExport?.filename).toBe("building.ifc");
    expect(state.lastExport?.sizeBytes).toBe(3);
    // Note: downloadUrl creation depends on browser APIs (URL.createObjectURL)
    // which may not be available in test environment
  });

  it("records agent errors", async () => {
    vi.mocked(ifcImport).mockRejectedValue(new Error("boom"));

    const file = createMockFile("sample.ifc");
    await useIfcStore.getState().importIfc(file);

    expect(useIfcStore.getState().error).toContain("boom");
  });
});
