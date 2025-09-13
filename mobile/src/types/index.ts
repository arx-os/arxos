// Equipment Types
export interface Equipment {
  id: string;
  name: string;
  type: string;
  location?: {
    x: number;
    y: number;
  };
  room_id?: string;
  status: EquipmentStatus;
  notes?: string;
  marked_by?: string;
  marked_at?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  install_date?: string;
  last_service_date?: string;
  ar_anchor_id?: string;
  specifications?: Record<string, any>;
}

export enum EquipmentStatus {
  Normal = 'normal',
  NeedsRepair = 'needs-repair',
  Failed = 'failed',
  Unknown = 'unknown',
}

// AR Types
export interface ARAnchor {
  id: string;
  equipment_id: string;
  building_id: string;
  floor_id?: string;
  room_id?: string;
  platform: 'ios' | 'android';
  anchor_data: string;
  position: Position3D;
  rotation?: Rotation3D;
  scale?: Scale3D;
  confidence?: number;
  tracking_state?: string;
  metadata?: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Position3D {
  x: number;
  y: number;
  z: number;
}

export interface Rotation3D {
  x: number;
  y: number;
  z: number;
}

export interface Scale3D {
  x: number;
  y: number;
  z: number;
}

// Building Types
export interface Building {
  id: string;
  name: string;
  building: string;
  level: number;
  organization_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Room {
  id: string;
  name: string;
  bounds: {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
  };
  equipment_ids: string[];
}

// Auth Types
export interface User {
  id: string;
  email: string;
  name: string;
  organization_id?: string;
  ar_preferences?: ARPreferences;
  ar_tutorial_completed?: boolean;
}

export interface ARPreferences {
  voice_input_enabled: boolean;
  haptic_feedback: boolean;
  auto_save_anchors: boolean;
  ar_quality: 'low' | 'medium' | 'high';
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// API Types
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  meta?: {
    request_id: string;
    timestamp: string;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// AR Session Types
export interface ARSession {
  id: string;
  building_id: string;
  floor_id?: string;
  platform: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  equipment_viewed: number;
  equipment_added: number;
  equipment_updated: number;
  anchors_created: number;
  anchors_updated: number;
}

// Sync Types
export interface SyncOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  entity: 'equipment' | 'anchor' | 'session';
  data: any;
  timestamp: string;
  synced: boolean;
}