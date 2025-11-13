/**
 * IFC import/export command handlers
 */

import { AgentClient } from "../client/AgentClient";

export interface IfcImportOptions {
  filePath?: string; // Optional: agent can provide file picker
  base64Data?: string; // Alternative: upload file as base64
}

export interface IfcImportResult {
  success: boolean;
  buildingPath: string;
  floorCount: number;
  roomCount: number;
  equipmentCount: number;
  yamlPath: string;
}

export interface IfcExportOptions {
  buildingPath: string;
  format: "yaml" | "gltf" | "usdz" | "ifc";
  scope?: {
    floors?: string[];
    rooms?: string[];
  };
}

export interface IfcExportResult {
  success: boolean;
  filePath?: string;
  base64Data?: string;
  size: number;
}

/**
 * Import IFC file and convert to YAML
 */
export async function ifcImport(
  options: IfcImportOptions,
  onProgress?: (progress: number, message: string) => void
): Promise<IfcImportResult> {
  const client = AgentClient.getInstance();

  // Generate request ID for streaming
  const requestId = `ifc-import-${Date.now()}`;

  // Subscribe to progress updates if callback provided
  if (onProgress) {
    client.onStream(requestId, (chunk, progress) => {
      onProgress(progress || 0, chunk);
    });
  }

  return client.send<IfcImportResult>("ifc.import", {
    ...options,
    requestId,
  });
}

/**
 * Export building data to various formats
 */
export async function ifcExport(
  options: IfcExportOptions,
  onProgress?: (progress: number, message: string) => void
): Promise<IfcExportResult> {
  const client = AgentClient.getInstance();

  const requestId = `ifc-export-${Date.now()}`;

  if (onProgress) {
    client.onStream(requestId, (chunk, progress) => {
      onProgress(progress || 0, chunk);
    });
  }

  return client.send<IfcExportResult>("ifc.export", {
    ...options,
    requestId,
  });
}

/**
 * List available IFC files in workspace
 */
export async function listIfcFiles(): Promise<Array<{
  path: string;
  name: string;
  size: number;
  lastModified: string;
}>> {
  const client = AgentClient.getInstance();
  return client.send("files.read", { pattern: "**/*.ifc" });
}
