/**
 * Sync Service - Handles data synchronization for AR functionality
 */

import { SpatialAnchor } from '../domain/AREntities';
import { Logger } from "../utils/logger";
import { SyncQueueItem, SyncResult, SyncItemType, SyncPriority, SyncItemStatus } from '../types/sync';
import { storageService, SyncQueueRecord } from './storageService';
import { apiService } from './apiService';
import { Equipment } from '../types/equipment';
import NetInfo from '@react-native-community/netinfo';
import { v4 as uuidv4 } from 'uuid';

export class SyncService {
  private logger: Logger;
  private isOnline: boolean = true;
  private syncInProgress: boolean = false;
  private maxRetries: number = 3;
  private retryDelay: number = 1000;
  private batchSize: number = 10;

  constructor() {
    this.logger = new Logger('SyncService');
    this.initializeNetworkListener();
  }

  /**
   * Initialize network status listener
   */
  private initializeNetworkListener(): void {
    NetInfo.addEventListener(state => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected || false;
      
      if (wasOffline && this.isOnline) {
        this.logger.info('Network connection restored, starting sync');
        this.syncQueue().catch(error => {
          this.logger.error('Auto-sync failed after network restore', error);
        });
      }
    });
  }

  /**
   * Queue operations for offline sync
   */
  async queueSpatialAnchor(anchor: SpatialAnchor): Promise<void> {
    const queueItem: SyncQueueRecord = {
      id: uuidv4(),
      operation: 'CREATE',
      table: 'spatial_anchors',
      recordId: anchor.id,
      data: anchor,
      retryCount: 0,
      createdAt: new Date().toISOString(),
    };

    await storageService.addToSyncQueue(queueItem);
    this.logger.debug('Spatial anchor queued for sync', { id: anchor.id });
  }

  async queueSpatialDataUpdate(update: any): Promise<void> {
    const queueItem: SyncQueueRecord = {
      id: uuidv4(),
      operation: 'UPDATE',
      table: 'spatial_data',
      recordId: update.id,
      data: update,
      retryCount: 0,
      createdAt: new Date().toISOString(),
    };

    await storageService.addToSyncQueue(queueItem);
    this.logger.debug('Spatial data update queued for sync', { id: update.id });
  }

  async queueEquipmentStatusUpdate(update: any): Promise<void> {
    const queueItem: SyncQueueRecord = {
      id: uuidv4(),
      operation: 'UPDATE',
      table: 'equipment',
      recordId: update.id,
      data: update,
      retryCount: 0,
      createdAt: new Date().toISOString(),
    };

    await storageService.addToSyncQueue(queueItem);
    this.logger.debug('Equipment status update queued for sync', { id: update.id });
  }

  async queuePhotoUpload(photoData: any): Promise<void> {
    const queueItem: SyncQueueRecord = {
      id: uuidv4(),
      operation: 'CREATE',
      table: 'photos',
      recordId: photoData.id,
      data: photoData,
      retryCount: 0,
      createdAt: new Date().toISOString(),
    };

    await storageService.addToSyncQueue(queueItem);
    this.logger.debug('Photo upload queued for sync', { id: photoData.id });
  }

  async queueNoteUpdate(noteData: any): Promise<void> {
    const queueItem: SyncQueueRecord = {
      id: uuidv4(),
      operation: 'UPDATE',
      table: 'equipment_notes',
      recordId: noteData.equipmentId,
      data: noteData,
      retryCount: 0,
      createdAt: new Date().toISOString(),
    };

    await storageService.addToSyncQueue(queueItem);
    this.logger.debug('Note update queued for sync', { equipmentId: noteData.equipmentId });
  }

  /**
   * Sync all queued operations
   */
  async syncQueue(): Promise<SyncResult> {
    if (this.syncInProgress) {
      this.logger.warn('Sync already in progress, skipping');
      return { synced: 0, failed: 0, errors: ['Sync already in progress'], duration: 0 };
    }

    if (!this.isOnline) {
      this.logger.warn('Device is offline, cannot sync');
      return { synced: 0, failed: 0, errors: ['Device is offline'], duration: 0 };
    }

    this.syncInProgress = true;
    const startTime = Date.now();
    const errors: string[] = [];
    let synced = 0;
    let failed = 0;

    try {
      const queue = await storageService.getSyncQueue();
      this.logger.info(`Starting sync of ${queue.length} items`);

      // Process queue in batches
      for (let i = 0; i < queue.length; i += this.batchSize) {
        const batch = queue.slice(i, i + this.batchSize);
        const batchResult = await this.processBatch(batch);
        
        synced += batchResult.synced;
        failed += batchResult.failed;
        errors.push(...batchResult.errors);

        // Small delay between batches to avoid overwhelming the server
        if (i + this.batchSize < queue.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      const duration = Date.now() - startTime;
      this.logger.info(`Sync completed: ${synced} synced, ${failed} failed in ${duration}ms`);

      return { synced, failed, errors, duration };
    } catch (error) {
      this.logger.error('Sync failed with error', error);
      errors.push(`Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return { synced, failed, errors, duration: Date.now() - startTime };
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * Process a batch of sync queue items
   */
  private async processBatch(batch: SyncQueueRecord[]): Promise<{synced: number; failed: number; errors: string[]}> {
    const errors: string[] = [];
    let synced = 0;
    let failed = 0;

    for (const item of batch) {
      try {
        await this.processSyncItem(item);
        await storageService.removeFromSyncQueue(item.id);
        synced++;
        this.logger.debug('Sync item processed successfully', { id: item.id });
      } catch (error) {
        failed++;
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        errors.push(`Item ${item.id}: ${errorMessage}`);
        
        // Update retry count
        const updatedItem = { ...item, retryCount: item.retryCount + 1, lastAttempt: new Date().toISOString() };
        
        if (item.retryCount >= this.maxRetries) {
          this.logger.error('Sync item exceeded max retries, removing from queue', { id: item.id });
          await storageService.removeFromSyncQueue(item.id);
        } else {
          // Update the item in the queue with new retry count
          await storageService.removeFromSyncQueue(item.id);
          await storageService.addToSyncQueue(updatedItem);
        }
      }
    }

    return { synced, failed, errors };
  }

  /**
   * Process a single sync queue item
   */
  private async processSyncItem(item: SyncQueueRecord): Promise<void> {
    this.logger.debug('Processing sync item', { id: item.id, operation: item.operation, table: item.table });

    switch (item.table) {
      case 'spatial_anchors':
        await this.syncSpatialAnchor(item.data);
        break;
      case 'spatial_data':
        await this.syncSpatialDataUpdate(item.data);
        break;
      case 'equipment':
        await this.syncEquipmentStatusUpdate(item.data);
        break;
      case 'photos':
        await this.syncPhotoUpload(item.data);
        break;
      case 'equipment_notes':
        await this.syncNoteUpdate(item.data);
        break;
      default:
        throw new Error(`Unknown table type: ${item.table}`);
    }
  }

  /**
   * Sync individual operations
   */
  async syncSpatialAnchor(anchor: SpatialAnchor): Promise<void> {
    try {
      await apiService.post('/spatial/anchors', anchor);
      this.logger.debug('Spatial anchor synced successfully', { id: anchor.id });
    } catch (error) {
      this.logger.error('Failed to sync spatial anchor', error);
      throw error;
    }
  }

  async syncSpatialDataUpdate(update: any): Promise<void> {
    try {
      await apiService.put(`/spatial/data/${update.id}`, update);
      this.logger.debug('Spatial data update synced successfully', { id: update.id });
    } catch (error) {
      this.logger.error('Failed to sync spatial data update', error);
      throw error;
    }
  }

  async syncEquipmentStatusUpdate(update: any): Promise<void> {
    try {
      await apiService.put(`/equipment/${update.id}/status`, update);
      this.logger.debug('Equipment status update synced successfully', { id: update.id });
    } catch (error) {
      this.logger.error('Failed to sync equipment status update', error);
      throw error;
    }
  }

  async syncPhotoUpload(photoData: any): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('photo', {
        uri: photoData.uri,
        type: photoData.type,
        name: photoData.name,
      } as any);
      formData.append('equipmentId', photoData.equipmentId);
      formData.append('metadata', JSON.stringify(photoData.metadata));

      await apiService.uploadFile('/photos/upload', formData);
      this.logger.debug('Photo upload synced successfully', { id: photoData.id });
    } catch (error) {
      this.logger.error('Failed to sync photo upload', error);
      throw error;
    }
  }

  async syncNoteUpdate(noteData: any): Promise<void> {
    try {
      await apiService.put(`/equipment/${noteData.equipmentId}/notes`, noteData);
      this.logger.debug('Note update synced successfully', { equipmentId: noteData.equipmentId });
    } catch (error) {
      this.logger.error('Failed to sync note update', error);
      throw error;
    }
  }

  /**
   * Sync all data (full sync)
   */
  async syncAllData(): Promise<SyncResult> {
    this.logger.info('Starting full data sync');
    
    // First sync the queue
    const queueResult = await this.syncQueue();
    
    // Then sync any dirty equipment records
    try {
      const allEquipment = await storageService.getAllEquipment();
      const dirtyEquipment = allEquipment.filter(eq => eq.isDirty);
      
      let syncedEquipment = 0;
      for (const equipment of dirtyEquipment) {
        try {
          await apiService.put(`/equipment/${equipment.id}`, equipment);
          // Mark as synced
          equipment.syncedAt = new Date().toISOString();
          equipment.isDirty = false;
          await storageService.saveEquipment(equipment);
          syncedEquipment++;
        } catch (error) {
          this.logger.error('Failed to sync equipment', { id: equipment.id, error });
        }
      }
      
      this.logger.info(`Synced ${syncedEquipment} dirty equipment records`);
    } catch (error) {
      this.logger.error('Failed to sync dirty equipment', error);
    }
    
    return queueResult;
  }

  /**
   * Retry a specific sync item
   */
  async retrySyncItem(itemId: string): Promise<SyncQueueItem> {
    const queue = await storageService.getSyncQueue();
    const item = queue.find(q => q.id === itemId);
    
    if (!item) {
      throw new Error(`Sync item not found: ${itemId}`);
    }

    try {
      await this.processSyncItem(item);
      await storageService.removeFromSyncQueue(itemId);
      
      return {
        id: item.id,
        type: this.mapTableToSyncType(item.table),
        data: item.data,
        priority: 'medium',
        retryCount: item.retryCount,
        maxRetries: this.maxRetries,
        createdAt: item.createdAt,
        lastAttempt: new Date().toISOString(),
        status: 'completed',
      };
    } catch (error) {
      const updatedItem = { ...item, retryCount: item.retryCount + 1, lastAttempt: new Date().toISOString() };
      
      if (item.retryCount >= this.maxRetries) {
        await storageService.removeFromSyncQueue(itemId);
        throw new Error(`Item exceeded max retries: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } else {
        await storageService.removeFromSyncQueue(itemId);
        await storageService.addToSyncQueue(updatedItem);
      }
      
      return {
        id: item.id,
        type: this.mapTableToSyncType(item.table),
        data: item.data,
        priority: 'medium',
        retryCount: updatedItem.retryCount,
        maxRetries: this.maxRetries,
        createdAt: item.createdAt,
        lastAttempt: updatedItem.lastAttempt,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Clear sync errors
   */
  async clearSyncErrors(): Promise<void> {
    // This would typically clear error logs or reset error states
    this.logger.info('Sync errors cleared');
  }

  /**
   * Get sync status
   */
  async getSyncStatus(): Promise<{
    isOnline: boolean;
    syncInProgress: boolean;
    queueLength: number;
    lastSync: string | null;
  }> {
    const queue = await storageService.getSyncQueue();
    const lastSync = await storageService.getSetting('lastSync');
    
    return {
      isOnline: this.isOnline,
      syncInProgress: this.syncInProgress,
      queueLength: queue.length,
      lastSync,
    };
  }

  /**
   * Map table name to sync type
   */
  private mapTableToSyncType(table: string): SyncItemType {
    switch (table) {
      case 'spatial_anchors':
      case 'spatial_data':
        return 'spatial_update';
      case 'equipment':
        return 'equipment_update';
      case 'photos':
        return 'photo_upload';
      case 'equipment_notes':
        return 'note_update';
      default:
        return 'status_update';
    }
  }

  /**
   * Set sync settings
   */
  setSyncSettings(settings: {
    maxRetries?: number;
    retryDelay?: number;
    batchSize?: number;
  }): void {
    if (settings.maxRetries !== undefined) {
      this.maxRetries = settings.maxRetries;
    }
    if (settings.retryDelay !== undefined) {
      this.retryDelay = settings.retryDelay;
    }
    if (settings.batchSize !== undefined) {
      this.batchSize = settings.batchSize;
    }
    
    this.logger.info('Sync settings updated', settings);
  }
}

// Export singleton instance
export const syncService = new SyncService();