/**
 * Spatial Service - Handles AR and spatial data operations
 * Connects to ArxOS backend spatial API endpoints
 */

import {apiService} from './apiService';
import {logger} from '../utils/logger';

// API Configuration
const SPATIAL_API_BASE = __DEV__ 
  ? 'http://localhost:8080/api/v1/mobile/spatial'
  : 'https://api.arxos.com/v1/mobile/spatial';

export interface SpatialPosition {
  x: number;
  y: number;
  z: number;
}

export interface SpatialAnchor {
  id: string;
  building_id: string;
  position: SpatialPosition;
  equipment_id?: string;
  confidence: number;
  anchor_type: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SpatialMappingRequest {
  building_id: string;
  session_id: string;
  anchors: SpatialAnchor[];
  points: SpatialPoint[];
  metadata?: Record<string, any>;
}

export interface SpatialPoint {
  position: SpatialPosition;
  timestamp: number;
}

export interface NearbyEquipmentRequest {
  building_id: string;
  center_x: number;
  center_y: number;
  center_z: number;
  radius?: number; // Default 10 meters
}

export interface NearbyEquipmentResponse {
  center: SpatialPosition;
  equipment: NearbyEquipmentItem[];
  total_found: number;
  search_radius: number;
}

export interface NearbyEquipmentItem {
  equipment: Record<string, any>;
  distance_meters: number;
  bearing_degrees: number;
}

export interface BuildingsResponse {
  buildings: Building[];
  total: number;
}

export interface Building {
  id: string;
  name: string;
  address: string;
  description?: string;
  has_spatial_coverage: boolean;
  equipment_count: number;
  last_scan?: string;
  created_at: string;
  updated_at: string;
}

export interface MappingResult {
  session_id: string;
  building_id: string;
  anchors_created: number;
  points_stored: number;
  coverage_added: number;
  estimated_time: string;
}

export class SpatialService {
  /**
   * Create a new spatial anchor for AR functionality
   */
  async createSpatialAnchor(anchorData: {
    building_id: string;
    position: SpatialPosition;
    equipment_id?: string;
    anchor_type?: string;
    metadata?: Record<string, any>;
  }): Promise<SpatialAnchor> {
    try {
      logger.info('Creating spatial anchor', anchorData);
      
      const response = await apiService.post<{anchor: SpatialAnchor}>(`${SPATIAL_API_BASE}/anchors`, anchorData);
      
      logger.info('Spatial anchor created successfully', { id: response.anchor.id });
      return response.anchor;
    } catch (error: any) {
      logger.error('Failed to create spatial anchor', error);
      throw new Error(error.response?.data?.message || 'Failed to create spatial anchor');
    }
  }

  /**
   * Get spatial anchors for a building
   */
  async getSpatialAnchors(buildingId: string, options?: {
    type?: string;
    has_equipment?: boolean;
    limit?: number;
  }): Promise<SpatialAnchor[]> {
    try {
      logger.info('Fetching spatial anchors', { buildingId, options });
      
      const queryParams = new URLSearchParams();
      if (options?.type) queryParams.append('type', options.type);
      if (options?.has_equipment !== undefined) queryParams.append('has_equipment', options.has_equipment.toString());
      if (options?.limit) queryParams.append('limit', options.limit.toString());
      
      const url = `${SPATIAL_API_BASE}/anchors/building/${buildingId}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await apiService.get<{anchors: SpatialAnchor[], total: number}>(url);
      
      logger.info('Spatial anchors fetched successfully', { count: response.anchors.length });
      return response.anchors;
    } catch (error: any) {
      logger.error('Failed to fetch spatial anchors', error);
      throw new Error(error.response?.data?.message || 'Failed to fetch spatial anchors');
    }
  }

  /**
   * Query nearby equipment within a spatial radius
   */
  async getNearbyEquipment(request: NearbyEquipmentRequest): Promise<NearbyEquipmentResponse> {
    try {
      logger.info('Querying nearby equipment', request);
      
      const queryParams = new URLSearchParams({
        building_id: request.building_id,
        center_x: request.center_x.toString(),
        center_y: request.center_y.toString(),
        center_z: request.center_z.toString(),
        radius: request.radius?.toString() || '10'
      });
      
      const url = `${SPATIAL_API_BASE}/nearby/equipment?${queryParams.toString()}`;
      const response = await apiService.get<NearbyEquipmentResponse>(url);
      
      logger.info('Nearby equipment query successful', { 
        found: response.equipment.length,
        radius: response.search_radius 
      });
      
      return response;
    } catch (error: any) {
      logger.error('Failed to query nearby equipment', error);
      throw new Error(error.response?.data?.message || 'Failed to query nearby equipment');
    }
  }

  /**
   * Upload spatial mapping data from AR session
   */
  async uploadSpatialMapping(mappingData: SpatialMappingRequest): Promise<MappingResult> {
    try {
      logger.info('Uploading spatial mapping data', {
        building_id: mappingData.building_id,
        session_id: mappingData.session_id,
        anchors_count: mappingData.anchors.length,
        points_count: mappingData.points.length
      });
      
      const response = await apiService.post<{mapping_result: MappingResult}>(
        `${SPATIAL_API_BASE}/mapping`,
        mappingData
      );
      
      logger.info('Spatial mapping uploaded successfully', response.mapping_result);
      return response.mapping_result;
    } catch (error: any) {
      logger.error('Failed to upload spatial mapping', error);
      throw new Error(error.response?.data?.message || 'Failed to upload spatial mapping');
    }
  }

  /**
   * Get buildings with spatial data available
   */
  async getSpatialBuildings(): Promise<BuildingsResponse> {
    try {
      logger.info('Fetching spatial buildings');
      
      const response = await apiService.get<BuildingsResponse>(`${SPATIAL_API_BASE}/buildings`);
      
      logger.info('Spatial buildings fetched successfully', { count: response.buildings.length });
      return response;
    } catch (error: any) {
      logger.error('Failed to fetch spatial buildings', error);
      throw new Error(error.response?.data?.message || 'Failed to fetch spatial buildings');
    }
  }

  /**
   * Calculate distance between two spatial positions
   */
  calculateDistance(pos1: SpatialPosition, pos2: SpatialPosition): number {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * Calculate bearing between two spatial positions
   */
  calculateBearing(pos1: SpatialPosition, pos2: SpatialPosition): number {
    const dx = pos2.x - pos1.x;
    const dy = pos2.y - pos1.y;
    return Math.atan2(dy, dx) * (180 / Math.PI);
  }

  /**
   * Convert ARKit position to ArxOS spatial position
   */
  convertARKitPosition(arkitPosition: {x: number, y: number, z: number}): SpatialPosition {
    return {
      x: arkitPosition.x,
      y: arkitPosition.y,
      z: arkitPosition.z
    };
  }

  /**
   * Convert ARCore position to ArxOS spatial position
   */
  convertARCorePosition(arcorePosition: {x: number, y: number, z: number}): SpatialPosition {
    return {
      x: arcorePosition.x,
      y: arcorePosition.y,
      z: arcorePosition.z
    };
  }
}

// Export singleton instance
export const spatialService = new SpatialService();
