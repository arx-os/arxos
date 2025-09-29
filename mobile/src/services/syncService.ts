/**
 * Sync Service
 * Handles offline-first data synchronization for ArxOS Mobile
 */

import NetInfo from '@react-native-netinfo/netinfo';
import {logger} from '../utils/logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';
import {storageService, SyncQueueRecord} from './storageService';
import {apiService} from './apiService';
import {environment} from '../config/environment';

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime?: string;
  pendingChanges: number;
  syncErrors: string[];
}

export interface SyncResult {
  success: boolean;
  syncedCount: number;
  errorCount: number;
  errors: string[];
}

class SyncService {
  private isOnline = false;
  private isSyncing = false;
  private syncInterval: NodeJS.Timeout | null = null;
  private lastSyncTime: string | null = null;
  private syncErrors: string[] = [];

  constructor() {
    this.initializeNetworkListener();
    this.startAutoSync();
  }

  /**
   * Initialize network connectivity listener
   */
  private initializeNetworkListener(): void {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (!wasOnline && this.isOnline) {
        logger.info('Network connection restored', {}, 'SyncService');
        this.syncPendingChanges();
      } else if (wasOnline && !this.isOnline) {
        logger.warn('Network connection lost', {}, 'SyncService');
      }
    });
  }

  /**
   * Start automatic sync
   */
  private startAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    this.syncInterval = setInterval(() => {
      if (this.isOnline && !this.isSyncing) {
        this.syncPendingChanges();
      }
    }, environment.autoSyncInterval);

    logger.info('Auto sync started', { interval: environment.autoSyncInterval }, 'SyncService');
  }

  /**
   * Stop automatic sync
   */
  public stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    logger.info('Auto sync stopped', {}, 'SyncService');
  }

  /**
   * Get current sync status
   */
  public async getSyncStatus(): Promise<SyncStatus> {
    try {
      const syncQueue = await storageService.getSyncQueue();
      
      return {
        isOnline: this.isOnline,
        isSyncing: this.isSyncing,
        lastSyncTime: this.lastSyncTime,
        pendingChanges: syncQueue.length,
        syncErrors: [...this.syncErrors],
      };
    } catch (error) {
      logger.error('Failed to get sync status', error, 'SyncService');
      return {
        isOnline: this.isOnline,
        isSyncing: this.isSyncing,
        lastSyncTime: this.lastSyncTime,
        pendingChanges: 0,
        syncErrors: [...this.syncErrors],
      };
    }
  }

  /**
   * Sync pending changes
   */
  public async syncPendingChanges(): Promise<SyncResult> {
    if (this.isSyncing) {
      logger.warn('Sync already in progress', {}, 'SyncService');
      return {
        success: false,
        syncedCount: 0,
        errorCount: 0,
        errors: ['Sync already in progress'],
      };
    }

    if (!this.isOnline) {
      logger.warn('Cannot sync while offline', {}, 'SyncService');
      return {
        success: false,
        syncedCount: 0,
        errorCount: 0,
        errors: ['Device is offline'],
      };
    }

    this.isSyncing = true;
    this.syncErrors = [];

    try {
      logger.info('Starting sync process', {}, 'SyncService');

      const syncQueue = await storageService.getSyncQueue();
      let syncedCount = 0;
      let errorCount = 0;
      const errors: string[] = [];

      // Process sync queue in batches
      const batchSize = environment.batchSize;
      for (let i = 0; i < syncQueue.length; i += batchSize) {
        const batch = syncQueue.slice(i, i + batchSize);
        
        for (const item of batch) {
          try {
            await this.processSyncItem(item);
            await storageService.removeFromSyncQueue(item.id);
            syncedCount++;
          } catch (error) {
            errorCount++;
            const errorMessage = `Failed to sync ${item.table}:${item.recordId}`;
            errors.push(errorMessage);
            this.syncErrors.push(errorMessage);
            
            logger.error('Sync item failed', { item, error }, 'SyncService');
            
            // Increment retry count
            const updatedItem = {
              ...item,
              retryCount: item.retryCount + 1,
              lastAttempt: new Date().toISOString(),
            };
            
            // Remove from queue if max retries reached
            if (updatedItem.retryCount >= environment.maxRetries) {
              await storageService.removeFromSyncQueue(item.id);
              logger.error('Max retries reached, removing from sync queue', { item }, 'SyncService');
            }
          }
        }
      }

      this.lastSyncTime = new Date().toISOString();
      
      const result: SyncResult = {
        success: errorCount === 0,
        syncedCount,
        errorCount,
        errors,
      };

      logger.info('Sync process completed', result, 'SyncService');
      return result;

    } catch (error) {
      logger.error('Sync process failed', error, 'SyncService');
      throw errorHandler.handleError(
        createError(
          ErrorType.SYNC,
          'Sync process failed',
          ErrorSeverity.HIGH,
          { component: 'SyncService', retryable: true }
        ),
        'SyncService'
      );
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Process individual sync item
   */
  private async processSyncItem(item: SyncQueueRecord): Promise<void> {
    const {operation, table, recordId, data} = item;

    switch (table) {
      case 'equipment':
        await this.syncEquipmentItem(operation, recordId, data);
        break;
      case 'users':
        await this.syncUserItem(operation, recordId, data);
        break;
      default:
        throw new Error(`Unknown table: ${table}`);
    }
  }

  /**
   * Sync equipment item
   */
  private async syncEquipmentItem(operation: string, recordId: string, data: any): Promise<void> {
    switch (operation) {
      case 'CREATE':
        await apiService.post('/equipment', data);
        break;
      case 'UPDATE':
        await apiService.put(`/equipment/${recordId}`, data);
        break;
      case 'DELETE':
        await apiService.delete(`/equipment/${recordId}`);
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
  }

  /**
   * Sync user item
   */
  private async syncUserItem(operation: string, recordId: string, data: any): Promise<void> {
    switch (operation) {
      case 'CREATE':
        await apiService.post('/users', data);
        break;
      case 'UPDATE':
        await apiService.put(`/users/${recordId}`, data);
        break;
      case 'DELETE':
        await apiService.delete(`/users/${recordId}`);
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
  }

  /**
   * Add item to sync queue
   */
  public async addToSyncQueue(
    operation: 'CREATE' | 'UPDATE' | 'DELETE',
    table: string,
    recordId: string,
    data?: any
  ): Promise<void> {
    try {
      const syncItem: SyncQueueRecord = {
        id: `${table}_${recordId}_${Date.now()}`,
        operation,
        table,
        recordId,
        data,
        retryCount: 0,
        createdAt: new Date().toISOString(),
      };

      await storageService.addToSyncQueue(syncItem);
      
      logger.debug('Added to sync queue', { syncItem }, 'SyncService');

      // Try to sync immediately if online
      if (this.isOnline && !this.isSyncing) {
        this.syncPendingChanges();
      }
    } catch (error) {
      logger.error('Failed to add to sync queue', error, 'SyncService');
      throw errorHandler.handleError(
        createError(
          ErrorType.SYNC,
          'Failed to add to sync queue',
          ErrorSeverity.MEDIUM,
          { component: 'SyncService', retryable: true }
        ),
        'SyncService'
      );
    }
  }

  /**
   * Force sync all data
   */
  public async forceSyncAll(): Promise<SyncResult> {
    logger.info('Force sync all data initiated', {}, 'SyncService');
    return this.syncPendingChanges();
  }

  /**
   * Clear sync errors
   */
  public clearSyncErrors(): void {
    this.syncErrors = [];
    logger.debug('Sync errors cleared', {}, 'SyncService');
  }

  /**
   * Get sync queue
   */
  public async getSyncQueue(): Promise<SyncQueueRecord[]> {
    try {
      return await storageService.getSyncQueue();
    } catch (error) {
      logger.error('Failed to get sync queue', error, 'SyncService');
      throw errorHandler.handleError(
        createError(
          ErrorType.SYNC,
          'Failed to get sync queue',
          ErrorSeverity.MEDIUM,
          { component: 'SyncService', retryable: true }
        ),
        'SyncService'
      );
    }
  }

  /**
   * Check if device is online
   */
  public isDeviceOnline(): boolean {
    return this.isOnline;
  }

  /**
   * Check if sync is in progress
   */
  public isSyncInProgress(): boolean {
    return this.isSyncing;
  }

  /**
   * Get last sync time
   */
  public getLastSyncTime(): string | null {
    return this.lastSyncTime;
  }

  /**
   * Cleanup
   */
  public cleanup(): void {
    this.stopAutoSync();
    logger.info('Sync service cleaned up', {}, 'SyncService');
  }
}

export const syncService = new SyncService();
export default syncService;