import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../lib/wasm", () => ({
  generateScanMesh: vi.fn()
}));

import { generateScanMesh } from "../lib/wasm";
import { useViewerStore } from "../state/viewer";

function resetStore() {
  useViewerStore.setState({ mesh: undefined, loading: false, error: undefined });
  vi.resetAllMocks();
}

describe("viewer store", () => {
  afterEach(() => {
    resetStore();
  });

  it("stores mesh buffers from wasm", async () => {
    vi.mocked(generateScanMesh).mockResolvedValue({
      wallPositions: [0, 0, 0, 1, 0, 0],
      equipmentPositions: [0.5, 0, 0.25],
      pointCloudPositions: [0.5, 0, 0.25],
      boundsMin: [0, 0, 0],
      boundsMax: [1, 1, 1]
    });

    await useViewerStore.getState().updateFromScan("{}" as string);

    const { mesh, error, loading } = useViewerStore.getState();
    expect(loading).toBe(false);
    expect(error).toBeUndefined();
    expect(mesh?.wallPositions.length).toBe(6);
    expect(mesh?.equipmentPositions.length).toBe(3);
  });

  it("captures wasm failure", async () => {
    vi.mocked(generateScanMesh).mockRejectedValue(new Error("boom"));

    await useViewerStore.getState().updateFromScan("{}" as string);

    const state = useViewerStore.getState();
    expect(state.error).toContain("boom");
    expect(state.loading).toBe(false);
  });
});
