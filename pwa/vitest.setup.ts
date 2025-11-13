const storage: Record<string, string> = {};

Object.defineProperty(global, "localStorage", {
  value: {
    getItem: (key: string) => storage[key] ?? null,
    setItem: (key: string, value: string) => {
      storage[key] = value;
    },
    removeItem: (key: string) => {
      delete storage[key];
    },
    clear: () => {
      for (const key of Object.keys(storage)) {
        delete storage[key];
      }
    }
  },
  writable: false
});

if (typeof HTMLCanvasElement !== "undefined") {
  const mockContext: Partial<CanvasRenderingContext2D> = {
    fillRect: () => undefined,
    clearRect: () => undefined,
    beginPath: () => undefined,
    arc: () => undefined,
    fill: () => undefined,
    stroke: () => undefined,
    lineTo: () => undefined,
    moveTo: () => undefined,
    fillText: () => undefined,
    strokeStyle: "#000",
    fillStyle: "#000",
    lineWidth: 1,
    font: "12px sans-serif"
  };

  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    configurable: true,
    writable: true,
    value: () => mockContext as CanvasRenderingContext2D
  });
}

import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import "fake-indexeddb/auto";

afterEach(() => {
  cleanup();
});

// Mock @arxos-wasm module for tests
vi.mock("@arxos-wasm", () => ({
  default: () => Promise.resolve(),
  arxos_version: () => "2.0.0",
  parse_ar_scan: (json: string) => {
    const data = JSON.parse(json);
    if (!data.detectedEquipment || !data.roomBoundaries) {
      throw new Error("Invalid AR scan data");
    }
    return data;
  },
  extract_equipment: (json: string) => {
    const data = JSON.parse(json);
    return data.detectedEquipment || [];
  },
  generate_scan_mesh: (json: string) => {
    const data = JSON.parse(json);
    return {
      wallPositions: [],
      equipmentPositions: [],
      pointCloudPositions: [],
      boundsMin: [0, 0, 0],
      boundsMax: [10, 10, 10],
      ...data,
    };
  },
  validate_ar_scan: (json: string) => {
    try {
      const data = JSON.parse(json);
      return !!(data.detectedEquipment && data.roomBoundaries);
    } catch {
      return false;
    }
  },
  command_palette: () =>
    Promise.resolve([
      {
        name: "version",
        command: "version",
        description: "Show ArxOS version",
        category: { slug: "system", label: "System" },
        shortcut: null,
        tags: ["info"],
        availability: { cli: true, pwa: true, agent: true },
      },
      {
        name: "status",
        command: "arxos status",
        description: "Show repository status",
        category: { slug: "git", label: "Git" },
        shortcut: null,
        tags: ["git"],
        availability: { cli: true, pwa: true, agent: true },
      },
    ]),
  command_categories: () =>
    Promise.resolve([
      { slug: "building", label: "Building" },
      { slug: "git", label: "Git" },
      { slug: "ar", label: "AR" },
      { slug: "system", label: "System" },
    ]),
  command_details: (name: string) => {
    if (name === "version") {
      return Promise.resolve({
        name: "version",
        command: "version",
        description: "Show ArxOS version",
        category: { slug: "system", label: "System" },
        shortcut: null,
        tags: ["info"],
        availability: { cli: true, pwa: true, agent: true },
      });
    }
    return Promise.reject(new Error("Command not found"));
  },
}));
