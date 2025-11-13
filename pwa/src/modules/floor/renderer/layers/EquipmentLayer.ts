import type { Layer, RenderContext, Equipment } from "../../types";
import { COLORS, worldToScreen } from "../../types";

export class EquipmentLayer implements Layer {
  type: "equipment" = "equipment";
  visible = true;
  private equipment: Equipment[] = [];

  setEquipment(equipment: Equipment[]): void {
    this.equipment = equipment;
  }

  render(context: RenderContext): void {
    if (!this.visible || this.equipment.length === 0) return;

    const { selection, hoveredElement } = context;

    for (const equip of this.equipment) {
      const isSelected = selection?.type === "equipment" && selection.id === equip.id;
      const isHovered = hoveredElement?.type === "equipment" && hoveredElement.id === equip.id;

      this.renderEquipment(equip, context, isSelected, isHovered);
    }
  }

  private renderEquipment(
    equipment: Equipment,
    context: RenderContext,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    const screenPos = worldToScreen(
      equipment.position,
      viewport,
      canvasWidth,
      canvasHeight
    );

    // Determine equipment color based on type
    const color = this.getEquipmentColor(equipment.equipment_type);

    // Draw equipment symbol
    this.renderSymbol(screenPos, color, context, isSelected, isHovered);

    // Draw equipment label
    this.renderLabel(equipment, screenPos, context, isSelected, isHovered);
  }

  private renderSymbol(
    screenPos: { x: number; y: number },
    color: string,
    context: RenderContext,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx, viewport } = context;
    const { zoom } = viewport;

    // Calculate size based on zoom (but clamp to reasonable values)
    const baseSize = 8;
    const size = Math.max(6, Math.min(16, baseSize * Math.sqrt(zoom)));

    // Draw outer circle for selection/hover
    if (isSelected || isHovered) {
      ctx.beginPath();
      ctx.arc(screenPos.x, screenPos.y, size + 4, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? COLORS.selection : COLORS.hover;
      ctx.globalAlpha = 0.3;
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }

    // Draw main symbol (diamond shape)
    ctx.beginPath();
    ctx.moveTo(screenPos.x, screenPos.y - size);
    ctx.lineTo(screenPos.x + size, screenPos.y);
    ctx.lineTo(screenPos.x, screenPos.y + size);
    ctx.lineTo(screenPos.x - size, screenPos.y);
    ctx.closePath();

    // Fill
    ctx.fillStyle = color;
    ctx.fill();

    // Stroke
    if (isSelected) {
      ctx.strokeStyle = COLORS.selection;
      ctx.lineWidth = 2;
    } else if (isHovered) {
      ctx.strokeStyle = COLORS.hover;
      ctx.lineWidth = 2;
    } else {
      ctx.strokeStyle = this.darkenColor(color, 0.2);
      ctx.lineWidth = 1;
    }
    ctx.stroke();

    // Draw center dot
    ctx.beginPath();
    ctx.arc(screenPos.x, screenPos.y, 2, 0, Math.PI * 2);
    ctx.fillStyle = this.darkenColor(color, 0.4);
    ctx.fill();
  }

  private renderLabel(
    equipment: Equipment,
    screenPos: { x: number; y: number },
    context: RenderContext,
    isSelected: boolean,
    isHovered: boolean
  ): void {
    const { ctx } = context;

    // Only show labels when selected or hovered (to avoid clutter)
    if (!isSelected && !isHovered) return;

    const labelY = screenPos.y + 20; // Position below symbol

    // Draw equipment name
    ctx.fillStyle = COLORS.text;
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    // Draw background for better readability
    const textMetrics = ctx.measureText(equipment.name);
    const padding = 3;
    ctx.fillStyle = "rgba(15, 23, 42, 0.9)"; // COLORS.background with alpha
    ctx.fillRect(
      screenPos.x - textMetrics.width / 2 - padding,
      labelY - 2,
      textMetrics.width + padding * 2,
      14
    );

    // Draw text
    ctx.fillStyle = COLORS.text;
    ctx.fillText(equipment.name, screenPos.x, labelY);

    // Draw equipment type below (if different from name)
    if (equipment.equipment_type && equipment.equipment_type !== equipment.name) {
      const typeY = labelY + 14;
      ctx.font = "9px sans-serif";
      ctx.fillStyle = this.hexToRgba(COLORS.text, 0.7);

      const typeMetrics = ctx.measureText(equipment.equipment_type);
      ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
      ctx.fillRect(
        screenPos.x - typeMetrics.width / 2 - padding,
        typeY - 2,
        typeMetrics.width + padding * 2,
        12
      );

      ctx.fillStyle = this.hexToRgba(COLORS.text, 0.7);
      ctx.fillText(equipment.equipment_type, screenPos.x, typeY);
    }
  }

  private getEquipmentColor(equipmentType: string): string {
    const type = equipmentType.toLowerCase();

    if (type.includes("hvac") || type.includes("air") || type.includes("vent")) {
      return COLORS.equipment.hvac;
    }
    if (type.includes("electric") || type.includes("power") || type.includes("lighting")) {
      return COLORS.equipment.electrical;
    }
    if (type.includes("plumb") || type.includes("water") || type.includes("drain")) {
      return COLORS.equipment.plumbing;
    }

    return COLORS.equipment.default;
  }

  private darkenColor(hex: string, amount: number): string {
    // Convert hex to RGB
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    // Darken
    const newR = Math.floor(r * (1 - amount));
    const newG = Math.floor(g * (1 - amount));
    const newB = Math.floor(b * (1 - amount));

    // Convert back to hex
    return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
  }

  private hexToRgba(hex: string, alpha: number): string {
    // Convert hex to RGB
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}
