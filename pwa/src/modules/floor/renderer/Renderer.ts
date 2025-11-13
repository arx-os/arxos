import type { Floor, Selection } from "../types";
import { COLORS } from "../types";
import { Camera } from "./Camera";
import { SceneGraph } from "./SceneGraph";
import { GridLayer } from "./layers/GridLayer";
import { RoomLayer } from "./layers/RoomLayer";
import { EquipmentLayer } from "./layers/EquipmentLayer";

export class Renderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private camera: Camera;
  private sceneGraph: SceneGraph;
  private floor: Floor | null = null;
  private selection: Selection | null = null;
  private hoveredElement: Selection | null = null;
  private animationFrameId: number | null = null;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Failed to get 2D context from canvas");
    }
    this.ctx = ctx;

    // Initialize with default bounds (will be updated when floor is loaded)
    this.camera = new Camera(
      {
        min: { x: 0, y: 0 },
        max: { x: 20, y: 20 },
      },
      1
    );

    this.sceneGraph = new SceneGraph();

    // Initialize layers
    this.sceneGraph.addLayer("grid", new GridLayer());
    this.sceneGraph.addLayer("rooms", new RoomLayer());
    this.sceneGraph.addLayer("equipment", new EquipmentLayer());

    // Start render loop
    this.startRenderLoop();
  }

  setFloor(floor: Floor): void {
    this.floor = floor;
    this.camera = new Camera(floor.bounds, 1);
    this.camera.fitToView(this.canvas.width, this.canvas.height);
    this.render();
  }

  getFloor(): Floor | null {
    return this.floor;
  }

  setSelection(selection: Selection | null): void {
    this.selection = selection;
    this.render();
  }

  getSelection(): Selection | null {
    return this.selection;
  }

  setHoveredElement(element: Selection | null): void {
    this.hoveredElement = element;
    this.render();
  }

  getCamera(): Camera {
    return this.camera;
  }

  getSceneGraph(): SceneGraph {
    return this.sceneGraph;
  }

  resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
    this.render();
  }

  fitToView(): void {
    this.camera.fitToView(this.canvas.width, this.canvas.height);
    this.render();
  }

  resetView(): void {
    this.camera.resetView();
    this.render();
  }

  toggleLayer(layerName: "grid" | "rooms" | "equipment"): void {
    this.sceneGraph.toggleLayer(layerName);
    this.render();
  }

  findElementAtPoint(screenX: number, screenY: number): Selection | null {
    if (!this.floor) return null;

    const worldCoord = this.screenToWorld(screenX, screenY);

    // Check equipment first (they have higher priority)
    const allEquipment = this.floor.rooms.flatMap((room) => room.equipment);
    const equipment = this.sceneGraph.findEquipmentAtPoint(
      allEquipment,
      worldCoord.x,
      worldCoord.y
    );
    if (equipment) return equipment;

    // Check rooms
    const room = this.sceneGraph.findRoomAtPoint(this.floor.rooms, worldCoord.x, worldCoord.y);
    if (room) return room;

    return null;
  }

  private screenToWorld(screenX: number, screenY: number): { x: number; y: number } {
    const viewport = this.camera.getViewport();
    const { zoom, pan } = viewport;

    const viewportCenterX = (viewport.bounds.min.x + viewport.bounds.max.x) / 2;
    const viewportCenterY = (viewport.bounds.min.y + viewport.bounds.max.y) / 2;

    const x = (screenX - this.canvas.width / 2) / zoom - pan.x + viewportCenterX;
    const y = (screenY - this.canvas.height / 2) / zoom - pan.y + viewportCenterY;

    return { x, y };
  }

  render(): void {
    // Clear canvas
    this.ctx.fillStyle = COLORS.background;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    if (!this.floor) {
      this.renderEmptyState();
      return;
    }

    // Update layer data
    const roomLayer = this.sceneGraph.getLayer("rooms") as RoomLayer;
    if (roomLayer) {
      roomLayer.setRooms(this.floor.rooms);
    }

    const equipmentLayer = this.sceneGraph.getLayer("equipment") as EquipmentLayer;
    if (equipmentLayer) {
      const allEquipment = this.floor.rooms.flatMap((room) => room.equipment);
      equipmentLayer.setEquipment(allEquipment);
    }

    // Prepare render context
    const renderContext = {
      ctx: this.ctx,
      viewport: this.camera.getViewport(),
      canvasWidth: this.canvas.width,
      canvasHeight: this.canvas.height,
      selection: this.selection,
      hoveredElement: this.hoveredElement,
    };

    // Render all layers through scene graph
    this.sceneGraph.render(renderContext);
  }

  private renderEmptyState(): void {
    this.ctx.fillStyle = COLORS.text;
    this.ctx.font = "16px sans-serif";
    this.ctx.textAlign = "center";
    this.ctx.textBaseline = "middle";
    this.ctx.fillText(
      "No floor loaded. Select a floor to view.",
      this.canvas.width / 2,
      this.canvas.height / 2
    );
  }

  private startRenderLoop(): void {
    const loop = () => {
      // Continuous render loop not needed for static scenes
      // We'll render on-demand via this.render()
      this.animationFrameId = requestAnimationFrame(loop);
    };
    // Don't start loop automatically - render on demand
  }

  destroy(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }
}
