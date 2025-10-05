/**
 * Equipment AR Service - Business logic for equipment AR functionality
 * Implements Clean Architecture with domain-driven design
 */

import { AREngine, EquipmentAROverlay, SpatialAnchor, EquipmentStatus as AREngineEquipmentStatus } from '../ar/core/AREngine';
import { 
  EquipmentARMetadata, 
  ARVisibility, 
  EquipmentStatus, 
  SpatialDataUpdate,
  IARContextService,
  ISpatialDataService
} from '../domain/AREntities';
import { Vector3, SpatialUtils } from '../types/SpatialTypes';
import { Equipment } from '../types/equipment';
import { LocalStorageService } from './LocalStorageService';
import { SyncService } from './syncService';
import { AuthService } from './authService';
import { Logger } from "../utils/logger";

export class EquipmentARService {
  private readonly SEARCH_RADIUS = 10.0; // meters
  private readonly MAX_VISIBLE_DISTANCE = 50.0; // meters
  private readonly MIN_CONFIDENCE_THRESHOLD = 0.7;
  
  constructor(
    private arEngine: AREngine,
    private arContextService: IARContextService,
    private spatialDataService: ISpatialDataService,
    private localStorageService: LocalStorageService,
    private syncService: SyncService,
    private authService: AuthService,
    private logger: Logger
  ) {}
  
  /**
   * Identify equipment in AR view based on current position
   */
  async identifyEquipmentInAR(
    position: Vector3, 
    buildingId: string, 
    floorId: string
  ): Promise<Equipment[]> {
    try {
      this.logger.info('Identifying equipment in AR', { position, buildingId, floorId });
      
      // Query nearby equipment from local cache
      const nearbyEquipment = await this.localStorageService.getNearbyEquipment(
        position, 
        buildingId, 
        floorId, 
        this.SEARCH_RADIUS
      );
      
      // Filter by AR visibility criteria
      const visibleEquipment = nearbyEquipment.filter(eq => 
        this.isVisibleInAR(eq, position)
      );
      
      this.logger.info('Equipment identified in AR', { 
        total: nearbyEquipment.length, 
        visible: visibleEquipment.length 
      });
      
      return visibleEquipment;
      
    } catch (error) {
      this.logger.error('Failed to identify equipment in AR', { error: error as Error, position, buildingId, floorId });
      throw new Error(`Equipment identification failed: ${(error as Error).message}`);
    }
  }
  
  /**
   * Update equipment status through AR interface
   */
  async updateEquipmentStatusAR(
    equipmentId: string,
    status: EquipmentStatus,
    position: Vector3,
    notes?: string
  ): Promise<void> {
    try {
      this.logger.info('Updating equipment status via AR', { equipmentId, status });
      
      const currentUser = this.authService.getCurrentUser();
      if (!currentUser) {
        throw new Error('User not authenticated');
      }
      
      const update: EquipmentStatusUpdate = {
        id: this.generateId(),
        equipmentId,
        status,
        notes,
        location: position,
        spatialAnchor: undefined, // No active anchor available
        timestamp: new Date(),
        technicianId: currentUser.id,
        arPlatform: this.arEngine.platform,
        buildingId: '', // No building context available
        floorId: '', // No floor context available
        syncStatus: 'pending'
      };
      
      // Store locally first
      await this.localStorageService.storeEquipmentStatusUpdate(update);
      
      // Queue for sync
      await this.syncService.queueEquipmentStatusUpdate(update);
      
      // Update AR overlay
      await this.updateEquipmentOverlayStatus(equipmentId, status);
      
      this.logger.info('Equipment status updated via AR', { equipmentId, status });
      
    } catch (error) {
      this.logger.error('Failed to update equipment status via AR', { error: error as Error, equipmentId, status });
      throw new Error(`Status update failed: ${(error as Error).message}`);
    }
  }
  
  /**
   * Capture equipment position using AR spatial anchor
   */
  async captureEquipmentPosition(
    equipmentId: string,
    spatialAnchor: SpatialAnchor
  ): Promise<void> {
    try {
      this.logger.info('Capturing equipment position via AR', { equipmentId, spatialAnchorId: spatialAnchor.id });
      
      const currentUser = this.authService.getCurrentUser();
      if (!currentUser) {
        throw new Error('User not authenticated');
      }
      
      const spatialUpdate: SpatialDataUpdate = {
        id: this.generateId(),
        equipmentId,
        spatialAnchor: {
          ...spatialAnchor,
          validationStatus: 'validated',
          lastUpdated: new Date()
        },
        arPlatform: this.arEngine.platform,
        timestamp: new Date(),
        technicianId: currentUser.id,
        buildingId: spatialAnchor.buildingId,
        confidence: spatialAnchor.confidence,
        validationStatus: 'pending',
        syncStatus: 'pending'
      };
      
      // Validate spatial data
      const isValid = await this.validateSpatialData(spatialUpdate);
      if (!isValid) {
        throw new Error('Invalid spatial data');
      }
      
      // Store locally
      await this.localStorageService.storeSpatialDataUpdate(spatialUpdate);
      
      // Queue for sync
      await this.syncService.queueSpatialDataUpdate(spatialUpdate);
      
      // Update equipment location in AR
      await this.updateEquipmentLocationInAR(equipmentId, spatialAnchor.position);
      
      this.logger.info('Equipment position captured via AR', { equipmentId, spatialAnchorId: spatialAnchor.id });
      
    } catch (error) {
      this.logger.error('Failed to capture equipment position via AR', { error: error as Error, equipmentId });
      throw new Error(`Position capture failed: ${(error as Error).message}`);
    }
  }
  
  /**
   * Cache equipment data for offline AR functionality
   */
  async cacheEquipmentForAR(buildingId: string): Promise<void> {
    try {
      this.logger.info('Caching equipment for AR', { buildingId });
      
      // Get equipment data from local storage
      const equipment = await this.localStorageService.getEquipmentByBuilding(buildingId);
      
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
        metadata: this.extractARMetadata(eq)
      }));
      
      await this.localStorageService.storeARMetadata(arMetadata);
      
      this.logger.info('Equipment cached for AR', { buildingId, equipmentCount: equipment.length });
      
    } catch (error) {
      this.logger.error('Failed to cache equipment for AR', { error: error as Error, buildingId });
      throw new Error(`Equipment caching failed: ${(error as Error).message}`);
    }
  }
  
  /**
   * Render equipment overlays in AR scene
   */
  async renderEquipmentOverlays(equipment: Equipment[], position: Vector3): Promise<void> {
    try {
      this.logger.info('Rendering equipment overlays in AR', { equipmentCount: equipment.length });
      
      for (const eq of equipment) {
        if (this.shouldRenderEquipment(eq, position)) {
          const overlay = await this.createEquipmentOverlay(eq, position);
          this.arEngine.addEquipmentOverlay(overlay);
        }
      }
      
      this.logger.info('Equipment overlays rendered in AR', { renderedCount: equipment.length });
      
    } catch (error) {
      this.logger.error('Failed to render equipment overlays in AR', { error });
      throw new Error(`Overlay rendering failed: ${(error as Error).message}`);
    }
  }
  
  /**
   * Update equipment overlay when status changes
   */
  private async updateEquipmentOverlayStatus(equipmentId: string, status: EquipmentStatus): Promise<void> {
    try {
      const equipment = await this.localStorageService.getEquipment(equipmentId);
      if (!equipment) {
        throw new Error(`Equipment not found: ${equipmentId}`);
      }
      
      const context = this.arContextService.getCurrentContext();
      if (!context) {
        throw new Error('No AR context available');
      }
      const overlay = await this.createEquipmentOverlay(equipment, context.currentPosition);
      overlay.status = status as AREngineEquipmentStatus;
      
      this.arEngine.updateEquipmentOverlay(overlay);
      
    } catch (error) {
      this.logger.error('Failed to update equipment overlay status', { error: error as Error, equipmentId, status });
    }
  }
  
  /**
   * Update equipment location in AR scene
   */
  private async updateEquipmentLocationInAR(equipmentId: string, newPosition: Vector3): Promise<void> {
    try {
      const equipment = await this.localStorageService.getEquipment(equipmentId);
      if (!equipment) {
        throw new Error(`Equipment not found: ${equipmentId}`);
      }
      
      const context = this.arContextService.getCurrentContext();
      if (!context) {
        throw new Error('No AR context available');
      }
      const overlay = await this.createEquipmentOverlay(equipment, context.currentPosition);
      overlay.position = newPosition;
      
      this.arEngine.updateEquipmentOverlay(overlay);
      
    } catch (error) {
      this.logger.error('Failed to update equipment location in AR', { error: error as Error, equipmentId });
    }
  }
  
  /**
   * Check if equipment should be visible in AR
   */
  private isVisibleInAR(equipment: Equipment, viewerPosition: Vector3): boolean {
    if (!equipment.location) {
      return false;
    }
    
    const distance = SpatialUtils.distance(viewerPosition, equipment.location);
    
    // Check distance threshold
    if (distance > this.MAX_VISIBLE_DISTANCE) {
      return false;
    }
    
    // Check equipment status
    if (equipment.status === EquipmentStatus.OFFLINE) {
      return false;
    }
    
    // Check AR visibility criteria
    const arVisibility = this.calculateARVisibility(equipment);
    return arVisibility.isVisible && arVisibility.lightingCondition !== 'dark';
  }
  
  /**
   * Calculate AR visibility for equipment
   */
  private calculateARVisibility(equipment: Equipment): ARVisibility {
    // This would integrate with AR engine to get real lighting conditions
    const lightingCondition = this.arEngine.getCurrentPosition() ? 'good' : 'poor';
    
    return {
      isVisible: true,
      distance: 0, // Will be calculated when needed
      occlusionLevel: 0,
      lightingCondition,
      contrast: 1.0,
      lastVisibilityCheck: new Date()
    };
  }
  
  /**
   * Check if equipment should be rendered
   */
  private shouldRenderEquipment(equipment: Equipment, viewerPosition: Vector3): boolean {
    return this.isVisibleInAR(equipment, viewerPosition);
  }
  
  /**
   * Create equipment overlay for AR rendering
   */
  private async createEquipmentOverlay(equipment: Equipment, position: Vector3): Promise<EquipmentAROverlay> {
    const metadata = this.extractARMetadata(equipment);
    const arVisibility = this.calculateARVisibility(equipment);
    
    return {
      equipmentId: equipment.id,
      position: equipment.location || { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0, w: 1 },
      scale: { x: 1, y: 1, z: 1 },
      status: equipment.status as AREngineEquipmentStatus,
      lastUpdated: equipment.updatedAt,
      arVisibility,
      modelType: this.determineModelType(equipment)
    };
  }
  
  /**
   * Extract AR-specific metadata from equipment
   */
  private extractARMetadata(equipment: Equipment): EquipmentARMetadata {
    return {
      name: equipment.name,
      type: equipment.type,
      model: equipment.model || 'Unknown',
      manufacturer: equipment.manufacturer,
      installationDate: equipment.installationDate,
      lastMaintenance: equipment.lastMaintenance,
      nextMaintenance: equipment.nextMaintenance,
      criticality: equipment.criticality || 'medium',
      maintenanceNotes: equipment.maintenanceNotes
    };
  }
  
  /**
   * Determine model type for AR rendering
   */
  private determineModelType(equipment: Equipment): '3D' | '2D' | 'icon' {
    // Logic to determine best model type based on equipment type and available resources
    if (equipment.type === 'HVAC' || equipment.type === 'Electrical') {
      return '3D';
    } else if (equipment.type === 'Plumbing' || equipment.type === 'FireSafety') {
      return '2D';
    } else {
      return 'icon';
    }
  }
  
  /**
   * Validate spatial data before storage
   */
  private async validateSpatialData(spatialUpdate: SpatialDataUpdate): Promise<boolean> {
    // Check confidence threshold
    if (spatialUpdate.confidence < this.MIN_CONFIDENCE_THRESHOLD) {
      return false;
    }
    
    // Check position validity
    const position = spatialUpdate.spatialAnchor.position;
    if (isNaN(position.x) || isNaN(position.y) || isNaN(position.z)) {
      return false;
    }
    
    // Check timestamp validity
    if (spatialUpdate.timestamp > new Date()) {
      return false;
    }
    
    return true;
  }
  
  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Additional interfaces for equipment status updates
export interface EquipmentStatusUpdate {
  id: string;
  equipmentId: string;
  status: EquipmentStatus;
  notes?: string;
  location: Vector3;
  spatialAnchor?: SpatialAnchor;
  timestamp: Date;
  technicianId: string;
  arPlatform: 'ARKit' | 'ARCore';
  buildingId: string;
  floorId: string;
  syncStatus: 'pending' | 'synced' | 'failed';
}
