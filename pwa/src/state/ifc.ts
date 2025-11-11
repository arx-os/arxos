import { create } from "zustand";
import { invokeAgent } from "../lib/agent";
import { useCollaborationStore } from "./collaboration";

type ImportSummary = {
  buildingName: string;
  yamlPath: string;
  floors: number;
  rooms: number;
  equipment: number;
};

type ExportArtifact = {
  filename: string;
  sizeBytes: number;
  downloadUrl: string;
};

type IfcStore = {
  importing: boolean;
  exporting: boolean;
  error?: string;
  lastImport?: ImportSummary;
  lastExport?: ExportArtifact;
  importIfc: (file: File) => Promise<void>;
  exportIfc: (options?: { filename?: string; delta?: boolean }) => Promise<void>;
  clearError: () => void;
};

function getAgentToken(): string {
  const token = useCollaborationStore.getState().token;
  if (!token.startsWith("did:key:")) {
    throw new Error("Agent token missing or invalid");
  }
  return token;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToBlobUri(base64: string, mime = "application/octet-stream"): string {
  const binaryString =
    typeof atob === "function"
      ? atob(base64)
      : (() => {
          const maybeBuffer = (globalThis as unknown as {
            Buffer?: { from(data: string, encoding: string): { toString(encoding: string): string } };
          }).Buffer;
          return typeof maybeBuffer !== "undefined"
            ? maybeBuffer.from(base64, "base64").toString("binary")
            : base64;
        })();

  if (typeof Blob === "function" && typeof URL !== "undefined" && typeof URL.createObjectURL === "function") {
    const binary = binaryString;
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: mime });
    return URL.createObjectURL(blob);
  }
  return `data:${mime};base64,${base64}`;
}

export const useIfcStore = create<IfcStore>((set) => ({
  importing: false,
  exporting: false,
  error: undefined,
  lastImport: undefined,
  lastExport: undefined,
  importIfc: async (file) => {
    try {
      set({ importing: true, error: undefined });
      const token = getAgentToken();
      const buffer = await file.arrayBuffer();
      const base64 = arrayBufferToBase64(buffer);

      const response = await invokeAgent<{
        building_name: string;
        yaml_path: string;
        floors: number;
        rooms: number;
        equipment: number;
      }>(token, "ifc.import", {
        filename: file.name,
        data: base64
      });

      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }

      set({
        importing: false,
        lastImport: {
          buildingName: response.payload.building_name,
          yamlPath: response.payload.yaml_path,
          floors: response.payload.floors,
          rooms: response.payload.rooms,
          equipment: response.payload.equipment
        }
      });
    } catch (error) {
      set({ importing: false, error: (error as Error).message });
    }
  },
  exportIfc: async (options) => {
    try {
      set({ exporting: true, error: undefined });
      const token = getAgentToken();
      const response = await invokeAgent<{
        filename: string;
        data: string;
        size_bytes: number;
      }>(token, "ifc.export", {
        filename: options?.filename,
        delta: options?.delta ?? false
      });

      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }

      const downloadUrl =
        base64ToBlobUri(response.payload.data) || `data:application/octet-stream;base64,${response.payload.data}`;
      set({
        exporting: false,
        lastExport: {
          filename: response.payload.filename,
          sizeBytes: response.payload.size_bytes,
          downloadUrl
        }
      });
    } catch (error) {
      set({ exporting: false, error: (error as Error).message });
    }
  },
  clearError: () => set({ error: undefined })
}));
