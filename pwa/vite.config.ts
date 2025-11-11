import path from "node:path";
import { defineConfig } from "vite";
import { configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@arxos-wasm": path.resolve(__dirname, "../crates/arxos-wasm/pkg/arxos_wasm.js")
    }
  },
  build: {
    target: "esnext",
    sourcemap: true
  },
  optimizeDeps: {
    exclude: ["@arxos-wasm"],
    include: ["three"]
  },
  worker: {
    format: "es"
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./vitest.setup.ts",
    coverage: {
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"]
    },
    exclude: [...configDefaults.exclude, "tests/e2e/**"]
  }
});

