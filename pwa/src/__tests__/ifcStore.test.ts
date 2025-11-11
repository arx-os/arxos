import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

vi.mock("../lib/agent", () => ({
  invokeAgent: vi.fn()
}));

vi.mock("../state/collaboration", () => ({
  useCollaborationStore: {
    getState: () => ({ token: "did:key:test", agentStatus: "connected" })
  }
}));

import { invokeAgent } from "../lib/agent";
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
    error: undefined,
    lastImport: undefined,
    lastExport: undefined
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
    const payload = {
      building_name: "Sample",
      yaml_path: "sample.yaml",
      floors: 2,
      rooms: 10,
      equipment: 5
    };
    vi.mocked(invokeAgent).mockResolvedValue({ status: "ok", payload });

    const file = createMockFile("sample.ifc");
    await useIfcStore.getState().importIfc(file);

    const summary = useIfcStore.getState().lastImport;
    expect(summary?.buildingName).toBe("Sample");
    expect(summary?.floors).toBe(2);
  });

  it("captures export artifact", async () => {
    const payload = {
      filename: "exports/building.ifc",
      data: btoa("ifc"),
      size_bytes: 3
    };
    vi.mocked(invokeAgent).mockResolvedValue({ status: "ok", payload });

    await useIfcStore.getState().exportIfc();
    const state = useIfcStore.getState();
    expect(state.error).toBeUndefined();
    expect(state.lastExport).toBeDefined();
    expect(state.lastExport?.filename).toBe("exports/building.ifc");
    expect(state.lastExport?.sizeBytes).toBe(3);
    expect(typeof state.lastExport?.downloadUrl).toBe("string");
  });

  it("records agent errors", async () => {
    vi.mocked(invokeAgent).mockResolvedValue({ status: "error", payload: { error: "boom" } });

    const file = createMockFile("sample.ifc");
    await useIfcStore.getState().importIfc(file);

    expect(useIfcStore.getState().error).toContain("boom");
  });
});
