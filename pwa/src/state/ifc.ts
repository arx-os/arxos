import { create } from "zustand";
import { ifcImport, ifcExport } from "../modules/agent/commands/ifc";
import { useAgentStore } from "../modules/agent/state/agentStore";

/**
 * Type definition for Node.js Buffer API when available in the global context
 * This is typically only available in Node.js environments, not browsers
 */
interface NodeBuffer {
  from(data: string, encoding: BufferEncoding): NodeBuffer;
  toString(encoding: BufferEncoding): string;
}

type BufferEncoding = "base64" | "binary" | "utf8" | "utf-8" | "hex" | "ascii";

/**
 * Global interface extension for Node.js Buffer API
 */
interface GlobalWithBuffer {
  Buffer: {
    from(data: string, encoding: BufferEncoding): NodeBuffer;
  };
}

/**
 * Type guard to check if Buffer API is available (Node.js environment)
 */
function hasBufferAPI(global: typeof globalThis): global is typeof globalThis & GlobalWithBuffer {
  return typeof (global as { Buffer?: unknown }).Buffer !== "undefined";
}

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
  importProgress: number;
  exportProgress: number;
  progressMessage: string;
  error?: string;
  lastImport?: ImportSummary;
  lastExport?: ExportArtifact;
  importIfc: (file: File) => Promise<void>;
  exportIfc: (options?: { filename?: string; delta?: boolean }) => Promise<void>;
  clearError: () => void;
};

function checkAgentConnected(): void {
  const agentState = useAgentStore.getState();
  if (!agentState.isInitialized || agentState.connectionState.status !== "connected") {
    throw new Error("Agent not connected. Please authenticate first.");
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert base64 string to a Blob URI for downloading
 * Falls back to data URI if Blob API is not available
 * Uses Node.js Buffer API when available (SSR/Node environments)
 */
function base64ToBlobUri(base64: string, mime = "application/octet-stream"): string {
  // Decode base64 to binary string
  const binaryString =
    typeof atob === "function"
      ? atob(base64)
      : hasBufferAPI(globalThis)
        ? globalThis.Buffer.from(base64, "base64").toString("binary")
        : base64; // Fallback - return as-is if no decoding available

  // Create Blob URI if APIs are available
  if (typeof Blob === "function" && typeof URL !== "undefined" && typeof URL.createObjectURL === "function") {
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i += 1) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: mime });
    return URL.createObjectURL(blob);
  }

  // Fallback to data URI
  return `data:${mime};base64,${base64}`;
}

export const useIfcStore = create<IfcStore>((set) => ({
  importing: false,
  exporting: false,
  importProgress: 0,
  exportProgress: 0,
  progressMessage: "",
  error: undefined,
  lastImport: undefined,
  lastExport: undefined,
  importIfc: async (file) => {
    try {
      set({ importing: true, importProgress: 0, progressMessage: "Starting import...", error: undefined });
      checkAgentConnected();

      const buffer = await file.arrayBuffer();
      const base64 = arrayBufferToBase64(buffer);

      const result = await ifcImport(
        {
          base64Data: base64,
        },
        (progress, message) => {
          set({ importProgress: progress, progressMessage: message });
        }
      );

      if (!result.success) {
        throw new Error("IFC import failed");
      }

      set({
        importing: false,
        importProgress: 100,
        progressMessage: "Import complete!",
        lastImport: {
          buildingName: result.buildingPath,
          yamlPath: result.yamlPath,
          floors: result.floorCount,
          rooms: result.roomCount,
          equipment: result.equipmentCount,
        },
      });
    } catch (error) {
      set({ importing: false, importProgress: 0, progressMessage: "", error: (error as Error).message });
    }
  },
  exportIfc: async (options) => {
    try {
      set({ exporting: true, exportProgress: 0, progressMessage: "Starting export...", error: undefined });
      checkAgentConnected();

      const result = await ifcExport(
        {
          buildingPath: options?.filename || "building",
          format: "ifc",
        },
        (progress, message) => {
          set({ exportProgress: progress, progressMessage: message });
        }
      );

      if (!result.success) {
        throw new Error("IFC export failed");
      }

      const downloadUrl = result.base64Data
        ? base64ToBlobUri(result.base64Data)
        : result.filePath || "";

      set({
        exporting: false,
        exportProgress: 100,
        progressMessage: "Export complete!",
        lastExport: {
          filename: options?.filename || "building.ifc",
          sizeBytes: result.size,
          downloadUrl,
        },
      });
    } catch (error) {
      set({ exporting: false, exportProgress: 0, progressMessage: "", error: (error as Error).message });
    }
  },
  clearError: () => set({ error: undefined })
}));
