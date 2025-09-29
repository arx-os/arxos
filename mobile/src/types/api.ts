/**
 * API-related type definitions
 */

export interface APIResponse<T = any> {
  data: T;
  meta: {
    timestamp: string;
    requestId: string;
  };
}

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  meta: {
    timestamp: string;
    requestId: string;
  };
}

export interface LoginRequest {
  username: string;
  password: string;
  deviceInfo: DeviceInfo;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
}

export interface DeviceInfo {
  platform: 'ios' | 'android';
  version: string;
  deviceId: string;
  model?: string;
  osVersion?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  organizationId?: string;
  fullName?: string;
}

export interface SyncResult {
  synced: number;
  failed: number;
  errors: string[];
}

export interface SyncStatus {
  lastSync: string;
  pendingUpdates: number;
  syncInProgress: boolean;
}

export type SyncStatusType = 'pending' | 'synced' | 'failed';

export interface SyncQueueItem {
  id: string;
  type: 'equipment_update' | 'spatial_update' | 'photo_upload';
  data: any;
  priority: 'low' | 'medium' | 'high';
  retryCount: number;
  maxRetries: number;
  createdAt: string;
  lastAttempt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
