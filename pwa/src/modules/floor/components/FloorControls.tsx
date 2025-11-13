import { ZoomIn, ZoomOut, Maximize2, Grid, Box, Circle } from "lucide-react";
import type { LayerVisibility } from "../types";

interface FloorControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToView: () => void;
  onToggleLayer: (layer: keyof LayerVisibility) => void;
  layerVisibility: LayerVisibility;
}

export function FloorControls({
  onZoomIn,
  onZoomOut,
  onFitToView,
  onToggleLayer,
  layerVisibility,
}: FloorControlsProps) {
  return (
    <div className="absolute top-4 right-4 flex flex-col gap-2">
      {/* Zoom controls */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden">
        <button
          onClick={onZoomIn}
          className="w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors border-b border-slate-700"
          title="Zoom In"
        >
          <ZoomIn size={18} className="text-slate-300" />
        </button>
        <button
          onClick={onZoomOut}
          className="w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors border-b border-slate-700"
          title="Zoom Out"
        >
          <ZoomOut size={18} className="text-slate-300" />
        </button>
        <button
          onClick={onFitToView}
          className="w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors"
          title="Fit to View"
        >
          <Maximize2 size={18} className="text-slate-300" />
        </button>
      </div>

      {/* Layer toggles */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden">
        <button
          onClick={() => onToggleLayer("grid")}
          className={`w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors border-b border-slate-700 ${
            layerVisibility.grid ? "text-cyan-400" : "text-slate-500"
          }`}
          title="Toggle Grid"
        >
          <Grid size={18} />
        </button>
        <button
          onClick={() => onToggleLayer("rooms")}
          className={`w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors border-b border-slate-700 ${
            layerVisibility.rooms ? "text-cyan-400" : "text-slate-500"
          }`}
          title="Toggle Rooms"
        >
          <Box size={18} />
        </button>
        <button
          onClick={() => onToggleLayer("equipment")}
          className={`w-10 h-10 flex items-center justify-center hover:bg-slate-700 transition-colors ${
            layerVisibility.equipment ? "text-cyan-400" : "text-slate-500"
          }`}
          title="Toggle Equipment"
        >
          <Circle size={18} />
        </button>
      </div>
    </div>
  );
}
