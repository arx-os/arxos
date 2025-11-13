import type { BoundingBox, Coordinate, Equipment, Floor, Room } from "../../../lib/wasm/geometry";

export type { BoundingBox, Coordinate, Equipment, Floor, Room };

// Viewport and Camera types
export interface Viewport {
  pan: { x: number; y: number };
  zoom: number;
  bounds: BoundingBox;
}

export interface ViewportTransform {
  scale: number;
  translateX: number;
  translateY: number;
}

// Selection types
export type SelectionType = "room" | "equipment" | null;

export interface Selection {
  type: SelectionType;
  id: string;
}

// Layer types
export type LayerType = "grid" | "rooms" | "equipment";

export interface LayerVisibility {
  grid: boolean;
  rooms: boolean;
  equipment: boolean;
}

// Rendering types
export interface RenderContext {
  ctx: CanvasRenderingContext2D;
  viewport: Viewport;
  canvasWidth: number;
  canvasHeight: number;
  selection: Selection | null;
  hoveredElement: Selection | null;
}

export interface Layer {
  type: LayerType;
  visible: boolean;
  render(context: RenderContext): void;
}

// Color palette
export const COLORS = {
  background: "#0f172a", // slate-900
  grid: {
    major: "#1e293b", // slate-800
    minor: "#334155", // slate-700
  },
  room: {
    mech: "#dc2626", // red-600
    elec: "#2563eb", // blue-600
    plumb: "#16a34a", // green-600
    office: "#9333ea", // purple-600
    default: "#64748b", // slate-500
  },
  equipment: {
    hvac: "#f97316", // orange-500
    electrical: "#eab308", // yellow-500
    plumbing: "#06b6d4", // cyan-500
    default: "#8b5cf6", // violet-500
  },
  selection: "#22d3ee", // cyan-400
  hover: "#94a3b8", // slate-400
  text: "#e2e8f0", // slate-200
};

// Helper functions
export function worldToScreen(
  worldCoord: Coordinate,
  viewport: Viewport,
  canvasWidth: number,
  canvasHeight: number
): { x: number; y: number } {
  const { zoom, pan } = viewport;

  // Calculate the center of the viewport in world coordinates
  const viewportCenterX = (viewport.bounds.min.x + viewport.bounds.max.x) / 2;
  const viewportCenterY = (viewport.bounds.min.y + viewport.bounds.max.y) / 2;

  // Transform world coordinates to screen space
  const x = (worldCoord.x - viewportCenterX + pan.x) * zoom + canvasWidth / 2;
  const y = (worldCoord.y - viewportCenterY + pan.y) * zoom + canvasHeight / 2;

  return { x, y };
}

export function screenToWorld(
  screenX: number,
  screenY: number,
  viewport: Viewport,
  canvasWidth: number,
  canvasHeight: number
): Coordinate {
  const { zoom, pan } = viewport;

  const viewportCenterX = (viewport.bounds.min.x + viewport.bounds.max.x) / 2;
  const viewportCenterY = (viewport.bounds.min.y + viewport.bounds.max.y) / 2;

  const x = (screenX - canvasWidth / 2) / zoom - pan.x + viewportCenterX;
  const y = (screenY - canvasHeight / 2) / zoom - pan.y + viewportCenterY;

  return { x, y };
}

export function calculateBoundsCenter(bounds: BoundingBox): Coordinate {
  return {
    x: (bounds.min.x + bounds.max.x) / 2,
    y: (bounds.min.y + bounds.max.y) / 2,
  };
}

export function calculateBoundsSize(bounds: BoundingBox): { width: number; height: number } {
  return {
    width: bounds.max.x - bounds.min.x,
    height: bounds.max.y - bounds.min.y,
  };
}
