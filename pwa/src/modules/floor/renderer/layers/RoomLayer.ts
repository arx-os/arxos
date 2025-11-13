import type { Layer, RenderContext, Room } from "../../types";
import { COLORS, worldToScreen } from "../../types";

export class RoomLayer implements Layer {
  type: "rooms" = "rooms";
  visible = true;
  private rooms: Room[] = [];

  setRooms(rooms: Room[]): void {
    this.rooms = rooms;
  }

  render(context: RenderContext): void {
    if (!this.visible || this.rooms.length === 0) return;

    const { ctx, viewport, canvasWidth, canvasHeight, selection, hoveredElement } = context;

    for (const room of this.rooms) {
      const isSelected = selection?.type === "room" && selection.id === room.id;
      const isHovered = hoveredElement?.type === "room" && hoveredElement.id === room.id;

      this.renderRoom(room, context, isSelected, isHovered);
    }
  }

  private renderRoom(
    room: Room,
    context: RenderContext,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    // Determine room color based on room type
    const fillColor = this.getRoomColor(room.room_type);
    const alpha = isSelected ? 0.6 : isHovered ? 0.4 : 0.3;

    // Use polygon if available, otherwise use bounding box
    if (room.polygon && room.polygon.length > 0) {
      this.renderPolygon(room.polygon, context, fillColor, alpha, isSelected, isHovered);
    } else {
      this.renderBoundingBox(room.bounds, context, fillColor, alpha, isSelected, isHovered);
    }

    // Render room label
    this.renderRoomLabel(room, context);
  }

  private renderPolygon(
    polygon: Array<{ x: number; y: number }>,
    context: RenderContext,
    fillColor: string,
    alpha: number,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    if (polygon.length < 3) return;

    // Convert polygon to screen coordinates
    const screenPoints = polygon.map((point) =>
      worldToScreen(point, viewport, canvasWidth, canvasHeight)
    );

    // Draw filled polygon
    ctx.beginPath();
    ctx.moveTo(screenPoints[0].x, screenPoints[0].y);
    for (let i = 1; i < screenPoints.length; i++) {
      ctx.lineTo(screenPoints[i].x, screenPoints[i].y);
    }
    ctx.closePath();

    // Fill with transparency
    ctx.fillStyle = this.hexToRgba(fillColor, alpha);
    ctx.fill();

    // Stroke outline
    if (isSelected) {
      ctx.strokeStyle = COLORS.selection;
      ctx.lineWidth = 3;
    } else if (isHovered) {
      ctx.strokeStyle = COLORS.hover;
      ctx.lineWidth = 2;
    } else {
      ctx.strokeStyle = fillColor;
      ctx.lineWidth = 1;
    }
    ctx.stroke();
  }

  private renderBoundingBox(
    bounds: { min: { x: number; y: number }; max: { x: number; y: number } },
    context: RenderContext,
    fillColor: string,
    alpha: number,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    const topLeft = worldToScreen(
      { x: bounds.min.x, y: bounds.min.y },
      viewport,
      canvasWidth,
      canvasHeight
    );
    const bottomRight = worldToScreen(
      { x: bounds.max.x, y: bounds.max.y },
      viewport,
      canvasWidth,
      canvasHeight
    );

    const width = bottomRight.x - topLeft.x;
    const height = bottomRight.y - topLeft.y;

    // Fill rectangle
    ctx.fillStyle = this.hexToRgba(fillColor, alpha);
    ctx.fillRect(topLeft.x, topLeft.y, width, height);

    // Stroke outline
    if (isSelected) {
      ctx.strokeStyle = COLORS.selection;
      ctx.lineWidth = 3;
    } else if (isHovered) {
      ctx.strokeStyle = COLORS.hover;
      ctx.lineWidth = 2;
    } else {
      ctx.strokeStyle = fillColor;
      ctx.lineWidth = 1;
    }
    ctx.strokeRect(topLeft.x, topLeft.y, width, height);
  }

  private renderRoomLabel(room: Room, context: RenderContext): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    // Calculate room center
    const centerX = (room.bounds.min.x + room.bounds.max.x) / 2;
    const centerY = (room.bounds.min.y + room.bounds.max.y) / 2;

    const screenPos = worldToScreen(
      { x: centerX, y: centerY },
      viewport,
      canvasWidth,
      canvasHeight
    );

    // Draw room name
    ctx.fillStyle = COLORS.text;
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    // Draw background for better readability
    const textMetrics = ctx.measureText(room.name);
    const padding = 4;
    ctx.fillStyle = "rgba(15, 23, 42, 0.8)"; // COLORS.background with alpha
    ctx.fillRect(
      screenPos.x - textMetrics.width / 2 - padding,
      screenPos.y - 8,
      textMetrics.width + padding * 2,
      16
    );

    // Draw text
    ctx.fillStyle = COLORS.text;
    ctx.fillText(room.name, screenPos.x, screenPos.y);

    // Draw room type below (if different from name)
    if (room.room_type && room.room_type !== room.name) {
      ctx.font = "10px sans-serif";
      ctx.fillStyle = this.hexToRgba(COLORS.text, 0.7);
      ctx.fillText(room.room_type, screenPos.x, screenPos.y + 12);
    }
  }

  private getRoomColor(roomType: string): string {
    const type = roomType.toLowerCase();

    if (type.includes("mech") || type.includes("hvac")) {
      return COLORS.room.mech;
    }
    if (type.includes("elec") || type.includes("electric")) {
      return COLORS.room.elec;
    }
    if (type.includes("plumb") || type.includes("water")) {
      return COLORS.room.plumb;
    }
    if (type.includes("office") || type.includes("workspace")) {
      return COLORS.room.office;
    }

    return COLORS.room.default;
  }

  private hexToRgba(hex: string, alpha: number): string {
    // Convert hex to RGB
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}
