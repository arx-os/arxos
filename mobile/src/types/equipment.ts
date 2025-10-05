/**
 * Equipment Types - Core equipment data structures
 */

import { Vector3 } from './SpatialTypes';

export interface Equipment {
  id: string;
  name: string;
  type: string;
  model?: string;
  manufacturer?: string;
  status: EquipmentStatus;
  location?: Vector3;
  buildingId: string;
  floorId?: string;
  roomId?: string;
  installationDate?: Date;
  lastMaintenance?: Date;
  nextMaintenance?: Date;
  criticality?: 'low' | 'medium' | 'high' | 'critical';
  maintenanceNotes?: string;
  createdAt: Date;
  updatedAt: Date;
}

export enum EquipmentStatus {
  OPERATIONAL = 'operational',
  MAINTENANCE = 'maintenance',
  OFFLINE = 'offline',
  NEEDS_REPAIR = 'needs_repair',
  FAILED = 'failed',
  TESTING = 'testing',
  STANDBY = 'standby'
}

export interface EquipmentFilter {
  buildingId?: string;
  floorId?: string;
  roomId?: string;
  type?: string;
  status?: EquipmentStatus;
  criticality?: string;
  limit?: number;
  offset?: number;
}

export interface EquipmentSearchResult {
  equipment: Equipment[];
  totalCount: number;
  searchTime: number;
}

export interface EquipmentSearchRequest {
  query?: string;
  filters?: EquipmentFilter;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface EquipmentSearchResponse {
  results: EquipmentSearchResult;
  success: boolean;
  message?: string;
}

export interface EquipmentStatusUpdate {
  equipmentId: string;
  status: EquipmentStatus;
  notes?: string;
  updatedBy: string;
  updatedAt: Date;
}

export interface GPSLocation {
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;
  heading?: number;
  speed?: number;
  timestamp: Date;
}