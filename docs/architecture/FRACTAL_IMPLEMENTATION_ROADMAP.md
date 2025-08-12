# Fractal ArxObject Implementation Roadmap

## Overview

This roadmap provides a detailed, step-by-step implementation plan for the Fractal ArxObject system, including prerequisites, dependencies, and specific engineering tasks.

## Prerequisites & Foundation Work

### Current State Assessment

Before implementing the fractal system, we need to ensure these components are in place:

#### ✅ Completed Prerequisites
- [x] Go ArxObject Engine with sub-microsecond operations
- [x] gRPC communication layer between Python and Go
- [x] SVGX rendering engine
- [x] Basic ArxObject data model
- [x] PostgreSQL with PostGIS extension
- [x] Redis caching infrastructure

#### 🔄 Required Enhancements
- [ ] Upgrade PostgreSQL to include TimescaleDB for time-series data
- [ ] Implement S3/MinIO for binary large object storage
- [ ] Set up CDN for static asset delivery
- [ ] Add WebSocket support for real-time viewport updates
- [ ] Implement tile server for map-style data delivery

## Phase 0: Infrastructure Preparation (Week 1-2)

### Database Enhancements

```bash
# 1. Install TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

# 2. Enable additional PostGIS functions
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

# 3. Set up partitioning for scale-based data
CREATE TABLE fractal_arxobjects_partitioned (
    LIKE fractal_arxobjects INCLUDING ALL
) PARTITION BY RANGE (optimal_scale);
```

### Storage Infrastructure

```yaml
# docker-compose additions
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: arxos
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
  
  tile-server:
    build: ./services/tile-server
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis
```

### Performance Monitoring

```typescript
// services/monitoring/performance-monitor.ts
export class PerformanceMonitor {
  private metrics = {
    zoomLatency: new Histogram(),
    tileLoadTime: new Histogram(),
    renderFrameTime: new Histogram(),
    cacheHitRate: new Counter(),
    memoryUsage: new Gauge()
  };

  trackZoomPerformance(duration: number, fromScale: number, toScale: number) {
    this.metrics.zoomLatency.observe(duration);
    
    if (duration > 200) {
      console.warn(`Zoom transition exceeded target: ${duration}ms`);
      this.logSlowZoom(fromScale, toScale, duration);
    }
  }
}
```

## Phase 1: Core Fractal Engine (Weeks 3-6)

### Task 1.1: Database Schema Migration

```sql
-- migrations/001_create_fractal_schema.sql

-- Main fractal objects table
CREATE TABLE IF NOT EXISTS fractal_arxobjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES fractal_arxobjects(id) ON DELETE CASCADE,
    
    -- Core properties
    object_type VARCHAR(255) NOT NULL,
    object_subtype VARCHAR(255),
    
    -- Spatial coordinates (millimeter precision)
    position_x DECIMAL(12,9) NOT NULL,
    position_y DECIMAL(12,9) NOT NULL,
    position_z DECIMAL(12,9) DEFAULT 0,
    
    -- Scale metadata
    min_scale DECIMAL(10,8) NOT NULL,
    max_scale DECIMAL(10,8) NOT NULL,
    optimal_scale DECIMAL(10,8) NOT NULL,
    
    -- Importance for rendering priority
    importance_level INTEGER NOT NULL DEFAULT 3
        CHECK (importance_level BETWEEN 1 AND 4),
    
    -- Physical dimensions in millimeters
    width DECIMAL(10,6),
    height DECIMAL(10,6),
    depth DECIMAL(10,6),
    
    -- Flexible properties
    properties JSONB NOT NULL DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Audit fields
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT valid_scale_range 
        CHECK (min_scale <= optimal_scale AND optimal_scale <= max_scale),
    CONSTRAINT valid_dimensions 
        CHECK (width >= 0 AND height >= 0 AND depth >= 0)
);

-- Create spatial index
CREATE INDEX idx_fractal_spatial ON fractal_arxobjects 
    USING GIST (ST_MakePoint(position_x, position_y, position_z));

-- Create scale-based indexes
CREATE INDEX idx_fractal_scale_range ON fractal_arxobjects (min_scale, max_scale);
CREATE INDEX idx_fractal_optimal_scale ON fractal_arxobjects (optimal_scale);
CREATE INDEX idx_fractal_importance ON fractal_arxobjects (importance_level, optimal_scale);
CREATE INDEX idx_fractal_parent ON fractal_arxobjects (parent_id);
CREATE INDEX idx_fractal_type ON fractal_arxobjects (object_type, optimal_scale);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_fractal_arxobjects_updated_at 
    BEFORE UPDATE ON fractal_arxobjects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Task 1.2: Scale Engine Implementation

```typescript
// services/scale-engine/scale-engine.service.ts

import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { FractalArxObject } from './entities/fractal-arxobject.entity';

@Injectable()
export class ScaleEngineService {
  // Core scale levels
  private readonly SCALE_LEVELS = {
    CAMPUS: 10.0,
    BUILDING: 1.0,
    FLOOR: 0.1,
    ROOM: 0.01,
    FIXTURE: 0.001,
    COMPONENT: 0.0001,
    SCHEMATIC: 0.00001
  };

  constructor(
    @InjectRepository(FractalArxObject)
    private arxObjectRepo: Repository<FractalArxObject>,
    private cacheService: CacheService,
    private performanceMonitor: PerformanceMonitor
  ) {}

  /**
   * Get objects visible at current scale within viewport
   */
  async getVisibleObjects(
    viewport: BoundingBox,
    scale: number,
    options: QueryOptions = {}
  ): Promise<FractalArxObject[]> {
    const startTime = Date.now();
    
    // Check cache first
    const cacheKey = this.getCacheKey(viewport, scale);
    const cached = await this.cacheService.get(cacheKey);
    if (cached) {
      this.performanceMonitor.recordCacheHit();
      return cached;
    }

    // Build query
    const query = this.arxObjectRepo
      .createQueryBuilder('obj')
      .where('obj.min_scale <= :scale', { scale })
      .andWhere('obj.max_scale >= :scale', { scale })
      .andWhere(
        `ST_Intersects(
          ST_MakePoint(obj.position_x, obj.position_y),
          ST_MakeEnvelope(:minX, :minY, :maxX, :maxY, 4326)
        )`,
        {
          minX: viewport.minX,
          minY: viewport.minY,
          maxX: viewport.maxX,
          maxY: viewport.maxY
        }
      );

    // Apply importance filtering
    if (options.minImportance) {
      query.andWhere('obj.importance_level <= :importance', {
        importance: options.minImportance
      });
    }

    // Apply type filtering
    if (options.types?.length) {
      query.andWhere('obj.object_type IN (:...types)', {
        types: options.types
      });
    }

    // Order by importance and optimal scale
    query
      .orderBy('obj.importance_level', 'ASC')
      .addOrderBy(
        `ABS(obj.optimal_scale - ${scale})`,
        'ASC'
      );

    // Apply detail budget
    const detailBudget = options.detailBudget || this.calculateDetailBudget();
    query.limit(detailBudget);

    const results = await query.getMany();

    // Cache results
    await this.cacheService.set(cacheKey, results, 300); // 5 min TTL

    // Track performance
    const duration = Date.now() - startTime;
    this.performanceMonitor.trackQueryPerformance(duration, results.length);

    return results;
  }

  /**
   * Calculate appropriate detail budget based on scale and device
   */
  private calculateDetailBudget(): number {
    // Base budget
    let budget = 1000;

    // Adjust for device capabilities
    if (typeof window !== 'undefined') {
      const memory = (navigator as any).deviceMemory || 4;
      const cores = navigator.hardwareConcurrency || 4;
      
      budget = budget * (memory / 4) * (cores / 4);
    }

    // Cap between reasonable limits
    return Math.min(Math.max(budget, 500), 5000);
  }

  /**
   * Get the natural scale breaks for smooth transitions
   */
  getScaleBreaks(): number[] {
    return Object.values(this.SCALE_LEVELS).sort((a, b) => b - a);
  }

  /**
   * Snap to nearest meaningful scale level
   */
  snapToNearestScale(scale: number): number {
    const scales = this.getScaleBreaks();
    return scales.reduce((prev, curr) => 
      Math.abs(curr - scale) < Math.abs(prev - scale) ? curr : prev
    );
  }
}
```

### Task 1.3: Viewport Manager

```typescript
// services/viewport/viewport-manager.service.ts

@Injectable()
export class ViewportManagerService {
  private currentViewport: BoundingBox;
  private currentScale: number;
  private visibleObjects: Map<string, FractalArxObject> = new Map();
  private loadingTiles: Set<string> = new Set();

  constructor(
    private scaleEngine: ScaleEngineService,
    private tileLoader: TileLoaderService,
    private eventEmitter: EventEmitter2
  ) {}

  /**
   * Initialize viewport with starting position
   */
  async initialize(
    centerPoint: Point,
    initialScale: number,
    viewportSize: Size
  ): Promise<void> {
    this.currentScale = initialScale;
    this.currentViewport = this.calculateViewport(centerPoint, viewportSize, initialScale);
    
    await this.loadVisibleObjects();
    this.eventEmitter.emit('viewport.initialized', {
      viewport: this.currentViewport,
      scale: this.currentScale,
      objectCount: this.visibleObjects.size
    });
  }

  /**
   * Handle zoom change with smooth transitions
   */
  async zoomTo(
    targetScale: number,
    focalPoint: Point,
    duration: number = 200
  ): Promise<void> {
    const startScale = this.currentScale;
    const scaleRatio = targetScale / startScale;

    // Determine zoom type
    const zoomType = this.getZoomType(scaleRatio);
    
    // Preload data for target scale
    if (zoomType === 'zoom-in') {
      await this.preloadDetailForZoomIn(focalPoint, targetScale);
    }

    // Animate zoom
    await this.animateZoom(startScale, targetScale, focalPoint, duration);

    // Update current scale
    this.currentScale = targetScale;

    // Load new objects
    await this.loadVisibleObjects();

    // Clean up old data
    if (zoomType === 'zoom-out') {
      this.cleanupDetailedData();
    }

    this.eventEmitter.emit('viewport.zoomed', {
      fromScale: startScale,
      toScale: targetScale,
      focalPoint
    });
  }

  /**
   * Handle viewport panning
   */
  async panTo(newCenter: Point, duration: number = 0): Promise<void> {
    const oldViewport = this.currentViewport;
    this.currentViewport = this.calculateViewport(
      newCenter,
      { 
        width: oldViewport.maxX - oldViewport.minX,
        height: oldViewport.maxY - oldViewport.minY
      },
      this.currentScale
    );

    // Load new tiles that come into view
    const newTiles = this.getNewTiles(oldViewport, this.currentViewport);
    await this.loadTiles(newTiles);

    // Update visible objects
    await this.loadVisibleObjects();

    this.eventEmitter.emit('viewport.panned', {
      from: oldViewport,
      to: this.currentViewport
    });
  }

  /**
   * Load tiles for viewport
   */
  private async loadTiles(tiles: Tile[]): Promise<void> {
    const loadPromises = tiles.map(tile => {
      const tileKey = this.getTileKey(tile);
      
      if (!this.loadingTiles.has(tileKey)) {
        this.loadingTiles.add(tileKey);
        return this.tileLoader
          .loadTile(tile, this.currentScale)
          .finally(() => this.loadingTiles.delete(tileKey));
      }
      
      return Promise.resolve();
    });

    await Promise.all(loadPromises);
  }

  private getZoomType(ratio: number): 'zoom-in' | 'zoom-out' | 'minor' {
    if (ratio < 0.5) return 'zoom-in';
    if (ratio > 2.0) return 'zoom-out';
    return 'minor';
  }
}
```

## Phase 2: Lazy Loading System (Weeks 7-10)

### Task 2.1: Tile-Based Loading

```typescript
// services/tile-loader/tile-loader.service.ts

@Injectable()
export class TileLoaderService {
  private tileCache: LRUCache<string, TileData>;
  private tileSize = 256; // pixels per tile

  constructor(
    private http: HttpClient,
    private cacheService: CacheService
  ) {
    this.tileCache = new LRUCache({
      max: 500,
      ttl: 1000 * 60 * 10 // 10 minutes
    });
  }

  /**
   * Load a tile of data
   */
  async loadTile(tile: Tile, scale: number): Promise<TileData> {
    const tileKey = `${tile.z}/${tile.x}/${tile.y}`;
    
    // Check memory cache
    if (this.tileCache.has(tileKey)) {
      return this.tileCache.get(tileKey)!;
    }

    // Check persistent cache
    const cached = await this.cacheService.get(`tile:${tileKey}`);
    if (cached) {
      this.tileCache.set(tileKey, cached);
      return cached;
    }

    // Load from server
    const tileData = await this.fetchTile(tile, scale);
    
    // Cache the result
    this.tileCache.set(tileKey, tileData);
    await this.cacheService.set(`tile:${tileKey}`, tileData, 3600);

    return tileData;
  }

  /**
   * Predictive preloading based on user movement
   */
  async preloadArea(
    center: Point,
    radius: number,
    scale: number,
    priority: 'high' | 'low' = 'low'
  ): Promise<void> {
    const tiles = this.getTilesInRadius(center, radius, scale);
    
    // Sort by distance from center
    tiles.sort((a, b) => {
      const distA = this.distanceFromCenter(a, center);
      const distB = this.distanceFromCenter(b, center);
      return distA - distB;
    });

    // Load tiles with appropriate priority
    const loadPromises = tiles.map((tile, index) => {
      const delay = priority === 'low' ? index * 50 : 0;
      return new Promise(resolve => {
        setTimeout(() => {
          this.loadTile(tile, scale).then(resolve);
        }, delay);
      });
    });

    await Promise.all(loadPromises);
  }

  private getTilesInRadius(
    center: Point,
    radius: number,
    scale: number
  ): Tile[] {
    const zoom = this.scaleToZoom(scale);
    const centerTile = this.pointToTile(center, zoom);
    const tileRadius = Math.ceil(radius / this.tileSize);
    
    const tiles: Tile[] = [];
    
    for (let dx = -tileRadius; dx <= tileRadius; dx++) {
      for (let dy = -tileRadius; dy <= tileRadius; dy++) {
        tiles.push({
          x: centerTile.x + dx,
          y: centerTile.y + dy,
          z: zoom
        });
      }
    }
    
    return tiles;
  }
}
```

### Task 2.2: Progressive Detail Loading

```typescript
// services/detail-loader/progressive-detail-loader.ts

@Injectable()
export class ProgressiveDetailLoader {
  private detailQueue: PriorityQueue<DetailRequest>;
  private loading = false;

  constructor(
    private arxObjectService: ArxObjectService,
    private performanceMonitor: PerformanceMonitor
  ) {
    this.detailQueue = new PriorityQueue((a, b) => b.priority - a.priority);
  }

  /**
   * Queue detail loading for objects
   */
  queueDetailLoad(
    objects: FractalArxObject[],
    scale: number,
    viewport: BoundingBox
  ): void {
    objects.forEach(obj => {
      const priority = this.calculatePriority(obj, scale, viewport);
      
      this.detailQueue.enqueue({
        objectId: obj.id,
        detailLevel: this.getDetailLevelForScale(scale),
        priority,
        scale
      });
    });

    if (!this.loading) {
      this.processQueue();
    }
  }

  /**
   * Process detail loading queue
   */
  private async processQueue(): Promise<void> {
    this.loading = true;

    while (!this.detailQueue.isEmpty()) {
      const batch = this.detailQueue.dequeueBatch(10); // Load 10 at a time
      
      await Promise.all(
        batch.map(request => this.loadDetail(request))
      );

      // Yield to browser
      await new Promise(resolve => setTimeout(resolve, 0));
    }

    this.loading = false;
  }

  /**
   * Calculate loading priority
   */
  private calculatePriority(
    object: FractalArxObject,
    scale: number,
    viewport: BoundingBox
  ): number {
    let priority = 100;

    // Higher importance = higher priority
    priority += (5 - object.importance_level) * 20;

    // Closer to viewport center = higher priority
    const distance = this.distanceFromViewportCenter(object, viewport);
    priority -= distance * 0.1;

    // Closer to optimal scale = higher priority
    const scaleDiff = Math.abs(object.optimal_scale - scale);
    priority -= scaleDiff * 10;

    return Math.max(0, priority);
  }
}
```

## Phase 3: Contribution System (Weeks 11-14)

### Task 3.1: Scale-Aware Contribution Tools

```typescript
// services/contribution/scale-contribution.service.ts

@Injectable()
export class ScaleContributionService {
  private readonly CONTRIBUTION_TYPES = {
    BUILDING: ['floor_plan', 'exterior', 'systems_overview'],
    ROOM: ['walls', 'doors', 'windows', 'major_equipment'],
    FIXTURE: ['outlets', 'switches', 'lights', 'hvac_registers'],
    COMPONENT: ['make_model', 'specifications', 'ratings'],
    SCHEMATIC: ['wiring', 'connections', 'modifications']
  };

  constructor(
    private arxObjectService: ArxObjectService,
    private biltService: BiltRewardService,
    private validationService: ValidationService
  ) {}

  /**
   * Submit contribution at specific scale
   */
  async submitContribution(
    objectId: string,
    contribution: ContributionData,
    userId: string,
    scale: number
  ): Promise<ContributionResult> {
    // Validate contribution type for scale
    const validTypes = this.getValidTypesForScale(scale);
    if (!validTypes.includes(contribution.type)) {
      throw new Error(`Invalid contribution type ${contribution.type} for scale ${scale}`);
    }

    // Validate data
    const validation = await this.validationService.validateContribution(
      contribution,
      scale
    );

    if (!validation.isValid) {
      return {
        success: false,
        errors: validation.errors
      };
    }

    // Calculate BILT reward
    const biltReward = await this.biltService.calculateReward(
      contribution,
      scale,
      validation.confidence
    );

    // Store contribution
    const stored = await this.storeContribution({
      object_id: objectId,
      contributor_id: userId,
      contribution_scale: scale,
      contribution_type: contribution.type,
      data: contribution.data,
      confidence_score: validation.confidence,
      bilt_earned: biltReward
    });

    // Update parent object if needed
    if (this.shouldPropagateToParent(contribution.type)) {
      await this.propagateToParent(objectId, contribution);
    }

    return {
      success: true,
      contributionId: stored.id,
      biltEarned: biltReward,
      confidence: validation.confidence
    };
  }

  /**
   * Get valid contribution types for scale level
   */
  private getValidTypesForScale(scale: number): string[] {
    if (scale >= 1.0) return this.CONTRIBUTION_TYPES.BUILDING;
    if (scale >= 0.1) return this.CONTRIBUTION_TYPES.ROOM;
    if (scale >= 0.01) return this.CONTRIBUTION_TYPES.FIXTURE;
    if (scale >= 0.001) return this.CONTRIBUTION_TYPES.COMPONENT;
    return this.CONTRIBUTION_TYPES.SCHEMATIC;
  }
}
```

### Task 3.2: BILT Reward Engine

```typescript
// services/rewards/bilt-reward.service.ts

@Injectable()
export class BiltRewardService {
  private readonly BASE_REWARDS = {
    floor_plan: 10,
    walls: 5,
    outlets: 3,
    make_model: 8,
    wiring: 15,
    modifications: 20
  };

  private readonly SCALE_MULTIPLIERS = {
    10.0: 1.0,   // Campus
    1.0: 1.0,    // Building
    0.1: 1.2,    // Floor
    0.01: 1.5,   // Room
    0.001: 1.8,  // Fixture
    0.0001: 2.0, // Component
    0.00001: 2.5 // Schematic
  };

  /**
   * Calculate BILT reward for contribution
   */
  async calculateReward(
    contribution: ContributionData,
    scale: number,
    confidence: number
  ): Promise<number> {
    // Get base reward
    const baseReward = this.BASE_REWARDS[contribution.type] || 5;

    // Get scale multiplier
    const scaleMultiplier = this.getScaleMultiplier(scale);

    // Calculate quality multiplier
    const qualityMultiplier = this.calculateQualityMultiplier(
      contribution,
      confidence
    );

    // Calculate final reward
    const reward = baseReward * scaleMultiplier * qualityMultiplier;

    // Apply bonuses
    const bonuses = await this.calculateBonuses(contribution);
    
    return Math.round((reward + bonuses) * 100) / 100; // Round to 2 decimals
  }

  private getScaleMultiplier(scale: number): number {
    // Find closest scale level
    const scales = Object.keys(this.SCALE_MULTIPLIERS)
      .map(Number)
      .sort((a, b) => b - a);

    for (const scaleLevel of scales) {
      if (scale >= scaleLevel) {
        return this.SCALE_MULTIPLIERS[scaleLevel];
      }
    }

    return this.SCALE_MULTIPLIERS[0.00001]; // Maximum multiplier for finest detail
  }

  private calculateQualityMultiplier(
    contribution: ContributionData,
    confidence: number
  ): number {
    let multiplier = 1.0;

    // Confidence affects multiplier
    multiplier *= (0.5 + confidence * 0.5); // 0.5x to 1x based on confidence

    // Completeness affects multiplier
    if (contribution.data.complete) {
      multiplier *= 1.2;
    }

    // Documentation affects multiplier
    if (contribution.data.documentation) {
      multiplier *= 1.1;
    }

    // Photos/evidence affects multiplier
    if (contribution.data.photos?.length > 0) {
      multiplier *= 1.15;
    }

    return multiplier;
  }

  private async calculateBonuses(contribution: ContributionData): Promise<number> {
    let bonus = 0;

    // First contribution bonus
    if (await this.isFirstContribution(contribution)) {
      bonus += 5;
    }

    // Rare detail bonus
    if (this.isRareDetail(contribution)) {
      bonus += 10;
    }

    // Verification bonus (if verifying others' work)
    if (contribution.type === 'verification') {
      bonus += 2;
    }

    return bonus;
  }
}
```

## Phase 4: UI Implementation (Weeks 15-18)

### Task 4.1: Zoom Interface Component

```typescript
// frontend/components/fractal-zoom/fractal-zoom.component.tsx

import React, { useRef, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { useGesture } from '@use-gesture/react';

interface FractalZoomProps {
  initialScale: number;
  initialCenter: Point;
  onScaleChange: (scale: number) => void;
  onViewportChange: (viewport: BoundingBox) => void;
}

export const FractalZoomComponent: React.FC<FractalZoomProps> = ({
  initialScale,
  initialCenter,
  onScaleChange,
  onViewportChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(initialScale);
  const [center, setCenter] = useState(initialCenter);
  const [objects, setObjects] = useState<FractalArxObject[]>([]);
  const [loading, setLoading] = useState(false);

  // Handle zoom gestures
  const bind = useGesture({
    onWheel: ({ delta: [, dy], event }) => {
      event.preventDefault();
      const scaleFactor = 1 - dy * 0.001;
      const newScale = scale * scaleFactor;
      
      // Clamp scale to valid range
      const clampedScale = Math.max(0.00001, Math.min(100, newScale));
      
      handleZoom(clampedScale, { x: event.clientX, y: event.clientY });
    },
    onPinch: ({ offset: [d] }) => {
      const newScale = initialScale * (d / 100);
      handleZoom(newScale, center);
    },
    onDrag: ({ offset: [x, y] }) => {
      handlePan({ x: center.x + x, y: center.y + y });
    }
  });

  // Handle zoom changes
  const handleZoom = async (newScale: number, focalPoint: Point) => {
    setLoading(true);
    
    // Update scale
    setScale(newScale);
    onScaleChange(newScale);

    // Load objects for new scale
    const viewport = calculateViewport(center, canvasRef.current!, newScale);
    const newObjects = await loadObjectsForScale(viewport, newScale);
    
    setObjects(newObjects);
    setLoading(false);
  };

  // Render scale indicator
  const renderScaleIndicator = () => {
    const scaleLabel = getScaleLabel(scale);
    const scalePercentage = getScalePercentage(scale);

    return (
      <div className="scale-indicator">
        <div className="scale-bar">
          <div 
            className="scale-fill" 
            style={{ width: `${scalePercentage}%` }}
          />
          <div className="scale-markers">
            {SCALE_MARKERS.map(marker => (
              <div 
                key={marker.scale}
                className="scale-marker"
                style={{ left: `${marker.position}%` }}
                onClick={() => handleZoom(marker.scale, center)}
              >
                {marker.label}
              </div>
            ))}
          </div>
        </div>
        <div className="scale-label">{scaleLabel}</div>
      </div>
    );
  };

  // Render contribution tools based on scale
  const renderScaleTools = () => {
    const tools = getToolsForScale(scale);

    return (
      <div className="scale-tools">
        <h3>Available at this scale:</h3>
        {tools.map(tool => (
          <button
            key={tool.id}
            className="tool-button"
            onClick={() => activateTool(tool)}
          >
            <Icon name={tool.icon} />
            {tool.label}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="fractal-zoom-container" {...bind()}>
      <canvas ref={canvasRef} className="zoom-canvas" />
      
      {/* Scale indicator */}
      {renderScaleIndicator()}
      
      {/* Context-sensitive tools */}
      {renderScaleTools()}
      
      {/* Loading indicator */}
      {loading && <LoadingOverlay message="Loading detail..." />}
      
      {/* Object count */}
      <div className="object-stats">
        Objects visible: {objects.length}
      </div>
    </div>
  );
};
```

### Task 4.2: Progressive Rendering

```typescript
// frontend/services/progressive-renderer.ts

export class ProgressiveRenderer {
  private renderQueue: RenderQueue;
  private framebudget = 16; // ms per frame for 60fps

  /**
   * Render objects progressively by importance
   */
  async renderProgressive(
    objects: FractalArxObject[],
    viewport: BoundingBox,
    scale: number
  ): Promise<void> {
    // Sort by importance and distance from center
    const sorted = this.sortForRendering(objects, viewport);

    // Group by importance level
    const groups = {
      critical: sorted.filter(o => o.importance_level === 1),
      important: sorted.filter(o => o.importance_level === 2),
      detail: sorted.filter(o => o.importance_level === 3),
      optional: sorted.filter(o => o.importance_level === 4)
    };

    // Render in phases
    await this.renderPhase(groups.critical, 'immediate');
    await this.renderPhase(groups.important, 'fast');
    await this.renderPhase(groups.detail, 'normal');
    await this.renderPhase(groups.optional, 'idle');
  }

  private async renderPhase(
    objects: FractalArxObject[],
    priority: 'immediate' | 'fast' | 'normal' | 'idle'
  ): Promise<void> {
    const batchSize = this.getBatchSize(priority);
    
    for (let i = 0; i < objects.length; i += batchSize) {
      const batch = objects.slice(i, i + batchSize);
      
      // Render batch
      const startTime = performance.now();
      this.renderBatch(batch);
      const renderTime = performance.now() - startTime;

      // Yield if we're taking too long
      if (renderTime > this.framebudget) {
        await this.yieldToBrowser();
      }
    }
  }

  private getBatchSize(priority: string): number {
    switch (priority) {
      case 'immediate': return 100;
      case 'fast': return 50;
      case 'normal': return 20;
      case 'idle': return 10;
      default: return 20;
    }
  }

  private async yieldTooBrowser(): Promise<void> {
    return new Promise(resolve => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => resolve());
      } else {
        setTimeout(resolve, 0);
      }
    });
  }
}
```

## Deployment & Testing Strategy

### Performance Testing

```typescript
// tests/performance/fractal-performance.spec.ts

describe('Fractal ArxObject Performance', () => {
  it('should complete zoom transition in < 200ms', async () => {
    const startTime = performance.now();
    
    await viewportManager.zoomTo(
      ZoomLevel.ROOM,
      { x: 100, y: 100 },
      200
    );
    
    const duration = performance.now() - startTime;
    expect(duration).toBeLessThan(200);
  });

  it('should maintain 60fps during pan', async () => {
    const frames = [];
    
    const measureFrame = () => {
      frames.push(performance.now());
      if (frames.length < 60) {
        requestAnimationFrame(measureFrame);
      }
    };
    
    requestAnimationFrame(measureFrame);
    
    await viewportManager.panTo({ x: 200, y: 200 }, 1000);
    
    // Check frame times
    const frameTimes = frames.map((time, i) => 
      i > 0 ? time - frames[i - 1] : 0
    ).filter(t => t > 0);
    
    const avgFrameTime = frameTimes.reduce((a, b) => a + b) / frameTimes.length;
    expect(avgFrameTime).toBeLessThan(17); // 60fps = 16.67ms per frame
  });

  it('should handle 10,000 objects at building scale', async () => {
    // Create test data
    const objects = generateTestObjects(10000);
    
    // Load at building scale
    const startTime = performance.now();
    const visible = await scaleEngine.getVisibleObjects(
      testViewport,
      ZoomLevel.BUILDING
    );
    const duration = performance.now() - startTime;
    
    expect(visible.length).toBeLessThanOrEqual(1000); // Detail budget
    expect(duration).toBeLessThan(100); // Fast query
  });
});
```

### Load Testing

```yaml
# k6 load test script
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 1000 }, // Spike to 1000
    { duration: '5m', target: 1000 }, // Stay at 1000
    { duration: '2m', target: 0 },    // Ramp down
  ],
};

export default function() {
  // Test viewport query at different scales
  const scales = [10, 1, 0.1, 0.01, 0.001];
  const scale = scales[Math.floor(Math.random() * scales.length)];
  
  const response = http.get(
    `${__ENV.API_URL}/api/v1/arxobjects/visible?scale=${scale}&viewport=0,0,100,100`
  );
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has objects': (r) => JSON.parse(r.body).length > 0,
  });
}
```

## Success Metrics & Monitoring

### Key Performance Indicators

```typescript
// monitoring/kpi-tracker.ts

export class FractalKPITracker {
  private metrics = {
    // Performance
    avgZoomTime: new Histogram({ name: 'fractal_zoom_duration_ms' }),
    tileLoadTime: new Histogram({ name: 'fractal_tile_load_ms' }),
    renderFrameTime: new Histogram({ name: 'fractal_frame_time_ms' }),
    
    // Usage
    zoomLevelsUsed: new Counter({ name: 'fractal_zoom_levels_used' }),
    contributionsPerScale: new Counter({ name: 'fractal_contributions_scale' }),
    
    // Quality
    cacheHitRate: new Gauge({ name: 'fractal_cache_hit_rate' }),
    detailAccuracy: new Gauge({ name: 'fractal_detail_accuracy' }),
    
    // Business
    biltEarnedPerScale: new Counter({ name: 'fractal_bilt_earned_scale' }),
    userEngagementTime: new Histogram({ name: 'fractal_engagement_time_s' })
  };

  trackZoomPerformance(duration: number, fromScale: number, toScale: number) {
    this.metrics.avgZoomTime.observe(duration);
    
    // Track which scales are most used
    this.metrics.zoomLevelsUsed.inc({ scale: toScale.toFixed(5) });
    
    // Alert if performance degrades
    if (duration > 200) {
      console.warn(`Zoom performance degraded: ${duration}ms from ${fromScale} to ${toScale}`);
    }
  }
}
```

## Next Immediate Steps

1. **Set up development environment with TimescaleDB and MinIO**
2. **Create database migration scripts for fractal schema**
3. **Implement basic Scale Engine service**
4. **Build proof-of-concept with 3 zoom levels**
5. **Create performance benchmarks**

This roadmap provides a clear path from current state to full fractal implementation while maintaining system stability and performance at each phase.