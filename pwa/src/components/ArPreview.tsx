import { useCallback, useEffect, useState } from "react";

type XRNavigator = Navigator & { xr?: XRSystem };

export default function ArPreview() {
  const [supportState, setSupportState] = useState<"checking" | "supported" | "unsupported">(
    "checking"
  );
  const [sessionActive, setSessionActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overlayReady, setOverlayReady] = useState(false);
  const [knownIssues, setKnownIssues] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function checkSupport() {
      const xr = (navigator as XRNavigator).xr;
      if (!xr) {
        setSupportState("unsupported");
        return;
      }

      try {
        const supported = await xr.isSessionSupported?.("immersive-ar");
        if (!cancelled) {
          setSupportState(supported ? "supported" : "unsupported");
        }
      } catch (err) {
        console.warn("WebXR detection failed", err);
        if (!cancelled) {
          setSupportState("unsupported");
        }
      }
    }

    void checkSupport();
    return () => {
      cancelled = true;
    };
  }, []);

  const startSession = useCallback(async () => {
    setError(null);
    const xr = (navigator as XRNavigator).xr;
    if (!xr || supportState !== "supported") {
      setError("WebXR AR sessions are not supported in this browser.");
      return;
    }

    try {
      const init: XRSessionInit = {
        requiredFeatures: [],
        optionalFeatures: ["dom-overlay"],
        domOverlay: { root: document.body }
      };
      const session = await xr.requestSession("immersive-ar", init);
      setSessionActive(true);
      session.addEventListener(
        "end",
        () => {
          setSessionActive(false);
          setOverlayReady(false);
        },
        { once: true }
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || "Failed to start AR session");
      setSessionActive(false);
    }
  }, [supportState]);

  const loadDemoOverlay = useCallback(async () => {
    try {
      const response = await fetch("/offline-demo/ar-overlay.json", { cache: "no-cache" });
      if (!response.ok) {
        throw new Error(`Unexpected response ${response.status}`);
      }
      const payload = await response.json();
      setOverlayReady(true);
      setKnownIssues(
        Array.isArray(payload?.issues)
          ? (payload.issues as string[])
          : ["Chrome Canary 128 crashes when DOM overlay unused.", "Safari 17.0 fails on first launch."]
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(`Failed to load demo overlay: ${message}`);
    }
  }, []);

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-lg shadow-slate-900/40">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">AR Overlay Preview</h3>
          <p className="text-xs text-slate-400">
            Detect immersive AR support, load a demo overlay, and initiate a browser-native session
            when available.
          </p>
        </div>
        <span
          className={`rounded-md px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-100 ${
            supportState === "supported"
              ? "bg-emerald-500/50"
              : supportState === "checking"
              ? "bg-amber-500/40"
              : "bg-slate-700/60"
          }`}
        >
          {supportState === "supported"
            ? "WebXR Ready"
            : supportState === "checking"
            ? "Checking"
            : "Unsupported"}
        </span>
      </header>

      <p className="text-xs text-slate-300">
        When immersive AR is supported, the PWA can project scan overlays on top of the real world
        without launching a native app. We use the same Rust scan parsers to prepare the data before
        sending it to the browser session.
      </p>

      <div className="mt-4 flex flex-col gap-2 text-xs text-slate-200">
        <button
          onClick={() => void loadDemoOverlay()}
          disabled={supportState !== "supported"}
          className="w-full rounded-md border border-emerald-700 bg-emerald-600/20 px-3 py-2 font-medium uppercase tracking-wide text-emerald-200 transition hover:bg-emerald-600/30 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {overlayReady ? "Demo Overlay Loaded" : "Load Demo Overlay"}
        </button>
        <button
          onClick={() => void startSession()}
          disabled={supportState !== "supported"}
          className="w-full rounded-md border border-sky-700 bg-sky-600/20 px-3 py-2 font-medium uppercase tracking-wide text-sky-200 transition hover:bg-sky-600/30 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {sessionActive ? "Session Active" : "Start AR Session"}
        </button>
        {error && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-[11px] text-red-200">
            {error}
          </div>
        )}
        {knownIssues.length > 0 && (
          <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200">
            <p className="font-semibold uppercase tracking-wide text-amber-300">Known Issues</p>
            <ul className="mt-1 list-disc pl-4 text-amber-200/80">
              {knownIssues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          </div>
        )}
        <ul className="list-disc pl-5 text-[11px] text-slate-400">
          <li>Chrome (Android) and Safari (iOS 17+) are the primary targets for immersive-ar.</li>
          <li>Ensure `chrome://flags/#webxr-incubations` or Safari experimental AR features are enabled.</li>
          <li>
            When the desktop agent is connected, scanned anchors can stream from the local workspace
            into the session.
          </li>
        </ul>
      </div>
    </section>
  );
}
