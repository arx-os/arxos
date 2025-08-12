import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { ConfigService } from '@nestjs/config';
import { Cache } from 'cache-manager';
import { Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import PQueue from 'p-queue';

import { ArxObjectDetail, DetailLevel, DetailType } from '../../entities/arxobject-detail.entity';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';

export interface DetailRequest {
  objectId: string;
  detailLevel: DetailLevel;
  detailType: DetailType;
  priority: 'critical' | 'high' | 'normal' | 'low' | 'background';
  requesterInfo?: {
    userId?: string;
    sessionId?: string;
    viewportId?: string;
  };
}

export interface DetailLoadResult {
  objectId: string;
  detailLevel: DetailLevel;
  detailType: DetailType;
  data: Record<string, any>;
  loadTime: number;
  source: 'cache' | 'database' | 'generated';
  compressed: boolean;
}

export interface FrameBudget {
  remainingTime: number; // ms
  maxItems: number;
  processedItems: number;
}

export interface LoadingStrategy {
  name: 'immediate' | 'progressive' | 'lazy' | 'background';
  batchSize: number;
  frameTimeout: number;
  priority: number;
}

@Injectable()
export class ProgressiveDetailLoaderService {
  private readonly logger = new Logger(ProgressiveDetailLoaderService.name);
  
  // Processing queues by priority
  private readonly criticalQueue: PQueue;
  private readonly highQueue: PQueue;
  private readonly normalQueue: PQueue;
  private readonly lowQueue: PQueue;
  private readonly backgroundQueue: PQueue;
  
  // Frame budget management
  private readonly targetFrameTime = 16; // 60fps = 16.67ms per frame
  private readonly maxProcessingTime = 10; // Max 10ms for detail loading per frame
  
  // Loading strategies
  private readonly loadingStrategies: Map<string, LoadingStrategy>;
  
  // Statistics
  private readonly stats = {
    totalRequests: 0,
    cacheHits: 0,
    cacheMisses: 0,
    averageLoadTime: 0,
    frameTimeExceeded: 0,
  };
  
  constructor(
    @InjectRepository(ArxObjectDetail)
    private readonly detailRepository: Repository<ArxObjectDetail>,
    @InjectRepository(FractalArxObject)
    private readonly arxObjectRepository: Repository<FractalArxObject>,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private readonly eventEmitter: EventEmitter2,
    private readonly configService: ConfigService,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    // Initialize priority queues
    this.criticalQueue = new PQueue({ concurrency: 10, timeout: 1000 });
    this.highQueue = new PQueue({ concurrency: 6, timeout: 2000 });
    this.normalQueue = new PQueue({ concurrency: 4, timeout: 5000 });
    this.lowQueue = new PQueue({ concurrency: 2, timeout: 10000 });
    this.backgroundQueue = new PQueue({ concurrency: 1, timeout: 30000 });
    
    // Initialize loading strategies
    this.loadingStrategies = new Map([
      ['immediate', { name: 'immediate', batchSize: 1, frameTimeout: 1, priority: 0 }],
      ['progressive', { name: 'progressive', batchSize: 5, frameTimeout: 8, priority: 1 }],
      ['lazy', { name: 'lazy', batchSize: 10, frameTimeout: 12, priority: 2 }],
      ['background', { name: 'background', batchSize: 20, frameTimeout: 100, priority: 3 }],
    ]);
  }

  /**
   * Load object details with progressive enhancement
   */
  async loadObjectDetails(
    objectId: string,
    scale: number,
    strategy: LoadingStrategy['name'] = 'progressive',
  ): Promise<DetailLoadResult[]> {
    const startTime = Date.now();
    
    // Determine required detail levels based on scale
    const requiredLevels = this.getRequiredDetailLevels(scale);
    
    // Create requests for all detail types at required levels
    const requests: DetailRequest[] = [];
    for (const level of requiredLevels) {
      for (const type of this.getDetailTypesForLevel(level)) {
        requests.push({
          objectId,
          detailLevel: level,
          detailType: type,
          priority: this.calculatePriority(level, type, scale),
        });
      }
    }
    
    // Load details progressively
    const results = await this.loadDetailsProgressively(requests, strategy);
    
    const totalTime = Date.now() - startTime;
    this.logger.debug(
      `Loaded ${results.length} details for object ${objectId} in ${totalTime}ms`,
    );
    
    return results;
  }

  /**
   * Load details progressively with frame budget management
   */
  private async loadDetailsProgressively(
    requests: DetailRequest[],
    strategyName: LoadingStrategy['name'],
  ): Promise<DetailLoadResult[]> {
    const strategy = this.loadingStrategies.get(strategyName)!;
    const results: DetailLoadResult[] = [];
    
    // Sort requests by priority
    const sortedRequests = requests.sort((a, b) => 
      this.getPriorityValue(a.priority) - this.getPriorityValue(b.priority)
    );
    
    // Process in batches with frame budget
    for (let i = 0; i < sortedRequests.length; i += strategy.batchSize) {
      const batch = sortedRequests.slice(i, i + strategy.batchSize);
      const frameBudget: FrameBudget = {
        remainingTime: strategy.frameTimeout,
        maxItems: strategy.batchSize,
        processedItems: 0,
      };
      
      const batchResults = await this.processBatchWithBudget(batch, frameBudget);
      results.push(...batchResults);
      
      // Yield to browser between batches if needed
      if (strategy.frameTimeout > this.targetFrameTime) {
        await this.yieldToBrowser();
      }
    }
    
    return results;
  }

  /**
   * Process a batch of requests within frame budget
   */
  private async processBatchWithBudget(
    requests: DetailRequest[],
    budget: FrameBudget,
  ): Promise<DetailLoadResult[]> {
    const results: DetailLoadResult[] = [];
    const frameStart = Date.now();
    
    for (const request of requests) {
      const itemStart = Date.now();
      
      // Check if we have budget remaining
      const elapsed = itemStart - frameStart;
      if (elapsed >= budget.remainingTime && results.length > 0) {
        this.logger.debug(`Frame budget exceeded (${elapsed}ms), deferring ${requests.length - results.length} items`);
        this.stats.frameTimeExceeded++;
        break;
      }
      
      try {
        const result = await this.loadSingleDetail(request);
        results.push(result);
        
        budget.processedItems++;
        budget.remainingTime -= (Date.now() - itemStart);
      } catch (error) {
        this.logger.error(`Failed to load detail for ${request.objectId}:`, error);
      }
    }
    
    return results;
  }

  /**
   * Load a single detail with caching
   */
  private async loadSingleDetail(request: DetailRequest): Promise<DetailLoadResult> {
    const startTime = Date.now();
    this.stats.totalRequests++;
    
    const cacheKey = `detail:${request.objectId}:${request.detailLevel}:${request.detailType}`;
    
    // Try cache first
    const cached = await this.cacheManager.get<DetailLoadResult>(cacheKey);
    if (cached) {
      this.stats.cacheHits++;
      this.performanceMonitor.recordCacheHit('detail');
      return {
        ...cached,
        loadTime: Date.now() - startTime,
        source: 'cache',
      };
    }
    
    this.stats.cacheMisses++;
    this.performanceMonitor.recordCacheMiss('detail');
    
    // Load from database
    const detail = await this.detailRepository.findOne({
      where: {
        arxobjectId: request.objectId,
        detailLevel: request.detailLevel,
        detailType: request.detailType,
      },
    });
    
    let result: DetailLoadResult;
    
    if (detail) {
      // Update access statistics
      await this.updateAccessStats(detail);
      
      result = {
        objectId: request.objectId,
        detailLevel: request.detailLevel,
        detailType: request.detailType,
        data: detail.data,
        loadTime: Date.now() - startTime,
        source: 'database',
        compressed: detail.isCompressed,
      };
    } else {
      // Generate detail on demand
      result = await this.generateDetail(request);
    }
    
    // Cache the result
    await this.cacheManager.set(cacheKey, result, 300000); // 5 minutes
    
    // Track performance
    const loadTime = Date.now() - startTime;
    this.updateAverageLoadTime(loadTime);
    this.performanceMonitor.recordQueryPerformance('detail-load', loadTime, 1);
    
    return result;
  }

  /**
   * Generate detail on demand
   */
  private async generateDetail(request: DetailRequest): Promise<DetailLoadResult> {
    const startTime = Date.now();
    
    // Get the object
    const object = await this.arxObjectRepository.findOne({
      where: { id: request.objectId },
    });
    
    if (!object) {
      throw new Error(`Object ${request.objectId} not found`);
    }
    
    // Generate detail based on type and level
    const data = await this.generateDetailData(object, request.detailLevel, request.detailType);
    
    // Store generated detail
    const detail = this.detailRepository.create({
      arxobjectId: request.objectId,
      detailLevel: request.detailLevel,
      detailType: request.detailType,
      data,
      dataSizeBytes: JSON.stringify(data).length,
      isCompressed: false,
    });
    
    await this.detailRepository.save(detail);
    
    return {
      objectId: request.objectId,
      detailLevel: request.detailLevel,
      detailType: request.detailType,
      data,
      loadTime: Date.now() - startTime,
      source: 'generated',
      compressed: false,
    };
  }

  /**
   * Generate detail data based on object, level, and type
   */
  private async generateDetailData(
    object: FractalArxObject,
    level: DetailLevel,
    type: DetailType,
  ): Promise<Record<string, any>> {
    switch (type) {
      case DetailType.VISUAL:
        return this.generateVisualDetail(object, level);
        
      case DetailType.TECHNICAL:
        return this.generateTechnicalDetail(object, level);
        
      case DetailType.SPECIFICATIONS:
        return this.generateSpecificationDetail(object, level);
        
      case DetailType.HISTORY:
        return this.generateHistoryDetail(object, level);
        
      case DetailType.RELATIONSHIPS:
        return this.generateRelationshipDetail(object, level);
        
      case DetailType.SCHEMATIC:
        return this.generateSchematicDetail(object, level);
        
      default:
        return { generated: true, timestamp: new Date().toISOString() };
    }
  }

  /**
   * Generate visual detail
   */
  private async generateVisualDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    const detail: Record<string, any> = {
      type: 'visual',
      level,
      geometry: {
        position: {
          x: object.positionX,
          y: object.positionY,
          z: object.positionZ,
        },
        rotation: {
          x: object.rotationX,
          y: object.rotationY,
          z: object.rotationZ,
        },
      },
    };
    
    // Add level-specific details
    switch (level) {
      case DetailLevel.BASIC:
        detail.shape = 'box';
        detail.color = this.getColorForType(object.objectType);
        break;
        
      case DetailLevel.STANDARD:
        detail.dimensions = {
          width: object.width,
          height: object.height,
          depth: object.depth,
        };
        detail.materials = this.getMaterialsForType(object.objectType);
        break;
        
      case DetailLevel.DETAILED:
        detail.surfaces = this.generateSurfaceDetails(object);
        detail.textures = this.getTexturesForType(object.objectType);
        break;
        
      case DetailLevel.TECHNICAL:
        detail.technical_drawings = this.generateTechnicalDrawings(object);
        detail.annotations = this.generateAnnotations(object);
        break;
        
      case DetailLevel.SCHEMATIC:
        detail.schematic_symbols = this.generateSchematicSymbols(object);
        detail.connection_points = this.generateConnectionPoints(object);
        break;
    }
    
    return detail;
  }

  /**
   * Generate technical detail
   */
  private async generateTechnicalDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    return {
      type: 'technical',
      level,
      specifications: object.properties,
      performance_data: this.generatePerformanceData(object),
      compliance: this.generateComplianceInfo(object),
      maintenance: this.generateMaintenanceInfo(object),
    };
  }

  /**
   * Get required detail levels based on scale
   */
  private getRequiredDetailLevels(scale: number): DetailLevel[] {
    const levels: DetailLevel[] = [DetailLevel.BASIC];
    
    if (scale <= 1.0) levels.push(DetailLevel.STANDARD);
    if (scale <= 0.1) levels.push(DetailLevel.DETAILED);
    if (scale <= 0.01) levels.push(DetailLevel.TECHNICAL);
    if (scale <= 0.001) levels.push(DetailLevel.SCHEMATIC);
    
    return levels;
  }

  /**
   * Get detail types for a given level
   */
  private getDetailTypesForLevel(level: DetailLevel): DetailType[] {
    const types: DetailType[] = [DetailType.VISUAL];
    
    if (level >= DetailLevel.STANDARD) {
      types.push(DetailType.SPECIFICATIONS);
    }
    
    if (level >= DetailLevel.DETAILED) {
      types.push(DetailType.TECHNICAL, DetailType.RELATIONSHIPS);
    }
    
    if (level >= DetailLevel.TECHNICAL) {
      types.push(DetailType.HISTORY);
    }
    
    if (level >= DetailLevel.SCHEMATIC) {
      types.push(DetailType.SCHEMATIC);
    }
    
    return types;
  }

  /**
   * Calculate priority based on level, type, and scale
   */
  private calculatePriority(
    level: DetailLevel,
    type: DetailType,
    scale: number,
  ): DetailRequest['priority'] {
    // Visual details are always high priority
    if (type === DetailType.VISUAL) {
      return level <= DetailLevel.STANDARD ? 'critical' : 'high';
    }
    
    // Technical details based on scale
    if (scale <= 0.001 && type === DetailType.TECHNICAL) {
      return 'high';
    }
    
    // Schematic details at very fine scales
    if (scale <= 0.0001 && type === DetailType.SCHEMATIC) {
      return 'normal';
    }
    
    // Everything else is lower priority
    return level <= DetailLevel.DETAILED ? 'normal' : 'low';
  }

  /**
   * Get numeric priority value
   */
  private getPriorityValue(priority: DetailRequest['priority']): number {
    switch (priority) {
      case 'critical': return 0;
      case 'high': return 1;
      case 'normal': return 2;
      case 'low': return 3;
      case 'background': return 4;
    }
  }

  /**
   * Update access statistics
   */
  private async updateAccessStats(detail: ArxObjectDetail): Promise<void> {
    await this.detailRepository.update(
      { id: detail.id },
      {
        lastAccessed: new Date(),
        accessCount: () => 'access_count + 1',
      },
    );
  }

  /**
   * Update average load time
   */
  private updateAverageLoadTime(loadTime: number): void {
    this.stats.averageLoadTime = 
      (this.stats.averageLoadTime * (this.stats.totalRequests - 1) + loadTime) / 
      this.stats.totalRequests;
  }

  /**
   * Yield to browser to maintain 60fps
   */
  private async yieldToBrowser(): Promise<void> {
    return new Promise(resolve => {
      if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
        (window as any).requestIdleCallback(resolve);
      } else {
        setTimeout(resolve, 0);
      }
    });
  }

  // Helper methods for detail generation
  private getColorForType(type: string): string {
    const colors: Record<string, string> = {
      BUILDING: '#4A90E2',
      ROOM: '#7ED321',
      ELECTRICAL_OUTLET: '#F5A623',
      LIGHT_FIXTURE: '#FFFF00',
      ELECTRICAL_PANEL: '#BD10E0',
    };
    return colors[type] || '#888888';
  }

  private getMaterialsForType(type: string): string[] {
    const materials: Record<string, string[]> = {
      BUILDING: ['concrete', 'steel', 'glass'],
      ROOM: ['drywall', 'paint', 'flooring'],
      ELECTRICAL_OUTLET: ['plastic', 'copper', 'steel'],
    };
    return materials[type] || ['generic'];
  }

  private generateSurfaceDetails(object: FractalArxObject): any {
    return {
      walls: 4,
      openings: 2,
      finish: 'painted',
    };
  }

  private getTexturesForType(type: string): string[] {
    return ['diffuse', 'normal', 'roughness'];
  }

  private generateTechnicalDrawings(object: FractalArxObject): any {
    return {
      plan_view: 'technical_drawing_url',
      elevation: 'elevation_drawing_url',
      section: 'section_drawing_url',
    };
  }

  private generateAnnotations(object: FractalArxObject): any[] {
    return [
      { type: 'dimension', text: '10.5m', position: [0, 0] },
      { type: 'label', text: object.name, position: [0.5, 0.5] },
    ];
  }

  private generateSchematicSymbols(object: FractalArxObject): any {
    return {
      symbol_type: 'electrical',
      symbol_url: 'symbol_library_url',
    };
  }

  private generateConnectionPoints(object: FractalArxObject): any[] {
    return [
      { id: 'input', type: 'electrical', position: [0, 0.5] },
      { id: 'output', type: 'electrical', position: [1, 0.5] },
    ];
  }

  private generatePerformanceData(object: FractalArxObject): any {
    return {
      efficiency: 0.95,
      load_capacity: 100,
      operating_temperature: 20,
    };
  }

  private generateComplianceInfo(object: FractalArxObject): any {
    return {
      codes: ['NEC', 'IBC'],
      certifications: ['UL', 'CE'],
      compliance_status: 'compliant',
    };
  }

  private generateMaintenanceInfo(object: FractalArxObject): any {
    return {
      last_maintenance: '2024-01-15',
      next_maintenance: '2024-07-15',
      maintenance_type: 'routine',
    };
  }

  private async generateSpecificationDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    return {
      manufacturer: 'Generic Corp',
      model: 'Model-123',
      specifications: object.properties,
    };
  }

  private async generateHistoryDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    return {
      installation_date: object.createdAt,
      modifications: [],
      maintenance_history: [],
    };
  }

  private async generateRelationshipDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    return {
      parent: object.parentId,
      children: [],
      connections: [],
    };
  }

  private async generateSchematicDetail(
    object: FractalArxObject,
    level: DetailLevel,
  ): Promise<Record<string, any>> {
    return {
      schematic_type: 'electrical',
      connections: [],
      symbols: [],
    };
  }

  /**
   * Get loading statistics
   */
  getStatistics(): any {
    return {
      ...this.stats,
      queues: {
        critical: { size: this.criticalQueue.size, pending: this.criticalQueue.pending },
        high: { size: this.highQueue.size, pending: this.highQueue.pending },
        normal: { size: this.normalQueue.size, pending: this.normalQueue.pending },
        low: { size: this.lowQueue.size, pending: this.lowQueue.pending },
        background: { size: this.backgroundQueue.size, pending: this.backgroundQueue.pending },
      },
      cacheHitRate: (this.stats.cacheHits / this.stats.totalRequests) || 0,
    };
  }
}