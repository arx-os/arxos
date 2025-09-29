/**
 * Synchronization-related type definitions
 */

export interface SyncState {
  isOnline: boolean;
  lastSync: string | null;
  pendingUpdates: number;
  syncInProgress: boolean;
  syncErrors: string[];
  queue: SyncQueueItem[];
}

export interface SyncQueueItem {
  id: string;
  type: SyncItemType;
  data: any;
  priority: SyncPriority;
  retryCount: number;
  maxRetries: number;
  createdAt: string;
  lastAttempt: string | null;
  status: SyncItemStatus;
  error?: string;
}

export type SyncItemType = 
  | 'equipment_update' 
  | 'spatial_update' 
  | 'photo_upload' 
  | 'status_update'
  | 'note_update';

export type SyncPriority = 'low' | 'medium' | 'high';

export type SyncItemStatus = 
  | 'pending' 
  | 'processing' 
  | 'completed' 
  | 'failed' 
  | 'cancelled';

export interface SyncResult {
  synced: number;
  failed: number;
  errors: string[];
  duration: number;
}

export interface SyncProgress {
  total: number;
  completed: number;
  failed: number;
  current?: string;
}

export interface ConflictResolution {
  type: 'server_wins' | 'client_wins' | 'merge' | 'manual';
  description: string;
  data: any;
}

export interface SyncSettings {
  autoSync: boolean;
  syncInterval: number;
  maxRetries: number;
  retryDelay: number;
  batchSize: number;
  compressionEnabled: boolean;
}
