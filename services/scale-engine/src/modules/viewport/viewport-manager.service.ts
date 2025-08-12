import { Injectable, Logger } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { ConfigService } from '@nestjs/config';

import { ScaleEngineService } from '../scale-engine/scale-engine.service';
import { TileLoaderService } from '../lazy-loader/tile-loader.service';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';
import { BoundingBoxDto, ViewportQueryDto, ZoomRequestDto } from '../../dto/viewport.dto';

export interface ViewportState {
  viewport: BoundingBoxDto;
  scale: number;
  center: { x: number; y: number };
  visibleObjects: Map<string, FractalArxObject>;
  loadingTiles: Set<string>;
}

export interface ViewportEvent {
  type: 'initialized' | 'zoomed' | 'panned' | 'objects-loaded';
  viewport: BoundingBoxDto;
  scale: number;
  objectCount: number;
  duration?: number;
}

export type ZoomDirection = 'in' | 'out' | 'stable';

@Injectable()
export class ViewportManagerService {
  private readonly logger = new Logger(ViewportManagerService.name);
  private state: ViewportState;
  private readonly tileSize: number;
  private readonly preloadRadius: number;
  private zoomAnimationFrame: any;

  constructor(
    private readonly scaleEngine: ScaleEngineService,
    private readonly tileLoader: TileLoaderService,
    private readonly eventEmitter: EventEmitter2,
    private readonly configService: ConfigService,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    this.tileSize = this.configService.get('viewport.tileSize');
    this.preloadRadius = this.configService.get('viewport.preloadRadius');
    
    this.state = {
      viewport: { minX: 0, minY: 0, maxX: 0, maxY: 0 },
      scale: 1.0,
      center: { x: 0, y: 0 },
      visibleObjects: new Map(),
      loadingTiles: new Set(),
    };
  }

  /**
   * Initialize viewport with starting position
   */
  async initialize(
    center: { x: number; y: number },
    scale: number,
    viewportSize: { width: number; height: number },
  ): Promise<void> {
    const startTime = Date.now();
    
    this.state.scale = scale;
    this.state.center = center;
    this.state.viewport = this.calculateViewport(center, viewportSize, scale);
    
    // Load initial objects
    await this.loadVisibleObjects();
    
    const duration = Date.now() - startTime;
    
    // Emit initialization event
    this.eventEmitter.emit('viewport.initialized', {
      type: 'initialized',
      viewport: this.state.viewport,
      scale: this.state.scale,
      objectCount: this.state.visibleObjects.size,
      duration,
    } as ViewportEvent);
    
    this.logger.log(
      `Viewport initialized at scale ${scale} with ${this.state.visibleObjects.size} objects in ${duration}ms`,
    );
  }

  /**
   * Handle zoom change with smooth transitions
   */
  async zoomTo(request: ZoomRequestDto): Promise<void> {
    const startTime = Date.now();
    const startScale = this.state.scale;
    const targetScale = request.targetScale;
    const focalPoint = { x: request.focalX, y: request.focalY };
    const duration = request.duration || 200;
    
    // Cancel any existing animation
    if (this.zoomAnimationFrame) {
      clearTimeout(this.zoomAnimationFrame);
    }
    
    const scaleRatio = targetScale / startScale;
    const zoomDirection = this.getZoomDirection(scaleRatio);
    
    this.logger.debug(
      `Zooming ${zoomDirection} from ${startScale} to ${targetScale} (ratio: ${scaleRatio})`,
    );
    
    // Preload data for target scale
    if (zoomDirection === 'in') {
      await this.preloadForZoomIn(focalPoint, targetScale);
    }
    
    // Animate zoom if duration > 0
    if (duration > 0) {
      await this.animateZoom(startScale, targetScale, focalPoint, duration);
    } else {
      this.state.scale = targetScale;
    }
    
    // Update viewport for new scale
    this.updateViewportForScale(targetScale, focalPoint);
    
    // Load new objects
    await this.loadVisibleObjects();
    
    // Clean up old data for zoom out
    if (zoomDirection === 'out') {
      this.cleanupDetailedData();
    }
    
    const totalDuration = Date.now() - startTime;
    
    // Track performance
    this.performanceMonitor.recordZoomTransition(
      startScale,
      targetScale,
      totalDuration,
    );
    
    // Emit zoom event
    this.eventEmitter.emit('viewport.zoomed', {
      type: 'zoomed',
      viewport: this.state.viewport,
      scale: targetScale,
      objectCount: this.state.visibleObjects.size,
      duration: totalDuration,
    } as ViewportEvent);
    
    if (totalDuration > this.configService.get('performance.targetZoomTime')) {
      this.logger.warn(
        `Slow zoom transition: ${totalDuration}ms (target: ${this.configService.get('performance.targetZoomTime')}ms)`,
      );
    }
  }

  /**
   * Handle viewport panning
   */
  async panTo(
    newCenter: { x: number; y: number },
    duration: number = 0,
  ): Promise<void> {
    const startTime = Date.now();
    const oldViewport = { ...this.state.viewport };
    
    // Update center
    this.state.center = newCenter;
    
    // Calculate new viewport
    const width = oldViewport.maxX - oldViewport.minX;
    const height = oldViewport.maxY - oldViewport.minY;
    this.state.viewport = this.calculateViewport(
      newCenter,
      { width, height },
      this.state.scale,
    );
    
    // Determine which new tiles need loading
    const newTiles = this.getNewTiles(oldViewport, this.state.viewport);
    
    // Load new tiles
    if (newTiles.length > 0) {
      await this.loadTiles(newTiles);
    }
    
    // Update visible objects
    await this.loadVisibleObjects();
    
    const totalDuration = Date.now() - startTime;
    
    // Emit pan event
    this.eventEmitter.emit('viewport.panned', {
      type: 'panned',
      viewport: this.state.viewport,
      scale: this.state.scale,
      objectCount: this.state.visibleObjects.size,
      duration: totalDuration,
    } as ViewportEvent);
  }

  /**
   * Get current viewport state
   */
  getState(): ViewportState {
    return { ...this.state };
  }

  /**
   * Get visible objects
   */
  getVisibleObjects(): FractalArxObject[] {
    return Array.from(this.state.visibleObjects.values());
  }

  /**
   * Calculate viewport bounds from center and size
   */
  private calculateViewport(
    center: { x: number; y: number },
    size: { width: number; height: number },
    scale: number,
  ): BoundingBoxDto {
    // Scale affects how much area is visible
    const halfWidth = (size.width * scale) / 2;
    const halfHeight = (size.height * scale) / 2;
    
    return {
      minX: center.x - halfWidth,
      minY: center.y - halfHeight,
      maxX: center.x + halfWidth,
      maxY: center.y + halfHeight,
    };
  }

  /**
   * Load visible objects for current viewport
   */
  private async loadVisibleObjects(): Promise<void> {
    const query: ViewportQueryDto = {
      scale: this.state.scale,
      detailBudget: this.scaleEngine.calculateDetailBudget(),
    };
    
    const objects = await this.scaleEngine.getVisibleObjects(
      this.state.viewport,
      query,
    );
    
    // Update visible objects map
    this.state.visibleObjects.clear();
    for (const obj of objects) {
      this.state.visibleObjects.set(obj.id, obj);
    }
    
    this.logger.debug(
      `Loaded ${objects.length} objects for viewport at scale ${this.state.scale}`,
    );
  }

  /**
   * Determine zoom direction
   */
  private getZoomDirection(ratio: number): ZoomDirection {
    if (ratio < 0.5) return 'in';
    if (ratio > 2.0) return 'out';
    return 'stable';
  }

  /**
   * Preload data for zoom in
   */
  private async preloadForZoomIn(
    focalPoint: { x: number; y: number },
    targetScale: number,
  ): Promise<void> {
    // Calculate area around focal point
    const preloadRadius = this.tileSize * targetScale * 2;
    
    await this.scaleEngine.prefetchArea(
      focalPoint,
      preloadRadius,
      targetScale,
    );
    
    this.logger.debug(
      `Preloaded area around (${focalPoint.x}, ${focalPoint.y}) for scale ${targetScale}`,
    );
  }

  /**
   * Animate zoom transition
   */
  private async animateZoom(
    startScale: number,
    targetScale: number,
    focalPoint: { x: number; y: number },
    duration: number,
  ): Promise<void> {
    const steps = Math.ceil(duration / 16); // 60fps
    const scaleStep = (targetScale - startScale) / steps;
    
    return new Promise((resolve) => {
      let currentStep = 0;
      
      const animate = () => {
        currentStep++;
        this.state.scale = startScale + scaleStep * currentStep;
        
        if (currentStep < steps) {
          this.zoomAnimationFrame = setTimeout(animate, 16);
        } else {
          this.state.scale = targetScale;
          resolve();
        }
      };
      
      animate();
    });
  }

  /**
   * Update viewport after scale change
   */
  private updateViewportForScale(
    newScale: number,
    focalPoint: { x: number; y: number },
  ): void {
    // Adjust center to keep focal point stable
    const scaleFactor = newScale / this.state.scale;
    
    const dx = focalPoint.x - this.state.center.x;
    const dy = focalPoint.y - this.state.center.y;
    
    this.state.center = {
      x: focalPoint.x - dx * scaleFactor,
      y: focalPoint.y - dy * scaleFactor,
    };
    
    // Recalculate viewport
    const width = this.state.viewport.maxX - this.state.viewport.minX;
    const height = this.state.viewport.maxY - this.state.viewport.minY;
    
    this.state.viewport = this.calculateViewport(
      this.state.center,
      { width: width / this.state.scale, height: height / this.state.scale },
      newScale,
    );
  }

  /**
   * Clean up detailed data when zooming out
   */
  private cleanupDetailedData(): void {
    // Remove objects that are too detailed for current scale
    const toRemove: string[] = [];
    
    for (const [id, obj] of this.state.visibleObjects) {
      if (obj.minScale > this.state.scale * 2) {
        toRemove.push(id);
      }
    }
    
    for (const id of toRemove) {
      this.state.visibleObjects.delete(id);
    }
    
    if (toRemove.length > 0) {
      this.logger.debug(`Cleaned up ${toRemove.length} detailed objects`);
    }
  }

  /**
   * Get new tiles that need loading
   */
  private getNewTiles(
    oldViewport: BoundingBoxDto,
    newViewport: BoundingBoxDto,
  ): Array<{ x: number; y: number; z: number }> {
    const zoom = this.scaleToZoom(this.state.scale);
    const tiles: Array<{ x: number; y: number; z: number }> = [];
    
    // Calculate tile ranges for both viewports
    const oldTiles = this.viewportToTiles(oldViewport, zoom);
    const newTiles = this.viewportToTiles(newViewport, zoom);
    
    // Find tiles that are in new but not in old
    for (const tile of newTiles) {
      const isNew = !oldTiles.some(
        (t) => t.x === tile.x && t.y === tile.y && t.z === tile.z,
      );
      if (isNew) {
        tiles.push(tile);
      }
    }
    
    return tiles;
  }

  /**
   * Convert viewport to tile coordinates
   */
  private viewportToTiles(
    viewport: BoundingBoxDto,
    zoom: number,
  ): Array<{ x: number; y: number; z: number }> {
    const tiles: Array<{ x: number; y: number; z: number }> = [];
    
    const minTileX = Math.floor((viewport.minX + 180) / 360 * Math.pow(2, zoom));
    const maxTileX = Math.floor((viewport.maxX + 180) / 360 * Math.pow(2, zoom));
    const minTileY = Math.floor((90 - viewport.maxY) / 180 * Math.pow(2, zoom));
    const maxTileY = Math.floor((90 - viewport.minY) / 180 * Math.pow(2, zoom));
    
    for (let x = minTileX; x <= maxTileX; x++) {
      for (let y = minTileY; y <= maxTileY; y++) {
        tiles.push({ x, y, z: zoom });
      }
    }
    
    return tiles;
  }

  /**
   * Convert scale to zoom level
   */
  private scaleToZoom(scale: number): number {
    // Approximate conversion - adjust based on your needs
    return Math.round(Math.log2(100 / scale));
  }

  /**
   * Load tiles
   */
  private async loadTiles(
    tiles: Array<{ x: number; y: number; z: number }>,
  ): Promise<void> {
    const loadPromises = tiles.map((tile) => {
      const tileKey = `${tile.z}:${tile.x}:${tile.y}`;
      
      if (!this.state.loadingTiles.has(tileKey)) {
        this.state.loadingTiles.add(tileKey);
        
        return this.tileLoader
          .loadTile(tile, this.state.scale)
          .finally(() => {
            this.state.loadingTiles.delete(tileKey);
          });
      }
      
      return Promise.resolve();
    });
    
    await Promise.all(loadPromises);
  }
}