/**
 * Storage Service
 * Handles local SQLite database operations for ArxOS Mobile
 */

import SQLite from 'react-native-sqlite-storage';
import {logger} from '../utils/logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';
import {environment} from '../config/environment';

// Database schema interfaces
export interface EquipmentRecord {
  id: string;
  name: string;
  type: string;
  location: string;
  status: string;
  lastMaintenance?: string;
  nextMaintenance?: string;
  specifications?: string;
  photos?: string[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
  syncedAt?: string;
  isDirty?: boolean;
}

export interface SyncQueueRecord {
  id: string;
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
  table: string;
  recordId: string;
  data?: any;
  retryCount: number;
  createdAt: string;
  lastAttempt?: string;
}

export interface UserRecord {
  id: string;
  email: string;
  name: string;
  role: string;
  organizationId?: string;
  preferences?: string;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

class StorageService {
  private db: SQLite.SQLiteDatabase | null = null;
  private isInitialized = false;

  constructor() {
    // Enable promise-based API
    SQLite.enablePromise(true);
  }

  /**
   * Initialize the database
   */
  async initialize(): Promise<void> {
    try {
      if (this.isInitialized) {
        return;
      }

      logger.info('Initializing SQLite database', {}, 'StorageService');

      this.db = await SQLite.openDatabase({
        name: environment.databaseName,
        location: 'default',
        createFromLocation: '~www/ArxOSMobile.db',
      });

      await this.createTables();
      await this.createIndexes();
      
      this.isInitialized = true;
      logger.info('SQLite database initialized successfully', {}, 'StorageService');
    } catch (error) {
      logger.error('Failed to initialize database', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Database initialization failed',
          ErrorSeverity.CRITICAL,
          { component: 'StorageService', retryable: false }
        ),
        'StorageService'
      );
    }
  }

  /**
   * Create database tables
   */
  private async createTables(): Promise<void> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }

    const tables = [
      // Equipment table
      `CREATE TABLE IF NOT EXISTS equipment (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL,
        lastMaintenance TEXT,
        nextMaintenance TEXT,
        specifications TEXT,
        photos TEXT,
        notes TEXT,
        createdAt TEXT NOT NULL,
        updatedAt TEXT NOT NULL,
        syncedAt TEXT,
        isDirty INTEGER DEFAULT 0
      )`,

      // Sync queue table
      `CREATE TABLE IF NOT EXISTS sync_queue (
        id TEXT PRIMARY KEY,
        operation TEXT NOT NULL,
        table TEXT NOT NULL,
        recordId TEXT NOT NULL,
        data TEXT,
        retryCount INTEGER DEFAULT 0,
        createdAt TEXT NOT NULL,
        lastAttempt TEXT
      )`,

      // User table
      `CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        organizationId TEXT,
        preferences TEXT,
        lastLogin TEXT,
        createdAt TEXT NOT NULL,
        updatedAt TEXT NOT NULL
      )`,

      // Settings table
      `CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updatedAt TEXT NOT NULL
      )`,
    ];

    for (const table of tables) {
      await this.db.executeSql(table);
    }

    logger.debug('Database tables created', {}, 'StorageService');
  }

  /**
   * Create database indexes
   */
  private async createIndexes(): Promise<void> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }

    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment(location)',
      'CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(type)',
      'CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status)',
      'CREATE INDEX IF NOT EXISTS idx_equipment_synced ON equipment(syncedAt)',
      'CREATE INDEX IF NOT EXISTS idx_equipment_dirty ON equipment(isDirty)',
      'CREATE INDEX IF NOT EXISTS idx_sync_queue_operation ON sync_queue(operation)',
      'CREATE INDEX IF NOT EXISTS idx_sync_queue_table ON sync_queue(table)',
      'CREATE INDEX IF NOT EXISTS idx_sync_queue_retry ON sync_queue(retryCount)',
    ];

    for (const index of indexes) {
      await this.db.executeSql(index);
    }

    logger.debug('Database indexes created', {}, 'StorageService');
  }

  /**
   * Equipment operations
   */
  async saveEquipment(equipment: EquipmentRecord): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = `
        INSERT OR REPLACE INTO equipment 
        (id, name, type, location, status, lastMaintenance, nextMaintenance, 
         specifications, photos, notes, createdAt, updatedAt, syncedAt, isDirty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      await this.db!.executeSql(sql, [
        equipment.id,
        equipment.name,
        equipment.type,
        equipment.location,
        equipment.status,
        equipment.lastMaintenance || null,
        equipment.nextMaintenance || null,
        equipment.specifications || null,
        equipment.photos ? JSON.stringify(equipment.photos) : null,
        equipment.notes || null,
        equipment.createdAt,
        equipment.updatedAt,
        equipment.syncedAt || null,
        equipment.isDirty ? 1 : 0,
      ]);

      logger.debug('Equipment saved', { id: equipment.id }, 'StorageService');
    } catch (error) {
      logger.error('Failed to save equipment', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to save equipment',
          ErrorSeverity.HIGH,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async getEquipment(id: string): Promise<EquipmentRecord | null> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'SELECT * FROM equipment WHERE id = ?';
      const [results] = await this.db!.executeSql(sql, [id]);

      if (results.rows.length === 0) {
        return null;
      }

      const row = results.rows.item(0);
      return this.mapEquipmentRow(row);
    } catch (error) {
      logger.error('Failed to get equipment', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to get equipment',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async getAllEquipment(): Promise<EquipmentRecord[]> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'SELECT * FROM equipment ORDER BY updatedAt DESC';
      const [results] = await this.db!.executeSql(sql);

      const equipment: EquipmentRecord[] = [];
      for (let i = 0; i < results.rows.length; i++) {
        equipment.push(this.mapEquipmentRow(results.rows.item(i)));
      }

      return equipment;
    } catch (error) {
      logger.error('Failed to get all equipment', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to get equipment list',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async deleteEquipment(id: string): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'DELETE FROM equipment WHERE id = ?';
      await this.db!.executeSql(sql, [id]);

      logger.debug('Equipment deleted', { id }, 'StorageService');
    } catch (error) {
      logger.error('Failed to delete equipment', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to delete equipment',
          ErrorSeverity.HIGH,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  /**
   * Sync queue operations
   */
  async addToSyncQueue(operation: SyncQueueRecord): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = `
        INSERT INTO sync_queue 
        (id, operation, table, recordId, data, retryCount, createdAt, lastAttempt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `;

      await this.db!.executeSql(sql, [
        operation.id,
        operation.operation,
        operation.table,
        operation.recordId,
        operation.data ? JSON.stringify(operation.data) : null,
        operation.retryCount,
        operation.createdAt,
        operation.lastAttempt || null,
      ]);

      logger.debug('Added to sync queue', { id: operation.id }, 'StorageService');
    } catch (error) {
      logger.error('Failed to add to sync queue', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to add to sync queue',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async getSyncQueue(): Promise<SyncQueueRecord[]> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'SELECT * FROM sync_queue ORDER BY createdAt ASC';
      const [results] = await this.db!.executeSql(sql);

      const queue: SyncQueueRecord[] = [];
      for (let i = 0; i < results.rows.length; i++) {
        const row = results.rows.item(i);
        queue.push({
          id: row.id,
          operation: row.operation,
          table: row.table,
          recordId: row.recordId,
          data: row.data ? JSON.parse(row.data) : null,
          retryCount: row.retryCount,
          createdAt: row.createdAt,
          lastAttempt: row.lastAttempt,
        });
      }

      return queue;
    } catch (error) {
      logger.error('Failed to get sync queue', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to get sync queue',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async removeFromSyncQueue(id: string): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'DELETE FROM sync_queue WHERE id = ?';
      await this.db!.executeSql(sql, [id]);

      logger.debug('Removed from sync queue', { id }, 'StorageService');
    } catch (error) {
      logger.error('Failed to remove from sync queue', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to remove from sync queue',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  /**
   * Settings operations
   */
  async setSetting(key: string, value: string): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = `
        INSERT OR REPLACE INTO settings (key, value, updatedAt)
        VALUES (?, ?, ?)
      `;

      await this.db!.executeSql(sql, [key, value, new Date().toISOString()]);

      logger.debug('Setting saved', { key }, 'StorageService');
    } catch (error) {
      logger.error('Failed to save setting', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to save setting',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async getSetting(key: string): Promise<string | null> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'SELECT value FROM settings WHERE key = ?';
      const [results] = await this.db!.executeSql(sql, [key]);

      if (results.rows.length === 0) {
        return null;
      }

      return results.rows.item(0).value;
    } catch (error) {
      logger.error('Failed to get setting', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to get setting',
          ErrorSeverity.MEDIUM,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  /**
   * Utility methods
   */
  private mapEquipmentRow(row: any): EquipmentRecord {
    return {
      id: row.id,
      name: row.name,
      type: row.type,
      location: row.location,
      status: row.status,
      lastMaintenance: row.lastMaintenance,
      nextMaintenance: row.nextMaintenance,
      specifications: row.specifications,
      photos: row.photos ? JSON.parse(row.photos) : [],
      notes: row.notes,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
      syncedAt: row.syncedAt,
      isDirty: row.isDirty === 1,
    };
  }

  /**
   * Database maintenance
   */
  async clearAllData(): Promise<void> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const tables = ['equipment', 'sync_queue', 'users', 'settings'];
      
      for (const table of tables) {
        await this.db!.executeSql(`DELETE FROM ${table}`);
      }

      logger.info('All data cleared from database', {}, 'StorageService');
    } catch (error) {
      logger.error('Failed to clear database', error, 'StorageService');
      throw errorHandler.handleError(
        createError(
          ErrorType.STORAGE,
          'Failed to clear database',
          ErrorSeverity.HIGH,
          { component: 'StorageService', retryable: true }
        ),
        'StorageService'
      );
    }
  }

  async getDatabaseSize(): Promise<number> {
    try {
      if (!this.db) {
        await this.initialize();
      }

      const sql = 'SELECT COUNT(*) as count FROM equipment';
      const [results] = await this.db!.executeSql(sql);
      
      return results.rows.item(0).count;
    } catch (error) {
      logger.error('Failed to get database size', error, 'StorageService');
      return 0;
    }
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    try {
      if (this.db) {
        await this.db.close();
        this.db = null;
        this.isInitialized = false;
        logger.info('Database connection closed', {}, 'StorageService');
      }
    } catch (error) {
      logger.error('Failed to close database', error, 'StorageService');
    }
  }
}

export const storageService = new StorageService();
export default storageService;