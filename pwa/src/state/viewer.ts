import { create } from "zustand";
import { generateScanMesh, type WasmMeshBuffers } from "../lib/wasm";

export type MeshBuffers = {
  wallPositions: Float32Array;
  equipmentPositions: Float32Array;
  pointCloudPositions: Float32Array;
  boundsMin: [number, number, number];
  boundsMax: [number, number, number];
};

type ViewerStore = {
  mesh?: MeshBuffers;
  loading: boolean;
  error?: string;
  updateFromScan: (json: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
};

function toFloat32Array(values: number[]): Float32Array {
  return new Float32Array(values);
}

function normalizeBuffers(payload: WasmMeshBuffers): MeshBuffers {
  return {
    wallPositions: toFloat32Array(payload.wallPositions ?? []),
    equipmentPositions: toFloat32Array(payload.equipmentPositions ?? []),
    pointCloudPositions: toFloat32Array(payload.pointCloudPositions ?? []),
    boundsMin: payload.boundsMin ?? [0, 0, 0],
    boundsMax: payload.boundsMax ?? [0, 0, 0]
  };
}

export const useViewerStore = create<ViewerStore>((set) => ({
  mesh: undefined,
  loading: false,
  error: undefined,
  updateFromScan: async (json: string) => {
    try {
      set({ loading: true, error: undefined });
      const payload = await generateScanMesh(json);
      set({ mesh: normalizeBuffers(payload), loading: false });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  },
  clearError: () => set({ error: undefined }),
  reset: () => set({ mesh: undefined, loading: false, error: undefined })
}));
