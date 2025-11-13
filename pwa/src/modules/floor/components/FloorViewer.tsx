import { useState, useRef, useCallback } from "react";
import type { Floor, Selection, LayerVisibility } from "../types";
import { FloorCanvas } from "./FloorCanvas";
import { FloorControls } from "./FloorControls";
import { FloorSelector } from "./FloorSelector";
import { SelectionPanel } from "./SelectionPanel";
import type { Renderer } from "../renderer/Renderer";

export function FloorViewer() {
  const [floor, setFloor] = useState<Floor | null>(null);
  const [buildingPath, setBuildingPath] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    grid: true,
    rooms: true,
    equipment: true,
  });

  const rendererRef = useRef<Renderer | null>(null);

  const handleFloorSelect = useCallback((selectedFloor: Floor, path: string) => {
    setFloor(selectedFloor);
    setBuildingPath(path);
    setSelection(null);
  }, []);

  const handleSelectionChange = useCallback((newSelection: Selection | null) => {
    setSelection(newSelection);
  }, []);

  const handleZoomIn = useCallback(() => {
    if (rendererRef.current) {
      const camera = rendererRef.current.getCamera();
      camera.zoomIn();
      rendererRef.current.render();
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (rendererRef.current) {
      const camera = rendererRef.current.getCamera();
      camera.zoomOut();
      rendererRef.current.render();
    }
  }, []);

  const handleFitToView = useCallback(() => {
    if (rendererRef.current) {
      rendererRef.current.fitToView();
    }
  }, []);

  const handleToggleLayer = useCallback((layer: keyof LayerVisibility) => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layer]: !prev[layer],
    }));

    if (rendererRef.current) {
      rendererRef.current.toggleLayer(layer);
    }
  }, []);

  return (
    <div className="relative w-full h-full bg-slate-900">
      <FloorCanvas
        floor={floor}
        selection={selection}
        onSelectionChange={handleSelectionChange}
      />

      <FloorSelector
        onFloorSelect={handleFloorSelect}
        selectedFloorId={floor?.id || null}
      />

      <FloorControls
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitToView={handleFitToView}
        onToggleLayer={handleToggleLayer}
        layerVisibility={layerVisibility}
      />

      {selection && floor && (
        <SelectionPanel
          selection={selection}
          floor={floor}
          onClose={() => setSelection(null)}
        />
      )}
    </div>
  );
}
