import type { Layer, RenderContext } from "../../types";
import { COLORS, worldToScreen } from "../../types";

export class GridLayer implements Layer {
  type: "grid" = "grid";
  visible = true;

  render(context: RenderContext): void {
    if (!this.visible) return;

    const { ctx, viewport, canvasWidth, canvasHeight } = context;
    const { zoom } = viewport;

    // Calculate adaptive grid spacing based on zoom level
    const baseSpacing = 1; // 1 meter in world space
    const minPixelSpacing = 50; // Minimum pixels between grid lines
    const spacing = this.calculateGridSpacing(baseSpacing, zoom, minPixelSpacing);

    // Calculate grid bounds in world space
    const worldBounds = this.calculateWorldBounds(viewport, canvasWidth, canvasHeight);

    // Draw minor grid lines (every spacing unit)
    this.drawGridLines(
      context,
      worldBounds,
      spacing,
      COLORS.grid.minor,
      1
    );

    // Draw major grid lines (every 5 spacing units)
    this.drawGridLines(
      context,
      worldBounds,
      spacing * 5,
      COLORS.grid.major,
      2
    );

    // Draw axis labels at major grid lines
    this.drawAxisLabels(context, worldBounds, spacing * 5);
  }

  private calculateGridSpacing(
    baseSpacing: number,
    zoom: number,
    minPixelSpacing: number
  ): number {
    // Calculate how many pixels the base spacing would be at current zoom
    const pixelSpacing = baseSpacing * zoom;

    // If too small, increase spacing by powers of 2
    if (pixelSpacing < minPixelSpacing) {
      let multiplier = 1;
      while (baseSpacing * multiplier * zoom < minPixelSpacing) {
        multiplier *= 2;
      }
      return baseSpacing * multiplier;
    }

    // If too large, decrease spacing by powers of 2
    if (pixelSpacing > minPixelSpacing * 4) {
      let divisor = 1;
      while (baseSpacing / divisor * zoom > minPixelSpacing * 4 && divisor < 16) {
        divisor *= 2;
      }
      return baseSpacing / divisor;
    }

    return baseSpacing;
  }

  private calculateWorldBounds(
    viewport: RenderContext["viewport"],
    canvasWidth: number,
    canvasHeight: number
  ): { minX: number; maxX: number; minY: number; maxY: number } {
    const { zoom, pan, bounds } = viewport;

    const viewportCenterX = (bounds.min.x + bounds.max.x) / 2;
    const viewportCenterY = (bounds.min.y + bounds.max.y) / 2;

    const halfWorldWidth = (canvasWidth / 2) / zoom;
    const halfWorldHeight = (canvasHeight / 2) / zoom;

    return {
      minX: viewportCenterX - pan.x - halfWorldWidth,
      maxX: viewportCenterX - pan.x + halfWorldWidth,
      minY: viewportCenterY - pan.y - halfWorldHeight,
      maxY: viewportCenterY - pan.y + halfWorldHeight,
    };
  }

  private drawGridLines(
    context: RenderContext,
    worldBounds: { minX: number; maxX: number; minY: number; maxY: number },
    spacing: number,
    color: string,
    lineWidth: number
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();

    // Vertical lines
    const startX = Math.floor(worldBounds.minX / spacing) * spacing;
    for (let x = startX; x <= worldBounds.maxX; x += spacing) {
      const screenTop = worldToScreen(
        { x, y: worldBounds.minY },
        viewport,
        canvasWidth,
        canvasHeight
      );
      const screenBottom = worldToScreen(
        { x, y: worldBounds.maxY },
        viewport,
        canvasWidth,
        canvasHeight
      );

      ctx.moveTo(screenTop.x, screenTop.y);
      ctx.lineTo(screenBottom.x, screenBottom.y);
    }

    // Horizontal lines
    const startY = Math.floor(worldBounds.minY / spacing) * spacing;
    for (let y = startY; y <= worldBounds.maxY; y += spacing) {
      const screenLeft = worldToScreen(
        { x: worldBounds.minX, y },
        viewport,
        canvasWidth,
        canvasHeight
      );
      const screenRight = worldToScreen(
        { x: worldBounds.maxX, y },
        viewport,
        canvasWidth,
        canvasHeight
      );

      ctx.moveTo(screenLeft.x, screenLeft.y);
      ctx.lineTo(screenRight.x, screenRight.y);
    }

    ctx.stroke();
  }

  private drawAxisLabels(
    context: RenderContext,
    worldBounds: { minX: number; maxX: number; minY: number; maxY: number },
    spacing: number
  ): void {
    const { ctx, viewport, canvasWidth, canvasHeight } = context;

    ctx.fillStyle = COLORS.text;
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    // X-axis labels (bottom of canvas)
    const startX = Math.floor(worldBounds.minX / spacing) * spacing;
    for (let x = startX; x <= worldBounds.maxX; x += spacing) {
      if (x === 0) continue; // Skip origin

      const screenPos = worldToScreen(
        { x, y: worldBounds.minY },
        viewport,
        canvasWidth,
        canvasHeight
      );

      ctx.fillText(x.toFixed(0), screenPos.x, canvasHeight - 15);
    }

    // Y-axis labels (left of canvas)
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    const startY = Math.floor(worldBounds.minY / spacing) * spacing;
    for (let y = startY; y <= worldBounds.maxY; y += spacing) {
      if (y === 0) continue; // Skip origin

      const screenPos = worldToScreen(
        { x: worldBounds.minX, y },
        viewport,
        canvasWidth,
        canvasHeight
      );

      ctx.fillText(y.toFixed(0), 5, screenPos.y);
    }

    // Draw origin marker
    const origin = worldToScreen({ x: 0, y: 0 }, viewport, canvasWidth, canvasHeight);
    if (
      origin.x >= 0 &&
      origin.x <= canvasWidth &&
      origin.y >= 0 &&
      origin.y <= canvasHeight
    ) {
      ctx.fillStyle = COLORS.grid.major;
      ctx.beginPath();
      ctx.arc(origin.x, origin.y, 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = COLORS.text;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText("(0, 0)", origin.x + 8, origin.y + 8);
    }
  }
}
