# Fractal ArxObject Architecture - System Design

## Executive Summary

This document outlines the revolutionary fractal scaling architecture for ArxObjects in Arxos, enabling seamless visual navigation from building-level to component-detail level within a unified interface. This transforms building data from static documents into a continuous, explorable visual experience where users can contribute at any level of detail.

## Table of Contents

1. [Core Architecture Overview](#core-architecture-overview)
2. [Data Model Design](#data-model-design)
3. [Scale Management System](#scale-management-system)
4. [Lazy Loading Infrastructure](#lazy-loading-infrastructure)
5. [Contribution System](#contribution-system)
6. [Implementation Phases](#implementation-phases)
7. [Technical Requirements](#technical-requirements)
8. [API Design](#api-design)

## Core Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   Web UI    │ │  Mobile App  │ │   AR/VR UI   │         │
│  │  (Zoom UI)  │ │ (Touch Zoom) │ │ (3D Zoom)    │         │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘         │
│         └────────────────┴────────────────┘                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   API Gateway Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Scale-Aware GraphQL/REST API                 │   │
│  │    • Zoom-level routing                              │   │
│  │    • Detail budget management                        │   │
│  │    • Progressive data loading                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Service Layer                               │
│  ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐   │
│  │  Scale Engine │ │  Contribution │ │   Validation    │   │
│  │   Service     │ │    Service    │ │    Service      │   │
│  └───────┬───────┘ └───────┬───────┘ └────────┬────────┘   │
│          │                  │                   │            │
│  ┌───────▼───────┐ ┌───────▼───────┐ ┌────────▼────────┐   │
│  │  Lazy Loader  │ │  BILT Rewards │ │  Peer Review    │   │
│  │    Service    │ │    Engine     │ │    Engine       │   │
│  └───────────────┘ └───────────────┘ └─────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Fractal ArxObject Store                    │   │
│  │    • Hierarchical storage (PostgreSQL + TimescaleDB)  │   │
│  │    • Spatial indexing (PostGIS)                       │   │
│  │    • Binary detail storage (S3/MinIO)                 │   │
│  │    • Cache layer (Redis)                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Scale-First Design**: Every operation considers the current zoom level
2. **Progressive Enhancement**: Start simple, add detail as users zoom
3. **Contribution at Any Level**: Users can add value at their comfort level
4. **Lazy Loading**: Only load what's visible (Google Maps model)
5. **Performance Budget**: Never exceed device capabilities

## Data Model Design

### Fractal ArxObject Structure

```sql
-- Core ArxObject table with scale awareness
CREATE TABLE fractal_arxobjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES fractal_arxobjects(id),
    
    -- Identity
    object_type VARCHAR(255) NOT NULL,
    object_subtype VARCHAR(255),
    
    -- Spatial data
    position_x DECIMAL(12,9) NOT NULL,  -- millimeter precision
    position_y DECIMAL(12,9) NOT NULL,
    position_z DECIMAL(12,9) NOT NULL DEFAULT 0,
    
    -- Scale information
    min_scale DECIMAL(10,8) NOT NULL,  -- Minimum meaningful scale (m/pixel)
    max_scale DECIMAL(10,8) NOT NULL,  -- Maximum meaningful scale
    optimal_scale DECIMAL(10,8) NOT NULL,  -- Best viewing scale
    
    -- Visibility and importance
    importance_level INTEGER NOT NULL DEFAULT 3,
    -- 1=critical (always show), 2=important, 3=detail, 4=optional
    
    -- Physical properties
    width DECIMAL(10,6),   -- millimeters
    height DECIMAL(10,6),  -- millimeters
    depth DECIMAL(10,6),   -- millimeters
    
    -- Metadata
    properties JSONB NOT NULL DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    
    -- Indexes for performance
    INDEX idx_spatial USING GIST (
        ST_MakePoint(position_x, position_y, position_z)
    ),
    INDEX idx_scale_range (min_scale, max_scale),
    INDEX idx_parent_scale (parent_id, min_scale),
    INDEX idx_type_scale (object_type, optimal_scale),
    INDEX idx_importance (importance_level, optimal_scale)
);

-- Scale-based visibility rules
CREATE TABLE visibility_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id),
    
    min_zoom DECIMAL(10,8) NOT NULL,
    max_zoom DECIMAL(10,8) NOT NULL,
    
    render_style JSONB,  -- Style overrides at different scales
    simplification_level INTEGER DEFAULT 0,  -- LOD for rendering
    
    INDEX idx_visibility_zoom (arxobject_id, min_zoom, max_zoom)
);

-- Contributions at different scales
CREATE TABLE scale_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id),
    
    contributor_id UUID NOT NULL,
    contribution_scale DECIMAL(10,8) NOT NULL,  -- Scale at which contributed
    
    contribution_type VARCHAR(100) NOT NULL,
    -- 'geometry', 'specification', 'schematic', 'modification', 'validation'
    
    data JSONB NOT NULL,
    
    -- Quality and rewards
    confidence_score DECIMAL(3,2) DEFAULT 0.5,  -- 0-1 confidence
    peer_validations INTEGER DEFAULT 0,
    bilt_earned DECIMAL(18,8),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_contrib_scale (arxobject_id, contribution_scale),
    INDEX idx_contrib_type (contribution_type, contribution_scale),
    INDEX idx_contributor (contributor_id, created_at DESC)
);

-- Detail levels for lazy loading
CREATE TABLE arxobject_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id),
    
    detail_level INTEGER NOT NULL,
    -- 1=basic, 2=standard, 3=detailed, 4=schematic, 5=microscopic
    
    detail_type VARCHAR(100) NOT NULL,
    -- 'visual', 'technical', 'specifications', 'history', 'relationships'
    
    data JSONB NOT NULL,
    data_size_bytes INTEGER NOT NULL,
    
    -- Storage optimization
    is_compressed BOOLEAN DEFAULT false,
    storage_url TEXT,  -- For large binary data (S3/CDN)
    
    last_accessed TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    
    INDEX idx_detail_level (arxobject_id, detail_level),
    INDEX idx_detail_access (last_accessed, access_count)
);
```

### Scale Level Definitions

```typescript
// Define standard zoom levels for consistency
export enum ZoomLevel {
  CAMPUS = 10.0,        // 10 meters per pixel
  BUILDING = 1.0,       // 1 meter per pixel
  FLOOR = 0.1,          // 10 cm per pixel
  ROOM = 0.01,          // 1 cm per pixel
  FIXTURE = 0.001,      // 1 mm per pixel
  COMPONENT = 0.0001,   // 0.1 mm per pixel
  SCHEMATIC = 0.00001   // 0.01 mm per pixel
}

// Scale ranges for different object types
export const OBJECT_SCALE_RANGES = {
  BUILDING: { min: 1.0, max: 100.0, optimal: 10.0 },
  ROOM: { min: 0.1, max: 10.0, optimal: 1.0 },
  ELECTRICAL_OUTLET: { min: 0.001, max: 1.0, optimal: 0.01 },
  WIRE_CONNECTION: { min: 0.00001, max: 0.001, optimal: 0.0001 }
};
```

## Scale Management System

### Scale Engine Service

```typescript
// services/scale-engine/scale-engine.service.ts

import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

@Injectable()
export class ScaleEngineService {
  constructor(
    @InjectRepository(FractalArxObject)
    private arxObjectRepository: Repository<FractalArxObject>
  ) {}

  /**
   * Get visible ArxObjects for current viewport and zoom level
   */
  async getVisibleObjects(
    viewport: BoundingBox,
    zoomLevel: number,
    detailBudget: number = 1000
  ): Promise<FractalArxObject[]> {
    // Query objects that are visible at this scale
    const query = this.arxObjectRepository
      .createQueryBuilder('obj')
      .where('obj.min_scale <= :zoom AND obj.max_scale >= :zoom', { zoom: zoomLevel })
      .andWhere(
        `ST_Intersects(
          ST_MakePoint(obj.position_x, obj.position_y),
          ST_MakeEnvelope(:minX, :minY, :maxX, :maxY, 4326)
        )`,
        viewport
      )
      .orderBy('obj.importance_level', 'ASC')
      .addOrderBy('obj.optimal_scale', 'DESC')
      .limit(detailBudget);

    return query.getMany();
  }

  /**
   * Calculate what detail level to load based on zoom
   */
  getDetailLevelForZoom(zoomLevel: number): DetailLevel {
    if (zoomLevel >= ZoomLevel.BUILDING) return DetailLevel.BASIC;
    if (zoomLevel >= ZoomLevel.FLOOR) return DetailLevel.STANDARD;
    if (zoomLevel >= ZoomLevel.ROOM) return DetailLevel.DETAILED;
    if (zoomLevel >= ZoomLevel.FIXTURE) return DetailLevel.TECHNICAL;
    return DetailLevel.SCHEMATIC;
  }

  /**
   * Materialize child objects when zooming in
   */
  async materializeChildren(
    parentId: string,
    targetZoom: number
  ): Promise<FractalArxObject[]> {
    return this.arxObjectRepository.find({
      where: {
        parent_id: parentId,
        min_scale: LessThanOrEqual(targetZoom),
        max_scale: GreaterThanOrEqual(targetZoom)
      },
      order: {
        importance_level: 'ASC'
      }
    });
  }
}
```

### Viewport Manager

```typescript
// services/viewport/viewport-manager.ts

export class ViewportManager {
  private currentScale: number;
  private viewport: BoundingBox;
  private detailBudget: number;
  private visibleObjects: Map<string, FractalArxObject>;
  
  constructor(
    private scaleEngine: ScaleEngineService,
    private lazyLoader: LazyLoaderService
  ) {
    this.visibleObjects = new Map();
    this.detailBudget = this.calculateDetailBudget();
  }

  /**
   * Handle zoom change
   */
  async onZoomChange(newScale: number, center: Point): Promise<void> {
    const scaleRatio = newScale / this.currentScale;
    
    if (scaleRatio < 0.5) {
      // Zooming in significantly - load more detail
      await this.loadMoreDetail(newScale);
    } else if (scaleRatio > 2.0) {
      // Zooming out significantly - simplify
      await this.simplifyView(newScale);
    }
    
    this.currentScale = newScale;
    await this.updateVisibleObjects();
  }

  /**
   * Progressive loading as user pans
   */
  async onViewportMove(newViewport: BoundingBox): Promise<void> {
    // Calculate tiles that need loading
    const tilesToLoad = this.calculateNewTiles(this.viewport, newViewport);
    
    // Load in priority order
    for (const tile of tilesToLoad) {
      await this.lazyLoader.loadTile(tile, this.currentScale);
    }
    
    this.viewport = newViewport;
    await this.updateVisibleObjects();
  }

  /**
   * Calculate detail budget based on device capabilities
   */
  private calculateDetailBudget(): number {
    const memory = navigator.deviceMemory || 4; // GB
    const cores = navigator.hardwareConcurrency || 4;
    
    // Base budget
    let budget = 1000;
    
    // Adjust for device capabilities
    budget *= (memory / 4); // Scale by memory
    budget *= (cores / 4);  // Scale by CPU
    
    // Cap at reasonable limits
    return Math.min(Math.max(budget, 500), 5000);
  }
}
```

## Lazy Loading Infrastructure

### Lazy Loader Service

```typescript
// services/lazy-loader/lazy-loader.service.ts

@Injectable()
export class LazyLoaderService {
  private cache: LRUCache<string, any>;
  private loadingQueue: PriorityQueue<LoadRequest>;
  
  constructor(
    private http: HttpClient,
    private cacheService: CacheService,
    private storageService: StorageService
  ) {
    this.cache = new LRUCache({ max: 500, ttl: 1000 * 60 * 5 });
    this.loadingQueue = new PriorityQueue();
  }

  /**
   * Load detail for ArxObject based on zoom level
   */
  async loadObjectDetail(
    objectId: string,
    zoomLevel: number
  ): Promise<ArxObjectDetail> {
    const cacheKey = `${objectId}:${Math.floor(zoomLevel * 1000)}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }
    
    // Determine what detail level we need
    const detailLevel = this.getRequiredDetailLevel(zoomLevel);
    
    // Queue the load request
    const loadRequest: LoadRequest = {
      objectId,
      detailLevel,
      priority: this.calculatePriority(objectId, zoomLevel),
      callback: null
    };
    
    return new Promise((resolve) => {
      loadRequest.callback = resolve;
      this.loadingQueue.enqueue(loadRequest);
      this.processQueue();
    });
  }

  /**
   * Predictive preloading based on user behavior
   */
  async preloadPredictedArea(
    currentViewport: BoundingBox,
    zoomLevel: number,
    zoomDirection: 'in' | 'out' | 'stable'
  ): Promise<void> {
    let areasToPreload: BoundingBox[] = [];
    
    if (zoomDirection === 'in') {
      // Preload higher detail for center area
      areasToPreload.push(this.getCenterArea(currentViewport, 0.5));
    } else if (zoomDirection === 'out') {
      // Preload surrounding areas at lower detail
      areasToPreload.push(...this.getSurroundingAreas(currentViewport));
    } else {
      // Preload adjacent areas at same detail
      areasToPreload.push(...this.getAdjacentAreas(currentViewport));
    }
    
    // Queue preload requests with lower priority
    for (const area of areasToPreload) {
      await this.preloadArea(area, zoomLevel, 'low');
    }
  }

  /**
   * Process loading queue with priority
   */
  private async processQueue(): Promise<void> {
    while (!this.loadingQueue.isEmpty()) {
      const request = this.loadingQueue.dequeue();
      
      try {
        const detail = await this.fetchDetail(request);
        this.cache.set(
          `${request.objectId}:${request.detailLevel}`,
          detail
        );
        request.callback(detail);
      } catch (error) {
        console.error('Failed to load detail:', error);
        request.callback(null);
      }
    }
  }
}
```

### Progressive Data Loading

```typescript
// services/progressive-loader/progressive-loader.ts

export class ProgressiveLoader {
  /**
   * Load data progressively based on importance
   */
  async loadProgressive(
    viewport: BoundingBox,
    scale: number
  ): Promise<LoadResult> {
    const levels = [
      { importance: 1, label: 'critical' },
      { importance: 2, label: 'important' },
      { importance: 3, label: 'detail' },
      { importance: 4, label: 'optional' }
    ];
    
    const results: LoadResult = {
      critical: [],
      important: [],
      detail: [],
      optional: []
    };
    
    for (const level of levels) {
      const objects = await this.loadImportanceLevel(
        viewport,
        scale,
        level.importance
      );
      
      results[level.label] = objects;
      
      // Yield to browser between levels for responsiveness
      await this.yieldToBrowser();
      
      // Check if we should continue loading
      if (!this.shouldContinueLoading()) {
        break;
      }
    }
    
    return results;
  }

  private async yieldToBrowser(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 0));
  }
}
```

## Contribution System

### Multi-Scale Contribution Service

```typescript
// services/contribution/contribution.service.ts

@Injectable()
export class ContributionService {
  /**
   * Accept contribution at any scale level
   */
  async addContribution(
    objectId: string,
    contribution: ScaleContribution,
    userId: string
  ): Promise<ContributionResult> {
    // Validate contribution for the scale
    const validation = await this.validateForScale(
      contribution,
      contribution.scale
    );
    
    if (!validation.isValid) {
      return { success: false, errors: validation.errors };
    }
    
    // Calculate BILT reward based on scale and quality
    const biltReward = this.calculateBiltReward(contribution);
    
    // Store contribution
    const stored = await this.storeContribution({
      ...contribution,
      contributor_id: userId,
      bilt_earned: biltReward,
      confidence_score: validation.confidence
    });
    
    // Update parent object if needed
    if (contribution.updates_parent) {
      await this.propagateToParent(objectId, contribution);
    }
    
    return {
      success: true,
      contributionId: stored.id,
      biltEarned: biltReward
    };
  }

  /**
   * Calculate BILT rewards with scale multipliers
   */
  private calculateBiltReward(contribution: ScaleContribution): number {
    const BASE_REWARDS = {
      geometry: 1.0,
      specification: 1.5,
      schematic: 2.0,
      modification: 2.5,
      validation: 0.5
    };
    
    const SCALE_MULTIPLIERS = {
      [ZoomLevel.BUILDING]: 1.0,
      [ZoomLevel.ROOM]: 1.2,
      [ZoomLevel.FIXTURE]: 1.5,
      [ZoomLevel.COMPONENT]: 1.8,
      [ZoomLevel.SCHEMATIC]: 2.0
    };
    
    const baseReward = BASE_REWARDS[contribution.type] || 1.0;
    const scaleMultiplier = this.getScaleMultiplier(contribution.scale);
    const qualityMultiplier = contribution.quality_score || 1.0;
    
    return baseReward * scaleMultiplier * qualityMultiplier;
  }

  /**
   * Different validation rules for different scales
   */
  private async validateForScale(
    contribution: ScaleContribution,
    scale: number
  ): Promise<ValidationResult> {
    if (scale >= ZoomLevel.BUILDING) {
      // Building level - basic geometric validation
      return this.validateGeometry(contribution);
    } else if (scale >= ZoomLevel.ROOM) {
      // Room level - check spatial conflicts
      return this.validateSpatialConflicts(contribution);
    } else if (scale >= ZoomLevel.FIXTURE) {
      // Fixture level - validate specifications
      return this.validateSpecifications(contribution);
    } else {
      // Component/Schematic level - validate against codes
      return this.validateAgainstCodes(contribution);
    }
  }
}
```

## Implementation Phases

### Phase 1: Foundation (Months 1-2)
**Goal**: Core fractal data model and basic zoom

```typescript
// Phase 1 Deliverables
const phase1 = {
  database: {
    - Create fractal_arxobjects schema
    - Implement spatial indexing
    - Set up scale-based queries
  },
  backend: {
    - Scale Engine Service
    - Basic viewport management
    - Simple lazy loading
  },
  frontend: {
    - Zoom controls (3 levels: building/room/fixture)
    - Pan navigation
    - Basic object rendering
  },
  testing: {
    - Load 1 building with 100 rooms
    - Zoom performance < 200ms
  }
};
```

### Phase 2: Lazy Loading (Months 2-3)
**Goal**: Google Maps-style progressive loading

```typescript
// Phase 2 Deliverables
const phase2 = {
  backend: {
    - Tile-based data loading
    - Predictive preloading
    - Cache management
  },
  frontend: {
    - Smooth zoom transitions
    - Progressive rendering
    - Loading indicators
  },
  optimization: {
    - CDN integration for static data
    - Redis caching layer
    - Request batching
  }
};
```

### Phase 3: Contribution System (Months 3-4)
**Goal**: Enable contributions at multiple scales

```typescript
// Phase 3 Deliverables
const phase3 = {
  features: {
    - Scale-aware contribution tools
    - BILT reward calculation
    - Validation system
  },
  ui: {
    - Context-sensitive toolbars
    - Contribution guides per scale
    - Visual feedback
  },
  rewards: {
    - Scale-based multipliers
    - Quality scoring
    - Peer review system
  }
};
```

### Phase 4: Advanced Features (Months 4-5)
**Goal**: Complete fractal system with all scales

```typescript
// Phase 4 Deliverables
const phase4 = {
  scales: {
    - Add component level (0.1mm)
    - Add schematic level (0.01mm)
    - Temporal dimension
  },
  performance: {
    - WebGL rendering for complex scenes
    - Web Workers for data processing
    - IndexedDB for offline caching
  },
  intelligence: {
    - Cross-scale search
    - Pattern recognition
    - Anomaly detection
  }
};
```

## Technical Requirements

### Performance Targets

```yaml
performance_requirements:
  zoom_transition: < 200ms
  pan_response: < 16ms (60fps)
  initial_load: < 2s
  detail_load: < 500ms
  memory_usage: < 2GB
  cache_hit_rate: > 90%
```

### Scalability Requirements

```yaml
scalability:
  buildings: 10,000+
  objects_per_building: 100,000+
  concurrent_users: 10,000+
  contributions_per_day: 1,000,000+
  detail_levels: 7 (campus to schematic)
```

### Browser Support

```yaml
browsers:
  chrome: 90+
  firefox: 88+
  safari: 14+
  edge: 90+
  mobile_chrome: 90+
  mobile_safari: 14+
```

## API Design

### GraphQL Schema

```graphql
type FractalArxObject {
  id: ID!
  type: String!
  position: Position!
  scale: ScaleInfo!
  details(level: DetailLevel): ObjectDetails
  children(scale: Float!): [FractalArxObject!]
  contributions(scale: Float): [Contribution!]
}

type ScaleInfo {
  minScale: Float!
  maxScale: Float!
  optimalScale: Float!
  currentVisibility(zoom: Float!): Boolean!
}

type Query {
  visibleObjects(
    viewport: ViewportInput!
    zoom: Float!
    detailBudget: Int
  ): [FractalArxObject!]!
  
  objectAtScale(
    id: ID!
    scale: Float!
  ): FractalArxObject
}

type Mutation {
  contributeAtScale(
    objectId: ID!
    scale: Float!
    contribution: ContributionInput!
  ): ContributionResult!
}

type Subscription {
  viewportUpdates(
    viewport: ViewportInput!
    scale: Float!
  ): [FractalArxObject!]!
}
```

### REST Endpoints

```typescript
// REST API for compatibility and caching
interface FractalArxObjectAPI {
  // Get visible objects for viewport
  GET /api/v1/arxobjects/visible
    ?viewport={minX,minY,maxX,maxY}
    &zoom={zoomLevel}
    &budget={maxObjects}
    
  // Get object details at scale
  GET /api/v1/arxobjects/{id}/scale/{scale}
  
  // Get children at scale
  GET /api/v1/arxobjects/{id}/children?scale={scale}
  
  // Submit contribution
  POST /api/v1/arxobjects/{id}/contribute
    body: { scale, type, data }
  
  // Get tile data (for caching)
  GET /api/v1/tiles/{z}/{x}/{y}
}
```

## Next Steps

1. **Review and approve this architecture**
2. **Set up development environment for fractal system**
3. **Create database migrations for new schema**
4. **Implement Phase 1 core components**
5. **Build proof-of-concept with 3 zoom levels**

This architecture provides the foundation for your revolutionary fractal ArxObject vision while maintaining practical implementation phases and performance targets.