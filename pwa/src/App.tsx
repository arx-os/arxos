import { useEffect } from "react";
import { useCommandPaletteStore } from "./state/commandPalette";
import CommandPalette from "./components/CommandPalette";
import FloorPlanCanvas from "./components/FloorPlanCanvas";
import CollaborationPanel from "./components/CollaborationPanel";
import GitStatusPanel from "./components/GitStatusPanel";
import IfcPanel from "./components/IfcPanel";
import ArPreview from "./components/ArPreview";
import WebGlViewer from "./components/WebGlViewer";

export default function App() {
  const { hydrate } = useCommandPaletteStore();
  const disableWebGl = import.meta.env.VITE_DISABLE_WEBGL === "1";

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold tracking-wide text-sky-300">ArxOS PWA</h1>
            <p className="text-sm text-slate-400">
              Rust-powered building version control – now in your browser.
            </p>
          </div>
          <CommandPalette />
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10">
        <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-slate-900/50">
          <h2 className="text-base font-semibold text-slate-100">Welcome</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">
            This workspace is the foundation for the WASM-first ArxOS experience. It connects to
            Rust logic compiled to WebAssembly, manages state with Zustand, and progressively
            enhances capabilities via service workers and a companion desktop agent.
          </p>
        </section>

        <FloorPlanCanvas />
        <CollaborationPanel />
        <GitStatusPanel />
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
    </div>
  );
}

