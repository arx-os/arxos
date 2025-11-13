import { useEffect, useState } from "react";
import { useCommandPaletteStore } from "./state/commandPalette";
import CommandPalette from "./components/CommandPalette";
import CommandConsole from "./components/CommandConsole";
import FloorPlanCanvas from "./components/FloorPlanCanvas";
import CollaborationPanel from "./components/CollaborationPanel";
import IfcPanel from "./components/IfcPanel";
import ArPreview from "./components/ArPreview";
import WebGlViewer from "./components/WebGlViewer";
import { FloorViewer } from "./modules/floor";
import { AuthModal, ConnectionIndicator, useAuthStore, useAgentStore } from "./modules/agent";
import { GitPanel } from "./modules/git/components";
import {
  SyncCoordinator,
  OfflineIndicator,
  SyncStatusToast,
  ConflictDialog
} from "./modules/offline";

export default function App() {
  const { hydrate } = useCommandPaletteStore();
  const disableWebGl = import.meta.env.VITE_DISABLE_WEBGL === "1";
  const [showFloorViewer, setShowFloorViewer] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const { isAuthenticated } = useAuthStore();
  const { isInitialized } = useAgentStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Show auth modal if not authenticated
  useEffect(() => {
    if (!isAuthenticated && !isInitialized) {
      setShowAuthModal(true);
    }
  }, [isAuthenticated, isInitialized]);

  // Add keyboard shortcut to toggle floor viewer
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "f" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setShowFloorViewer((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold tracking-wide text-sky-300">ArxOS PWA</h1>
            <p className="text-sm text-slate-400">
              Rust-powered building version control – now in your browser.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionIndicator />
            <CommandPalette />
          </div>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-1 flex-col gap-6 overflow-y-auto px-6 py-10">
        <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/50">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-100">Welcome</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">
                This workspace is the foundation for the WASM-first ArxOS experience. It connects to
                Rust logic compiled to WebAssembly, manages state with Zustand, and progressively
                enhances capabilities via service workers and a companion desktop agent.
              </p>
            </div>
            <button
              onClick={() => setShowFloorViewer(true)}
              className="ml-4 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
            >
              Open Floor Viewer
            </button>
          </div>
        </section>

        <FloorPlanCanvas />
        <CollaborationPanel />

        {/* Git UI */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/70 shadow-lg shadow-slate-900/50 overflow-hidden">
          <div className="h-[600px]">
            <GitPanel />
          </div>
        </section>

        {!disableWebGl && <WebGlViewer />}
        <IfcPanel />
        <ArPreview />

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
            <h3 className="text-sm font-semibold text-slate-100">Command Palette-first</h3>
            <p className="mt-2 text-xs text-slate-400">
              Mirror the terminal workflow with keyboard-driven commands. Palette data is sourced
              from Rust via the WASM bindings.
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
            <h3 className="text-sm font-semibold text-slate-100">Zustand Global State</h3>
            <p className="mt-2 text-xs text-slate-400">
              Lightweight stores manage palette history, offline queue metadata, and user context.
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
            <h3 className="text-sm font-semibold text-slate-100">Agent Bridge Ready</h3>
            <p className="mt-2 text-xs text-slate-400">
              Designed to connect with the desktop companion for Git, IFC, and workspace file ops
              over a secure WebSocket channel.
            </p>
          </div>
        </section>
      </main>

      <CommandConsole />

      {/* Floor Viewer - Full screen overlay */}
      {showFloorViewer && (
        <div className="fixed inset-0 z-50 bg-slate-950">
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={() => setShowFloorViewer(false)}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg border border-slate-700 transition-colors"
            >
              Close (Cmd/Ctrl+F)
            </button>
          </div>
          <FloorViewer />
        </div>
      )}

      {/* Agent Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={() => {
          setShowAuthModal(false);
        }}
      />

      {/* Offline-First Sync System */}
      <SyncCoordinator />
      <OfflineIndicator />
      <SyncStatusToast />
      <ConflictDialog />
    </div>
  );
}

