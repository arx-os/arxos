import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Cache } from 'cache-manager';
import { Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import PQueue from 'p-queue';
import * as LRU from 'lru-cache';

import { TileCache } from '../../entities/tile-cache.entity';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';

export interface TileCoordinate {
  z: number; // Zoom level
  x: number; // X tile coordinate
  y: number; // Y tile coordinate
}

export interface TileData {
  coordinate: TileCoordinate;
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
  objects: FractalArxObject[];
  vectorData?: VectorTileData;
  metadata: {
    scale: number;
    generatedAt: Date;
    objectCount: number;
    dataSize: number;
    compressed: boolean;
  };
}

export interface VectorTileData {
  layers: {
    [layerName: string]: {
      features: any[];
      extent: number;
      version: number;
    };
  };
}

export interface TileRequest {
  coordinate: TileCoordinate;
  scale: number;
  priority: 'immediate' | 'high' | 'normal' | 'low';
  callback?: (tile: TileData) => void;
}

@Injectable()
export class AdvancedTileLoaderService {
  private readonly logger = new Logger(AdvancedTileLoaderService.name);
  
  // Multi-level cache
  private readonly memoryCache: LRU<string, TileData>;
  private readonly loadingTiles: Map<string, Promise<TileData>>;
  private readonly tileQueue: PQueue;
  
  // Configuration
  private readonly maxTileSize: number;
  private readonly vectorTileThreshold: number;
  private readonly compressionThreshold: number;
  
  constructor(
    @InjectRepository(TileCache)
    private readonly tileCacheRepository: Repository<TileCache>,
    @InjectRepository(FractalArxObject)
    private readonly arxObjectRepository: Repository<FractalArxObject>,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private readonly configService: ConfigService,
    private readonly eventEmitter: EventEmitter2,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    // Initialize memory cache with size limit
    this.memoryCache = new LRU<string, TileData>({
      max: 500, // Maximum 500 tiles in memory
      ttl: 1000 * 60 * 5, // 5 minutes TTL
      updateAgeOnGet: true,
      updateAgeOnHas: true,
      sizeCalculation: (tile) => tile.metadata.dataSize,
      maxSize: 100 * 1024 * 1024, // 100MB max memory
      dispose: (tile, key) => {
        this.logger.debug(`Evicting tile ${key} from memory cache`);
      },
    });
    
    // Track loading tiles to prevent duplicate requests
    this.loadingTiles = new Map();
    
    // Priority queue for tile loading
    this.tileQueue = new PQueue({
      concurrency: 6, // Load up to 6 tiles simultaneously
      timeout: 5000, // 5 second timeout per tile
      throwOnTimeout: false,
    });
    
    // Configuration
    this.maxTileSize = this.configService.get('tiles.maxSize', 512);
    this.vectorTileThreshold = this.configService.get('tiles.vectorThreshold', 100);
    this.compressionThreshold = this.configService.get('tiles.compressionThreshold', 1024);
  }

  /**
   * Load a tile with multi-level caching
   */
  async loadTile(request: TileRequest): Promise<TileData> {
    const startTime = Date.now();
    const tileKey = this.getTileKey(request.coordinate, request.scale);
    
    // Level 1: Memory cache
    const memoryCached = this.memoryCache.get(tileKey);
    if (memoryCached) {
      this.performanceMonitor.recordCacheHit('tile-memory');
      this.emitTileLoaded(memoryCached, Date.now() - startTime, 'memory');
      return memoryCached;
    }
    
    // Check if already loading
    const loading = this.loadingTiles.get(tileKey);
    if (loading) {
      return loading;
    }
    
    // Create loading promise
    const loadPromise = this.loadTileWithPriority(request);
    this.loadingTiles.set(tileKey, loadPromise);
    
    try {
      const tile = await loadPromise;
      this.memoryCache.set(tileKey, tile);
      return tile;
    } finally {
      this.loadingTiles.delete(tileKey);
    }
  }

  /**
   * Load tile with priority queue
   */
  private async loadTileWithPriority(request: TileRequest): Promise<TileData> {
    const priority = this.getPriorityValue(request.priority);
    
    return this.tileQueue.add(
      async () => {
        const startTime = Date.now();
        const tileKey = this.getTileKey(request.coordinate, request.scale);
        
        // Level 2: Redis cache
        try {
          const redisCached = await this.cacheManager.get<TileData>(tileKey);
          if (redisCached) {
            this.performanceMonitor.recordCacheHit('tile-redis');
            this.emitTileLoaded(redisCached, Date.now() - startTime, 'redis');
            return redisCached;
          }
        } catch (error) {
          this.logger.warn(`Redis cache error for tile ${tileKey}:`, error);
        }
        
        // Level 3: Database cache
        const dbCached = await this.loadFromDatabase(request.coordinate, request.scale);
        if (dbCached) {
          this.performanceMonitor.recordCacheHit('tile-database');
          await this.cacheManager.set(tileKey, dbCached, 300000); // 5 min Redis TTL
          this.emitTileLoaded(dbCached, Date.now() - startTime, 'database');
          return dbCached;
        }
        
        // Level 4: Generate new tile
        this.performanceMonitor.recordCacheMiss('tile');
        const newTile = await this.generateTile(request.coordinate, request.scale);
        
        // Cache in all levels
        await this.cacheTile(newTile, tileKey);
        
        const duration = Date.now() - startTime;
        this.performanceMonitor.recordQueryPerformance('tile-generation', duration, newTile.objects.length);
        this.emitTileLoaded(newTile, duration, 'generated');
        
        if (request.callback) {
          request.callback(newTile);
        }
        
        return newTile;
      },
      { priority },
    );
  }

  /**
   * Generate a new tile from source data
   */
  private async generateTile(
    coordinate: TileCoordinate,
    scale: number,
  ): Promise<TileData> {
    const bounds = this.calculateTileBounds(coordinate);
    
    // Query objects in tile bounds
    const objects = await this.queryTileObjects(bounds, scale);
    
    // Determine if we should use vector tiles
    const useVectorTile = objects.length > this.vectorTileThreshold;
    
    // Generate vector data if needed
    let vectorData: VectorTileData | undefined;
    if (useVectorTile) {
      vectorData = await this.generateVectorTileData(objects, bounds);
    }
    
    // Calculate data size
    const dataSize = this.calculateDataSize(objects, vectorData);
    
    // Compress if necessary
    const shouldCompress = dataSize > this.compressionThreshold;
    
    const tile: TileData = {
      coordinate,
      bounds,
      objects: useVectorTile ? this.simplifyObjectsForVector(objects) : objects,
      vectorData,
      metadata: {
        scale,
        generatedAt: new Date(),
        objectCount: objects.length,
        dataSize,
        compressed: shouldCompress,
      },
    };
    
    return tile;
  }

  /**
   * Query objects within tile bounds
   */
  private async queryTileObjects(
    bounds: TileData['bounds'],
    scale: number,
  ): Promise<FractalArxObject[]> {
    return this.arxObjectRepository
      .createQueryBuilder('obj')
      .where('obj.minScale <= :scale AND obj.maxScale >= :scale', { scale })
      .andWhere(
        `ST_Intersects(
          obj.geom,
          ST_MakeEnvelope(:minX, :minY, :maxX, :maxY, 4326)
        )`,
        bounds,
      )
      .orderBy('obj.importanceLevel', 'ASC')
      .limit(this.maxTileSize)
      .getMany();
  }

  /**
   * Generate vector tile data for efficient rendering
   */
  private async generateVectorTileData(
    objects: FractalArxObject[],
    bounds: TileData['bounds'],
  ): Promise<VectorTileData> {
    const layers: VectorTileData['layers'] = {};
    
    // Group objects by type for layering
    const objectsByType = this.groupObjectsByType(objects);
    
    for (const [type, typeObjects] of Object.entries(objectsByType)) {
      layers[type] = {
        features: typeObjects.map(obj => this.objectToVectorFeature(obj, bounds)),
        extent: 4096, // Standard vector tile extent
        version: 2,
      };
    }
    
    return { layers };
  }

  /**
   * Convert ArxObject to vector tile feature
   */
  private objectToVectorFeature(
    obj: FractalArxObject,
    bounds: TileData['bounds'],
  ): any {
    // Convert coordinates to tile-relative coordinates (0-4096)
    const tileWidth = bounds.maxX - bounds.minX;
    const tileHeight = bounds.maxY - bounds.minY;
    
    const relativeX = ((Number(obj.positionX) - bounds.minX) / tileWidth) * 4096;
    const relativeY = ((Number(obj.positionY) - bounds.minY) / tileHeight) * 4096;
    
    return {
      id: obj.id,
      type: 'Point',
      geometry: [Math.round(relativeX), Math.round(relativeY)],
      properties: {
        type: obj.objectType,
        name: obj.name,
        importance: obj.importanceLevel,
        optimalScale: obj.optimalScale,
      },
    };
  }

  /**
   * Simplify objects for vector tile representation
   */
  private simplifyObjectsForVector(objects: FractalArxObject[]): FractalArxObject[] {
    // Return only essential properties for vector tiles
    return objects.map(obj => ({
      ...obj,
      properties: {}, // Remove heavy properties
      tags: [], // Remove tags
    }));
  }

  /**
   * Cache tile in multiple layers
   */
  private async cacheTile(tile: TileData, key: string): Promise<void> {
    // Cache in Redis
    try {
      await this.cacheManager.set(key, tile, 300000); // 5 minutes
    } catch (error) {
      this.logger.warn(`Failed to cache tile in Redis: ${error}`);
    }
    
    // Cache in database
    try {
      const tileCache = this.tileCacheRepository.create({
        z: tile.coordinate.z,
        x: tile.coordinate.x,
        y: tile.coordinate.y,
        scale: tile.metadata.scale,
        bounds: {
          type: 'Polygon',
          coordinates: [[
            [tile.bounds.minX, tile.bounds.minY],
            [tile.bounds.maxX, tile.bounds.minY],
            [tile.bounds.maxX, tile.bounds.maxY],
            [tile.bounds.minX, tile.bounds.maxY],
            [tile.bounds.minX, tile.bounds.minY],
          ]],
        },
        objectCount: tile.metadata.objectCount,
        objects: tile.objects.map(obj => ({
          id: obj.id,
          type: obj.objectType,
          x: obj.positionX,
          y: obj.positionY,
        })),
        expiresAt: new Date(Date.now() + 3600000), // 1 hour
      });
      
      await this.tileCacheRepository.save(tileCache);
    } catch (error) {
      this.logger.warn(`Failed to cache tile in database: ${error}`);
    }
  }

  /**
   * Load tile from database cache
   */
  private async loadFromDatabase(
    coordinate: TileCoordinate,
    scale: number,
  ): Promise<TileData | null> {
    const cached = await this.tileCacheRepository.findOne({
      where: {
        z: coordinate.z,
        x: coordinate.x,
        y: coordinate.y,
      },
    });
    
    if (!cached || cached.expiresAt < new Date()) {
      return null;
    }
    
    // Update hit count
    await this.tileCacheRepository.update(
      { z: coordinate.z, x: coordinate.x, y: coordinate.y },
      { hitCount: () => 'hit_count + 1', lastHit: new Date() },
    );
    
    // Convert back to TileData
    const bounds = this.calculateTileBounds(coordinate);
    
    return {
      coordinate,
      bounds,
      objects: cached.objects as any[], // Simplified objects from cache
      metadata: {
        scale,
        generatedAt: cached.createdAt,
        objectCount: cached.objectCount,
        dataSize: 0, // Not stored in DB cache
        compressed: false,
      },
    };
  }

  /**
   * Calculate tile bounds from coordinates
   */
  private calculateTileBounds(coordinate: TileCoordinate): TileData['bounds'] {
    const tileSize = 360 / Math.pow(2, coordinate.z);
    return {
      minX: coordinate.x * tileSize - 180,
      maxX: (coordinate.x + 1) * tileSize - 180,
      minY: coordinate.y * tileSize - 90,
      maxY: (coordinate.y + 1) * tileSize - 90,
    };
  }

  /**
   * Get priority value for queue
   */
  private getPriorityValue(priority: TileRequest['priority']): number {
    switch (priority) {
      case 'immediate': return 0;
      case 'high': return 1;
      case 'normal': return 2;
      case 'low': return 3;
      default: return 2;
    }
  }

  /**
   * Generate tile key for caching
   */
  private getTileKey(coordinate: TileCoordinate, scale: number): string {
    return `tile:${coordinate.z}:${coordinate.x}:${coordinate.y}:${scale.toFixed(8)}`;
  }

  /**
   * Group objects by type
   */
  private groupObjectsByType(
    objects: FractalArxObject[],
  ): Record<string, FractalArxObject[]> {
    return objects.reduce((groups, obj) => {
      const type = obj.objectType;
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(obj);
      return groups;
    }, {} as Record<string, FractalArxObject[]>);
  }

  /**
   * Calculate data size for compression decision
   */
  private calculateDataSize(
    objects: FractalArxObject[],
    vectorData?: VectorTileData,
  ): number {
    let size = JSON.stringify(objects).length;
    if (vectorData) {
      size += JSON.stringify(vectorData).length;
    }
    return size;
  }

  /**
   * Emit tile loaded event
   */
  private emitTileLoaded(
    tile: TileData,
    duration: number,
    source: 'memory' | 'redis' | 'database' | 'generated',
  ): void {
    this.eventEmitter.emit('tile.loaded', {
      coordinate: tile.coordinate,
      scale: tile.metadata.scale,
      objectCount: tile.metadata.objectCount,
      duration,
      source,
    });
  }

  /**
   * Clear all caches
   */
  async clearCaches(): Promise<void> {
    this.memoryCache.clear();
    this.loadingTiles.clear();
    await this.cacheManager.reset();
    this.logger.log('All tile caches cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): any {
    return {
      memory: {
        size: this.memoryCache.size,
        calculatedSize: this.memoryCache.calculatedSize,
      },
      loading: this.loadingTiles.size,
      queue: {
        size: this.tileQueue.size,
        pending: this.tileQueue.pending,
      },
    };
  }
}