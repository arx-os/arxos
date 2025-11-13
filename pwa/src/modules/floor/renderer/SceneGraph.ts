import type { Floor, Room, Equipment, Selection } from "../types";
import type { Layer, LayerVisibility, RenderContext } from "../types";

export class SceneGraph {
  private layers: Map<string, Layer> = new Map();
  private layerOrder: string[] = ["grid", "rooms", "equipment"];
  private visibility: LayerVisibility = {
    grid: true,
    rooms: true,
    equipment: true,
  };

  addLayer(name: string, layer: Layer): void {
    this.layers.set(name, layer);
  }

  removeLayer(name: string): void {
    this.layers.delete(name);
  }

  getLayer(name: string): Layer | undefined {
    return this.layers.get(name);
  }

  setLayerVisibility(name: keyof LayerVisibility, visible: boolean): void {
    this.visibility[name] = visible;
    const layer = this.layers.get(name);
    if (layer) {
      layer.visible = visible;
    }
  }

  toggleLayer(name: keyof LayerVisibility): void {
    this.setLayerVisibility(name, !this.visibility[name]);
  }

  getLayerVisibility(): LayerVisibility {
    return { ...this.visibility };
  }

  render(context: RenderContext): void {
    // Render layers in order
    for (const layerName of this.layerOrder) {
      const layer = this.layers.get(layerName);
      if (layer && layer.visible) {
        layer.render(context);
      }
    }
  }

  clear(): void {
    this.layers.clear();
  }

  // Helper methods for hit testing
  findRoomAtPoint(rooms: Room[], worldX: number, worldY: number): Selection | null {
    // Iterate in reverse order to prioritize top layers
    for (let i = rooms.length - 1; i >= 0; i--) {
      const room = rooms[i];
      if (this.isPointInRoom(room, worldX, worldY)) {
        return { type: "room", id: room.id };
      }
    }
    return null;
  }

  findEquipmentAtPoint(
    equipment: Equipment[],
    worldX: number,
    worldY: number,
    threshold = 0.5
  ): Selection | null {
    // Find closest equipment within threshold
    let closestEquipment: Equipment | null = null;
    let closestDistance = threshold;

    for (const equip of equipment) {
      const dx = equip.position.x - worldX;
      const dy = equip.position.y - worldY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < closestDistance) {
        closestDistance = distance;
        closestEquipment = equip;
      }
    }

    return closestEquipment ? { type: "equipment", id: closestEquipment.id } : null;
  }

  private isPointInRoom(room: Room, worldX: number, worldY: number): boolean {
    // Use polygon if available, otherwise use bounding box
    if (room.polygon && room.polygon.length > 0) {
      return this.isPointInPolygon(room.polygon, worldX, worldY);
    }

    // Fallback to bounding box check
    const { min, max } = room.bounds;
    return worldX >= min.x && worldX <= max.x && worldY >= min.y && worldY <= max.y;
  }

  private isPointInPolygon(
    polygon: Array<{ x: number; y: number }>,
    x: number,
    y: number
  ): boolean {
    // Ray casting algorithm
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].x;
      const yi = polygon[i].y;
      const xj = polygon[j].x;
      const yj = polygon[j].y;

      const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }
}
