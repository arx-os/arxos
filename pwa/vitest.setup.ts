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
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});
