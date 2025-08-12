import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, SelectQueryBuilder } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import { Cache } from 'cache-manager';
import { Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';

import { FractalArxObject, ImportanceLevel } from '../../entities/fractal-arxobject.entity';
import { BoundingBoxDto, ViewportQueryDto } from '../../dto/viewport.dto';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';

export interface ScaleLevel {
  name: string;
  scale: number;
  description: string;
}

export interface DetailLevel {
  BASIC: 1;
  STANDARD: 2;
  DETAILED: 3;
  TECHNICAL: 4;
  SCHEMATIC: 5;
}

@Injectable()
export class ScaleEngineService {
  private readonly logger = new Logger(ScaleEngineService.name);
  private readonly scaleLevels: Map<string, number>;
  private readonly defaultDetailBudget: number;

  constructor(
    @InjectRepository(FractalArxObject)
    private readonly arxObjectRepository: Repository<FractalArxObject>,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private readonly configService: ConfigService,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    // Initialize scale levels from config
    this.scaleLevels = new Map(
      Object.entries(this.configService.get('scale.levels')),
    );
    this.defaultDetailBudget = this.configService.get('scale.detailBudget.default');
  }

  /**
   * Get visible ArxObjects for current viewport and zoom level
   */
  async getVisibleObjects(
    viewport: BoundingBoxDto,
    query: ViewportQueryDto,
  ): Promise<FractalArxObject[]> {
    const startTime = Date.now();
    
    // Generate cache key
    const cacheKey = this.generateCacheKey(viewport, query);
    
    // Try cache first
    const cached = await this.cacheManager.get<FractalArxObject[]>(cacheKey);
    if (cached) {
      this.performanceMonitor.recordCacheHit('viewport');
      return cached;
    }

    // Build query
    const queryBuilder = this.buildViewportQuery(viewport, query);
    
    // Execute query
    const results = await queryBuilder.getMany();
    
    // Cache results
    await this.cacheManager.set(cacheKey, results, 300000); // 5 minutes
    
    // Track performance
    const duration = Date.now() - startTime;
    this.performanceMonitor.recordQueryPerformance('viewport', duration, results.length);
    
    if (duration > 100) {
      this.logger.warn(`Slow viewport query: ${duration}ms for ${results.length} objects`);
    }
    
    return results;
  }

  /**
   * Build the viewport query with all filters
   */
  private buildViewportQuery(
    viewport: BoundingBoxDto,
    query: ViewportQueryDto,
  ): SelectQueryBuilder<FractalArxObject> {
    const qb = this.arxObjectRepository.createQueryBuilder('obj');
    
    // Scale range filter
    qb.where('obj.minScale <= :scale AND obj.maxScale >= :scale', {
      scale: query.scale,
    });
    
    // Spatial bounds filter using PostGIS
    qb.andWhere(
      `ST_Intersects(
        obj.geom,
        ST_MakeEnvelope(:minX, :minY, :maxX, :maxY, 4326)
      )`,
      {
        minX: viewport.minX,
        minY: viewport.minY,
        maxX: viewport.maxX,
        maxY: viewport.maxY,
      },
    );
    
    // Importance filter
    if (query.importanceFilter) {
      qb.andWhere('obj.importanceLevel <= :importance', {
        importance: query.importanceFilter,
      });
    }
    
    // Type filter
    if (query.types && query.types.length > 0) {
      qb.andWhere('obj.objectType IN (:...types)', {
        types: query.types,
      });
    }
    
    // Order by importance and distance from optimal scale
    qb.orderBy('obj.importanceLevel', 'ASC')
      .addOrderBy(`ABS(obj.optimalScale - ${query.scale})`, 'ASC');
    
    // Apply detail budget
    const budget = query.detailBudget || this.defaultDetailBudget;
    qb.limit(budget);
    
    return qb;
  }

  /**
   * Get detail level for a given zoom scale
   */
  getDetailLevelForScale(scale: number): number {
    if (scale >= this.scaleLevels.get('building')) return 1; // BASIC
    if (scale >= this.scaleLevels.get('floor')) return 2; // STANDARD
    if (scale >= this.scaleLevels.get('room')) return 3; // DETAILED
    if (scale >= this.scaleLevels.get('fixture')) return 4; // TECHNICAL
    return 5; // SCHEMATIC
  }

  /**
   * Materialize child objects when zooming in
   */
  async materializeChildren(
    parentId: string,
    targetScale: number,
    limit: number = 100,
  ): Promise<FractalArxObject[]> {
    const cacheKey = `children:${parentId}:${targetScale}`;
    
    // Check cache
    const cached = await this.cacheManager.get<FractalArxObject[]>(cacheKey);
    if (cached) {
      return cached;
    }
    
    // Query children
    const children = await this.arxObjectRepository
      .createQueryBuilder('obj')
      .where('obj.parentId = :parentId', { parentId })
      .andWhere('obj.minScale <= :scale AND obj.maxScale >= :scale', {
        scale: targetScale,
      })
      .orderBy('obj.importanceLevel', 'ASC')
      .limit(limit)
      .getMany();
    
    // Cache results
    await this.cacheManager.set(cacheKey, children, 300000);
    
    return children;
  }

  /**
   * Get scale statistics for monitoring
   */
  async getScaleStatistics(viewport?: BoundingBoxDto): Promise<any> {
    const query = this.arxObjectRepository
      .createQueryBuilder('obj')
      .select([
        `CASE 
          WHEN obj.optimalScale >= 10.0 THEN 'Campus'
          WHEN obj.optimalScale >= 1.0 THEN 'Building'
          WHEN obj.optimalScale >= 0.1 THEN 'Floor'
          WHEN obj.optimalScale >= 0.01 THEN 'Room'
          WHEN obj.optimalScale >= 0.001 THEN 'Fixture'
          WHEN obj.optimalScale >= 0.0001 THEN 'Component'
          ELSE 'Schematic'
        END as scaleRange`,
        'COUNT(*) as objectCount',
        'AVG(obj.importanceLevel) as avgImportance',
      ])
      .groupBy('scaleRange');
    
    if (viewport) {
      query.where(
        `ST_Intersects(
          obj.geom,
          ST_MakeEnvelope(:minX, :minY, :maxX, :maxY, 4326)
        )`,
        viewport,
      );
    }
    
    return query.getRawMany();
  }

  /**
   * Get natural scale breaks for smooth transitions
   */
  getScaleBreaks(): number[] {
    return Array.from(this.scaleLevels.values()).sort((a, b) => b - a);
  }

  /**
   * Snap to nearest meaningful scale level
   */
  snapToNearestScale(scale: number): number {
    const scales = this.getScaleBreaks();
    return scales.reduce((prev, curr) =>
      Math.abs(curr - scale) < Math.abs(prev - scale) ? curr : prev,
    );
  }

  /**
   * Calculate detail budget based on device capabilities
   */
  calculateDetailBudget(
    deviceMemory?: number,
    deviceCores?: number,
  ): number {
    const config = this.configService.get('scale.detailBudget');
    let budget = config.default;
    
    if (deviceMemory) {
      budget = Math.floor(budget * (deviceMemory / 4));
    }
    
    if (deviceCores) {
      budget = Math.floor(budget * (deviceCores / 4));
    }
    
    return Math.min(Math.max(budget, config.min), config.max);
  }

  /**
   * Generate cache key for viewport query
   */
  private generateCacheKey(
    viewport: BoundingBoxDto,
    query: ViewportQueryDto,
  ): string {
    const parts = [
      'viewport',
      Math.floor(viewport.minX * 1000),
      Math.floor(viewport.minY * 1000),
      Math.floor(viewport.maxX * 1000),
      Math.floor(viewport.maxY * 1000),
      Math.floor(query.scale * 1000),
      query.detailBudget || 'default',
      query.importanceFilter || 'all',
      query.types?.join(',') || 'all',
    ];
    
    return parts.join(':');
  }

  /**
   * Prefetch objects for predicted navigation
   */
  async prefetchArea(
    center: { x: number; y: number },
    radius: number,
    scale: number,
  ): Promise<void> {
    const viewport: BoundingBoxDto = {
      minX: center.x - radius,
      minY: center.y - radius,
      maxX: center.x + radius,
      maxY: center.y + radius,
    };
    
    const query: ViewportQueryDto = {
      scale,
      detailBudget: this.calculateDetailBudget(),
    };
    
    // Prefetch in background
    this.getVisibleObjects(viewport, query).catch((error) => {
      this.logger.error('Prefetch failed:', error);
    });
  }
}