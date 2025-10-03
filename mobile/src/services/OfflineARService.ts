/**
 * Offline AR Service - Handles offline AR capabilities and data synchronization
 * Implements Clean Architecture with domain-driven design
 */

import { 
  SpatialAnchor, 
  SpatialConflict, 
  SpatialResolution, 
  SpatialDataUpdate,
  ARSessionMetrics
} from '../domain/AREntities';
import { Vector3, SpatialUtils } from '../types/SpatialTypes';
import { Equipment } from '../types/Equipment';
import { LocalStorageService } from './LocalStorageService';
import { SyncService } from './SyncService';
import { Logger } from '../utils/Logger';

export class OfflineARService {
  private readonly MAX_CACHE_SIZE = 1000; // Maximum number of equipment items to cache
  private readonly CACHE_EXPIRY_HOURS = 24; // Cache expiry time in hours
  private readonly CONFLICT_RESOLUTION_TIMEOUT = 30000; // 30 seconds
  
  constructor(
    private localStorageService: LocalStorageService,
    private syncService: SyncService,
    private logger: Logger
  ) {}
  
  /**
   * Cache equipment data for offline AR functionality
   */
  async cacheEquipmentForAR(buildingId: string): Promise<void> {
    try {
      this.logger.info('Caching equipment for offline AR', { buildingId });
      
      // Get equipment data from local storage
      const equipment = await this.localStorageService.getEquipmentByBuilding(buildingId);
      
      if (equipment.length > this.MAX_CACHE_SIZE) {
        this.logger.warn('Equipment cache size limit exceeded', { 
          buildingId, 
          equipmentCount: equipment.length,
          maxSize: this.MAX_CACHE_SIZE 
        });
        
        // Cache only the most important equipment
        equipment.sort((a, b) => this.getEquipmentPriority(b) - this.getEquipmentPriority(a));
        equipment.splice(this.MAX_CACHE_SIZE);
      }
      
      // Store with spatial indexing for AR queries
      await this.localStorageService.storeEquipmentWithSpatialIndex(equipment);
      
      // Cache AR-specific metadata
      const arMetadata = equipment.map(eq => ({
        id: eq.id,
        name: eq.name,
        type: eq.type,
        position: eq.location,
        arVisibility: this.calculateARVisibility(eq),
        lastUpdated: eq.updatedAt,
        priority: this.getEquipmentPriority(eq),
        cacheExpiry: new Date(Date.now() + this.CACHE_EXPIRY_HOURS * 60 * 60 * 1000)
      }));
      
      await this.localStorageService.storeARMetadata(arMetadata);
      
      // Cache spatial anchors if available
      const spatialAnchors = await this.localStorageService.getSpatialAnchorsByBuilding(buildingId);
      await this.localStorageService.storeSpatialAnchorsForAR(spatialAnchors);
      
      this.logger.info('Equipment cached for offline AR', { 
        buildingId, 
        equipmentCount: equipment.length,
        spatialAnchorsCount: spatialAnchors.length 
      });
      
    } catch (error) {
      this.logger.error('Failed to cache equipment for offline AR', { error, buildingId });
      throw new Error(`Equipment caching failed: ${error.message}`);
    }
  }
  
  /**
   * Store spatial anchor for offline use
   */
  async storeSpatialAnchor(anchor: SpatialAnchor): Promise<void> {
    try {
      this.logger.info('Storing spatial anchor for offline use', { anchorId: anchor.id });
      
      // Validate anchor data
      if (!this.validateSpatialAnchor(anchor)) {
        throw new Error('Invalid spatial anchor data');
      }
      
      // Store locally
      await this.localStorageService.storeSpatialAnchor(anchor);
      
      // Queue for sync when online
      await this.syncService.queueSpatialAnchor(anchor);
      
      this.logger.info('Spatial anchor stored for offline use', { anchorId: anchor.id });
      
    } catch (error) {
      this.logger.error('Failed to store spatial anchor for offline use', { error, anchorId: anchor.id });
      throw new Error(`Spatial anchor storage failed: ${error.message}`);
    }
  }
  
  /**
   * Resolve spatial conflicts automatically
   */
  async resolveSpatialConflicts(): Promise<void> {
    try {
      this.logger.info('Resolving spatial conflicts');
      
      const conflicts = await this.localStorageService.getSpatialConflicts();
      
      if (conflicts.length === 0) {
        this.logger.info('No spatial conflicts to resolve');
        return;
      }
      
      this.logger.info('Found spatial conflicts', { conflictCount: conflicts.length });
      
      for (const conflict of conflicts) {
        try {
          const resolution = await this.resolveConflict(conflict);
          await this.applyResolution(resolution);
          
          this.logger.info('Spatial conflict resolved', { 
            conflictId: conflict.id, 
            resolutionMethod: resolution.resolutionMethod 
          });
          
        } catch (error) {
          this.logger.error('Failed to resolve spatial conflict', { 
            error, 
            conflictId: conflict.id 
          });
          
          // Mark conflict as failed
          await this.localStorageService.markConflictResolutionFailed(conflict.id, error.message);
        }
      }
      
      this.logger.info('Spatial conflicts resolution completed', { 
        totalConflicts: conflicts.length 
      });
      
    } catch (error) {
      this.logger.error('Failed to resolve spatial conflicts', { error });
      throw new Error(`Conflict resolution failed: ${error.message}`);
    }
  }
  
  /**
   * Sync offline AR data when connection is available
   */
  async syncOfflineARData(): Promise<void> {
    try {
      this.logger.info('Syncing offline AR data');
      
      // Sync spatial anchors
      await this.syncSpatialAnchors();
      
      // Sync spatial data updates
      await this.syncSpatialDataUpdates();
      
      // Sync equipment status updates
      await this.syncEquipmentStatusUpdates();
      
      // Resolve any remaining conflicts
      await this.resolveSpatialConflicts();
      
      this.logger.info('Offline AR data sync completed');
      
    } catch (error) {
      this.logger.error('Failed to sync offline AR data', { error });
      throw new Error(`AR data sync failed: ${error.message}`);
    }
  }
  
  /**
   * Get cached equipment for AR queries
   */
  async getCachedEquipmentForAR(
    position: Vector3, 
    radius: number, 
    buildingId: string
  ): Promise<Equipment[]> {
    try {
      const cachedEquipment = await this.localStorageService.getCachedEquipmentForAR(
        position, 
        radius, 
        buildingId
      );
      
      // Filter out expired cache entries
      const validEquipment = cachedEquipment.filter(eq => 
        eq.cacheExpiry && eq.cacheExpiry > new Date()
      );
      
      this.logger.info('Retrieved cached equipment for AR', { 
        total: cachedEquipment.length, 
        valid: validEquipment.length 
      });
      
      return validEquipment;
      
    } catch (error) {
      this.logger.error('Failed to get cached equipment for AR', { error });
      throw new Error(`Cached equipment retrieval failed: ${error.message}`);
    }
  }
  
  /**
   * Check if AR data is available offline
   */
  async isARDataAvailableOffline(buildingId: string): Promise<boolean> {
    try {
      const cachedMetadata = await this.localStorageService.getARMetadata(buildingId);
      const hasValidCache = cachedMetadata.some(meta => 
        meta.cacheExpiry && meta.cacheExpiry > new Date()
      );
      
      return hasValidCache;
      
    } catch (error) {
      this.logger.error('Failed to check offline AR data availability', { error });
      return false;
    }
  }
  
  /**
   * Clear expired AR cache
   */
  async clearExpiredARCache(): Promise<void> {
    try {
      this.logger.info('Clearing expired AR cache');
      
      const expiredMetadata = await this.localStorageService.getExpiredARMetadata();
      
      for (const metadata of expiredMetadata) {
        await this.localStorageService.removeARMetadata(metadata.id);
      }
      
      this.logger.info('Expired AR cache cleared', { 
        expiredCount: expiredMetadata.length 
      });
      
    } catch (error) {
      this.logger.error('Failed to clear expired AR cache', { error });
    }
  }
  
  /**
   * Get AR session metrics for offline analysis
   */
  async getARSessionMetrics(sessionId: string): Promise<ARSessionMetrics | null> {
    try {
      return await this.localStorageService.getARSessionMetrics(sessionId);
    } catch (error) {
      this.logger.error('Failed to get AR session metrics', { error, sessionId });
      return null;
    }
  }
  
  /**
   * Store AR session metrics
   */
  async storeARSessionMetrics(metrics: ARSessionMetrics): Promise<void> {
    try {
      await this.localStorageService.storeARSessionMetrics(metrics);
      this.logger.info('AR session metrics stored', { sessionId: metrics.sessionId });
    } catch (error) {
      this.logger.error('Failed to store AR session metrics', { error });
    }
  }
  
  /**
   * Sync spatial anchors
   */
  private async syncSpatialAnchors(): Promise<void> {
    const pendingAnchors = await this.localStorageService.getPendingSpatialAnchors();
    
    for (const anchor of pendingAnchors) {
      try {
        await this.syncService.syncSpatialAnchor(anchor);
        await this.localStorageService.markSpatialAnchorSynced(anchor.id);
      } catch (error) {
        await this.localStorageService.markSpatialAnchorSyncFailed(anchor.id, error.message);
      }
    }
  }
  
  /**
   * Sync spatial data updates
   */
  private async syncSpatialDataUpdates(): Promise<void> {
    const pendingUpdates = await this.localStorageService.getPendingSpatialDataUpdates();
    
    for (const update of pendingUpdates) {
      try {
        await this.syncService.syncSpatialDataUpdate(update);
        await this.localStorageService.markSpatialDataUpdateSynced(update.id);
      } catch (error) {
        await this.localStorageService.markSpatialDataUpdateSyncFailed(update.id, error.message);
      }
    }
  }
  
  /**
   * Sync equipment status updates
   */
  private async syncEquipmentStatusUpdates(): Promise<void> {
    const pendingUpdates = await this.localStorageService.getPendingEquipmentStatusUpdates();
    
    for (const update of pendingUpdates) {
      try {
        await this.syncService.syncEquipmentStatusUpdate(update);
        await this.localStorageService.markEquipmentStatusUpdateSynced(update.id);
      } catch (error) {
        await this.localStorageService.markEquipmentStatusUpdateSyncFailed(update.id, error.message);
      }
    }
  }
  
  /**
   * Resolve individual conflict
   */
  private async resolveConflict(conflict: SpatialConflict): Promise<SpatialResolution> {
    const resolver = new SpatialConflictResolver();
    return await resolver.resolve(conflict);
  }
  
  /**
   * Apply conflict resolution
   */
  private async applyResolution(resolution: SpatialResolution): Promise<void> {
    await this.localStorageService.applySpatialResolution(resolution);
  }
  
  /**
   * Validate spatial anchor data
   */
  private validateSpatialAnchor(anchor: SpatialAnchor): boolean {
    // Check position validity
    const position = anchor.position;
    if (isNaN(position.x) || isNaN(position.y) || isNaN(position.z)) {
      return false;
    }
    
    // Check confidence
    if (anchor.confidence < 0 || anchor.confidence > 1) {
      return false;
    }
    
    // Check required fields
    if (!anchor.id || !anchor.buildingId || !anchor.floorId) {
      return false;
    }
    
    return true;
  }
  
  /**
   * Calculate equipment priority for caching
   */
  private getEquipmentPriority(equipment: Equipment): number {
    let priority = 0;
    
    // Higher priority for critical equipment
    if (equipment.criticality === 'critical') priority += 100;
    else if (equipment.criticality === 'high') priority += 75;
    else if (equipment.criticality === 'medium') priority += 50;
    else priority += 25;
    
    // Higher priority for recently updated equipment
    const daysSinceUpdate = (Date.now() - equipment.updatedAt.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSinceUpdate < 1) priority += 20;
    else if (daysSinceUpdate < 7) priority += 10;
    
    // Higher priority for operational equipment
    if (equipment.status === 'operational') priority += 15;
    
    return priority;
  }
  
  /**
   * Calculate AR visibility for equipment
   */
  private calculateARVisibility(equipment: Equipment): any {
    return {
      isVisible: true,
      distance: 0,
      occlusionLevel: 0,
      lightingCondition: 'good',
      contrast: 1.0,
      lastVisibilityCheck: new Date()
    };
  }
}

/**
 * Spatial Conflict Resolver
 */
class SpatialConflictResolver {
  async resolve(conflict: SpatialConflict): Promise<SpatialResolution> {
    switch (conflict.conflictType) {
      case 'position':
        return this.resolvePositionConflict(conflict);
      case 'orientation':
        return this.resolveOrientationConflict(conflict);
      case 'scale':
        return this.resolveScaleConflict(conflict);
      case 'duplicate':
        return this.resolveDuplicateConflict(conflict);
      default:
        throw new Error(`Unknown conflict type: ${conflict.conflictType}`);
    }
  }
  
  private async resolvePositionConflict(conflict: SpatialConflict): Promise<SpatialResolution> {
    // Use confidence scores and timestamps to resolve
    const bestAnchor = conflict.conflictingAnchors.reduce((best, current) => 
      current.confidence > best.confidence ? current : best
    );
    
    return {
      id: this.generateId(),
      type: 'position',
      resolvedAnchor: bestAnchor,
      resolutionMethod: 'confidence_based',
      confidence: bestAnchor.confidence,
      timestamp: new Date(),
      appliedBy: 'system'
    };
  }
  
  private async resolveOrientationConflict(conflict: SpatialConflict): Promise<SpatialResolution> {
    // Use most recent orientation
    const latestAnchor = conflict.conflictingAnchors.reduce((latest, current) => 
      current.timestamp > latest.timestamp ? current : latest
    );
    
    return {
      id: this.generateId(),
      type: 'orientation',
      resolvedAnchor: latestAnchor,
      resolutionMethod: 'timestamp_based',
      confidence: latestAnchor.confidence,
      timestamp: new Date(),
      appliedBy: 'system'
    };
  }
  
  private async resolveScaleConflict(conflict: SpatialConflict): Promise<SpatialResolution> {
    // Use average scale
    const avgAnchor = this.calculateAverageAnchor(conflict.conflictingAnchors);
    
    return {
      id: this.generateId(),
      type: 'scale',
      resolvedAnchor: avgAnchor,
      resolutionMethod: 'algorithm',
      confidence: avgAnchor.confidence,
      timestamp: new Date(),
      appliedBy: 'system'
    };
  }
  
  private async resolveDuplicateConflict(conflict: SpatialConflict): Promise<SpatialResolution> {
    // Keep the first anchor, remove duplicates
    const primaryAnchor = conflict.conflictingAnchors[0];
    
    return {
      id: this.generateId(),
      type: 'merge',
      resolvedAnchor: primaryAnchor,
      resolutionMethod: 'manual',
      confidence: primaryAnchor.confidence,
      timestamp: new Date(),
      appliedBy: 'system'
    };
  }
  
  private calculateAverageAnchor(anchors: SpatialAnchor[]): SpatialAnchor {
    const avgPosition = {
      x: anchors.reduce((sum, a) => sum + a.position.x, 0) / anchors.length,
      y: anchors.reduce((sum, a) => sum + a.position.y, 0) / anchors.length,
      z: anchors.reduce((sum, a) => sum + a.position.z, 0) / anchors.length
    };
    
    const avgConfidence = anchors.reduce((sum, a) => sum + a.confidence, 0) / anchors.length;
    
    return {
      ...anchors[0],
      position: avgPosition,
      confidence: avgConfidence
    };
  }
  
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
