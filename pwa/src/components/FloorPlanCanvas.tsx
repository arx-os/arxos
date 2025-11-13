import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  extractEquipmentFromScan,
  initWasm,
  parseArScan,
  validateArScan,
  type WasmArScanData,
  type WasmOpening,
  type WasmWall
} from "../lib/wasm";
import { useViewerStore } from "../state/viewer";
import { get, set as setKeyVal } from "idb-keyval";

const FLOOR_PLAN_STORAGE_KEY = "arxos-floor-plan-scan-input";

const canUseLocalStorage = () => {
  try {
    if (typeof window === "undefined" || !("localStorage" in window)) {
      return false;
    }
    const testKey = "__arxos_test";
    window.localStorage.setItem(testKey, "1");
    window.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
};

const loadStoredScan = async () => {
  if (typeof indexedDB === "undefined") {
    if (canUseLocalStorage()) {
      return window.localStorage.getItem(FLOOR_PLAN_STORAGE_KEY);
    }
    return null;
  }
  return get<string>(FLOOR_PLAN_STORAGE_KEY);
};

const persistStoredScan = async (value: string) => {
  if (typeof indexedDB === "undefined") {
    if (canUseLocalStorage()) {
      window.localStorage.setItem(FLOOR_PLAN_STORAGE_KEY, value);
    }
    return;
  }
  await setKeyVal(FLOOR_PLAN_STORAGE_KEY, value);
};

export type EquipmentPoint = {
  x: number;
  y: number;
  label: string;
};

type WallSegment = {
  start: { x: number; y: number };
  end: { x: number; y: number };
};

type Opening = {
  position: { x: number; y: number };
  width: number;
  height: number;
  type?: string;
};

type LayoutState = {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  walls: WallSegment[];
  openings: Opening[];
};

const createDefaultLayout = (): LayoutState => ({
  minX: 0,
  maxX: 18,
  minY: 0,
  maxY: 12,
  walls: [],
  openings: []
});

const SAMPLE_SCAN = JSON.stringify(
  {
    detectedEquipment: [
      {
        name: "VAV-301",
        type: "HVAC",
        position: { x: 10.5, y: 8.2, z: 2.7 },
        confidence: 0.95,
        detectionMethod: "ARKit"
      },
      {
        name: "Light-301",
        type: "Lighting",
        position: { x: 12.0, y: 6.5, z: 2.9 },
        confidence: 0.87,
        detectionMethod: "ARKit"
      }
    ],
    roomBoundaries: {
      walls: [
        { startPoint: { x: 0, y: 0, z: 0 }, endPoint: { x: 18, y: 0, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 18, y: 0, z: 0 }, endPoint: { x: 18, y: 12, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 18, y: 12, z: 0 }, endPoint: { x: 0, y: 12, z: 0 }, height: 3, thickness: 0.2 },
        { startPoint: { x: 0, y: 12, z: 0 }, endPoint: { x: 0, y: 0, z: 0 }, height: 3, thickness: 0.2 }
      ],
      openings: [{ position: { x: 9, y: 0, z: 0 }, width: 1.2, height: 2.1, type: "door" }]
    }
  },
  null,
  2
);

function deriveLayout(data: WasmArScanData, equipment: EquipmentPoint[]): LayoutState {
  let minX = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;

  const track = (x?: number | null, y?: number | null) => {
    if (typeof x !== "number" || typeof y !== "number") {
      return;
    }
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  };

  const wallsSource: WasmWall[] = data.roomBoundaries?.walls ?? [];
  const openingsSource: WasmOpening[] = data.roomBoundaries?.openings ?? [];

  const walls: WallSegment[] = wallsSource.map((wall) => {
    track(wall.startPoint.x, wall.startPoint.y);
    track(wall.endPoint.x, wall.endPoint.y);
    return {
      start: { x: wall.startPoint.x, y: wall.startPoint.y },
      end: { x: wall.endPoint.x, y: wall.endPoint.y }
    };
  });

  const openings: Opening[] = openingsSource.map((opening) => {
    track(opening.position.x, opening.position.y);
    return {
      position: { x: opening.position.x, y: opening.position.y },
      width: opening.width,
      height: opening.height,
      type: opening.type
    };
  });

  equipment.forEach((item) => track(item.x, item.y));

  if (minX === Number.POSITIVE_INFINITY || minY === Number.POSITIVE_INFINITY) {
    return createDefaultLayout();
  }

  const padding = 1;
  return {
    minX: minX - padding,
    maxX: maxX + padding,
    minY: minY - padding,
    maxY: maxY + padding,
    walls,
    openings
  };
}

export default function FloorPlanCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [scanInput, setScanInput] = useState<string>(SAMPLE_SCAN);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("Paste AR scan JSON or edit the sample to render.");
  const [validationState, setValidationState] = useState<"idle" | "valid" | "invalid">("idle");
  const [loading, setLoading] = useState(false);
  const [equipment, setEquipment] = useState<EquipmentPoint[]>([]);
  const [layout, setLayout] = useState<LayoutState>(() => createDefaultLayout());
  const [hydrated, setHydrated] = useState(false);

  const worldSize = useMemo(() => {
    const width = Math.max(layout.maxX - layout.minX, 1);
    const height = Math.max(layout.maxY - layout.minY, 1);
    return { width, height };
  }, [layout.maxX, layout.minX, layout.maxY, layout.minY]);

  const renderScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await initWasm();
      const isValid = await validateArScan(scanInput);
      setValidationState(isValid ? "valid" : "invalid");
      if (!isValid) {
        setEquipment([]);
        setLayout(createDefaultLayout());
        setStatus("Scan failed validation. Please review the JSON payload.");
        return;
      }

      const parsed = await parseArScan(scanInput);
      setLayout(deriveLayout(parsed, equipment));
      const equipmentList = await extractEquipmentFromScan(scanInput);
      setEquipment(equipmentList.map((item) => ({
        x: item.position.x,
        y: item.position.y,
        label: item.name
      })));
      setValidationState("valid");
      setStatus(
        `Rendered ${equipmentList.length} equipment points with ${parsed.roomBoundaries.walls.length} walls.`
      );
      void useViewerStore.getState().updateFromScan(scanInput);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setStatus("Unable to render AR scan");
      setValidationState("invalid");
    } finally {
      setLoading(false);
    }
  }, [scanInput, equipment]);

  const loadSample = useCallback(() => {
    setScanInput(SAMPLE_SCAN);
    setStatus("Loaded sample scan.");
    setValidationState("idle");
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const saved = await loadStoredScan();
        if (!cancelled && saved) {
          setScanInput(saved);
          setStatus("Loaded scan from previous session.");
        }
      } catch (error) {
        console.warn("Unable to load floor plan state", error);
      } finally {
        if (!cancelled) {
          setHydrated(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    void persistStoredScan(scanInput).catch((error) => {
      console.warn("Failed to persist floor plan state", error);
    });
  }, [scanInput, hydrated]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    void renderScan();
  }, [renderScan, hydrated]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    const { width, height } = canvas;
    const padding = 36;
    const scaleX = (width - padding * 2) / worldSize.width;
    const scaleY = (height - padding * 2) / worldSize.height;
    const maxY = layout.maxY;

    const toCanvasX = (value: number) => padding + (value - layout.minX) * scaleX;
    const toCanvasY = (value: number) => padding + (maxY - value) * scaleY;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, width, height);

    // Grid
    ctx.strokeStyle = "rgba(148, 163, 184, 0.15)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= worldSize.width; x++) {
      const posX = padding + x * scaleX;
      ctx.beginPath();
      ctx.moveTo(posX, padding);
      ctx.lineTo(posX, height - padding);
      ctx.stroke();
    }
    for (let y = 0; y <= worldSize.height; y++) {
      const posY = padding + y * scaleY;
      ctx.beginPath();
      ctx.moveTo(padding, posY);
      ctx.lineTo(width - padding, posY);
      ctx.stroke();
    }

    // Walls
    ctx.strokeStyle = "rgba(56, 189, 248, 0.7)";
    ctx.lineWidth = 3;
    layout.walls.forEach((wall) => {
      ctx.beginPath();
      ctx.moveTo(toCanvasX(wall.start.x), toCanvasY(wall.start.y));
      ctx.lineTo(toCanvasX(wall.end.x), toCanvasY(wall.end.y));
      ctx.stroke();
    });

    // Openings
    ctx.strokeStyle = "rgba(251, 191, 36, 0.7)";
    ctx.lineWidth = 2;
    layout.openings.forEach((opening) => {
      const startX = toCanvasX(opening.position.x) - (opening.width * scaleX) / 2;
      const endX = toCanvasX(opening.position.x) + (opening.width * scaleX) / 2;
      const y = toCanvasY(opening.position.y);
      ctx.beginPath();
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
      ctx.stroke();
    });

    // Equipment
    equipment.forEach((item) => {
      const x = toCanvasX(item.x);
      const y = toCanvasY(item.y);
      ctx.fillStyle = "#38bdf8";
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "12px 'Inter', sans-serif";
      ctx.fillText(item.label, x + 10, y - 10);
    });
  }, [equipment, layout, worldSize.height, worldSize.width]);

  return (
    <div
      className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-inner shadow-slate-950/40"
      data-testid="panel-floor-plan"
    >
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Floor Plan Studio</h3>
          <p className="text-xs text-slate-400">
            Parse AR scan JSON, validate via WASM, and render a 2D projection of equipment.
          </p>
        </div>
        <span className="rounded-md border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
          Canvas prototype
        </span>
      </div>

      <div className="mb-4 grid gap-4 md:grid-cols-[minmax(0,1fr),240px]">
        <textarea
          value={scanInput}
          onChange={(event) => setScanInput(event.target.value)}
          rows={12}
          className="w-full resize-y rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
        />
        <div className="flex flex-col gap-3 text-xs text-slate-300">
          <button
            onClick={() => void renderScan()}
            disabled={loading}
            className="rounded-lg border border-sky-700 bg-sky-600/20 px-3 py-2 text-xs font-medium uppercase tracking-wide text-sky-200 transition hover:bg-sky-600/30 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Rendering..." : "Validate & Render"}
          </button>
          <button
            onClick={loadSample}
            className="rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-200 transition hover:bg-slate-800"
          >
            Load Sample Scan
          </button>
          <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3">
            <p className="font-semibold text-slate-200">Status</p>
            <p className="mt-1 text-slate-400">{status}</p>
            <p className="mt-2 text-[10px] uppercase tracking-wide text-slate-500">
              Validation: {validationState === "idle" ? "Not run" : validationState === "valid" ? "Valid" : "Invalid"}
            </p>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
          {error}
        </div>
      ) : (
        <canvas
          ref={canvasRef}
          width={720}
          height={420}
          className="w-full rounded-lg border border-slate-800 bg-slate-950"
        />
      )}
    </div>
  );
}

