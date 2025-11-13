import type { BoundingBox, Coordinate, Viewport } from "../types";
import { calculateBoundsCenter, calculateBoundsSize } from "../types";

export class Camera {
  private viewport: Viewport;
  private minZoom = 0.1;
  private maxZoom = 10;
  private isDragging = false;
  private dragStart: { x: number; y: number } | null = null;

  constructor(bounds: BoundingBox, initialZoom = 1) {
    this.viewport = {
      pan: { x: 0, y: 0 },
      zoom: initialZoom,
      bounds,
    };
  }

  getViewport(): Viewport {
    return { ...this.viewport };
  }

  setZoom(zoom: number): void {
    this.viewport.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
  }

  zoom(delta: number, centerX?: number, centerY?: number): void {
    const oldZoom = this.viewport.zoom;
    const newZoom = oldZoom * (1 + delta);
    this.setZoom(newZoom);

    // If zoom center is provided, adjust pan to zoom toward that point
    if (centerX !== undefined && centerY !== undefined) {
      const zoomRatio = this.viewport.zoom / oldZoom;
      this.viewport.pan.x = centerX + (this.viewport.pan.x - centerX) * zoomRatio;
      this.viewport.pan.y = centerY + (this.viewport.pan.y - centerY) * zoomRatio;
    }
  }

  zoomIn(): void {
    this.zoom(0.2);
  }

  zoomOut(): void {
    this.zoom(-0.2);
  }

  pan(deltaX: number, deltaY: number): void {
    this.viewport.pan.x += deltaX / this.viewport.zoom;
    this.viewport.pan.y += deltaY / this.viewport.zoom;
  }

  setPan(x: number, y: number): void {
    this.viewport.pan = { x, y };
  }

  fitToView(canvasWidth: number, canvasHeight: number, padding = 0.9): void {
    const boundsSize = calculateBoundsSize(this.viewport.bounds);

    // Calculate zoom to fit the bounds with padding
    const zoomX = (canvasWidth * padding) / boundsSize.width;
    const zoomY = (canvasHeight * padding) / boundsSize.height;
    const zoom = Math.min(zoomX, zoomY);

    this.setZoom(zoom);
    this.setPan(0, 0);
  }

  resetView(): void {
    this.setPan(0, 0);
    this.setZoom(1);
  }

  startDrag(screenX: number, screenY: number): void {
    this.isDragging = true;
    this.dragStart = { x: screenX, y: screenY };
  }

  drag(screenX: number, screenY: number): void {
    if (!this.isDragging || !this.dragStart) return;

    const deltaX = screenX - this.dragStart.x;
    const deltaY = screenY - this.dragStart.y;

    this.pan(deltaX, deltaY);

    this.dragStart = { x: screenX, y: screenY };
  }

  endDrag(): void {
    this.isDragging = false;
    this.dragStart = null;
  }

  isPointInBounds(worldCoord: Coordinate): boolean {
    const { min, max } = this.viewport.bounds;
    return (
      worldCoord.x >= min.x &&
      worldCoord.x <= max.x &&
      worldCoord.y >= min.y &&
      worldCoord.y <= max.y
    );
  }
}
