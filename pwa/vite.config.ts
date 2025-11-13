import path from "node:path";
import { defineConfig } from "vite";
import { configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "robots.txt", "apple-touch-icon.png"],
      manifest: {
        name: "ArxOS PWA",
        short_name: "ArxOS",
        description: "Git-native building management",
        theme_color: "#0c4a6e",
        icons: [
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,wasm}"],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.*\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
            handler: "CacheFirst",
            options: {
              cacheName: "images-cache",
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
        ],
        // Enable background sync
        navigateFallback: null,
      },
      devOptions: {
        enabled: false, // Enable for testing in dev mode
      },
    }),
  ],
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

