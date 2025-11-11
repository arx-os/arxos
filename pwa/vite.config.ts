import path from "node:path";
import { defineConfig } from "vite";
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
    exclude: ["@arxos-wasm"]
  },
  worker: {
    format: "es"
  }
});

