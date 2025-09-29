/**
 * Equipment-related type definitions
 */

export interface Equipment {
  id: string;
  name: string;
  type: string;
  status: EquipmentStatus;
  location: EquipmentLocation;
  specifications: EquipmentSpecifications;
  lastUpdated: string;
  lastUpdatedBy: string;
  photos?: string[];
  notes?: string;
}

export type EquipmentStatus = 
  | 'normal' 
  | 'needs-repair' 
  | 'failed' 
  | 'offline' 
  | 'maintenance';

export interface EquipmentLocation {
  buildingId: string;
  floorId: string;
  roomId: string;
  coordinates?: {
    x: number;
    y: number;
    z: number;
  };
  address?: string;
}

export interface EquipmentSpecifications {
  model: string;
  manufacturer: string;
  serialNumber: string;
  installationDate: string;
  warrantyExpiry?: string;
  capacity?: string;
  powerRating?: string;
}

export interface EquipmentStatusUpdate {
  id: string;
  equipmentId: string;
  status: EquipmentStatus;
  notes: string;
  photos: string[];
  location: GPSLocation;
  timestamp: string;
  technicianId: string;
  buildingId: string;
  floorId: string;
  roomId: string;
  syncStatus: SyncStatus;
}

export interface GPSLocation {
  latitude: number;
  longitude: number;
  accuracy: number;
  altitude?: number;
  heading?: number;
  speed?: number;
}

export interface EquipmentSearchRequest {
  query: string;
  buildingId: string;
  filters?: {
    floor?: string;
    room?: string;
    type?: string;
    status?: EquipmentStatus;
  };
  limit?: number;
  offset?: number;
}

export interface EquipmentSearchResponse {
  equipment: Equipment[];
  total: number;
  hasMore: boolean;
}

export interface EquipmentSearchResult {
  equipmentId: string;
  name: string;
  type: string;
  location: string;
  status: EquipmentStatus;
  lastUpdated: string;
}
