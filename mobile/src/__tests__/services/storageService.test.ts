/**
 * StorageService Tests
 * Unit tests for SQLite storage service
 */

import {storageService, EquipmentRecord} from '../../services/storageService';
import SQLite from 'react-native-sqlite-storage';

// Mock SQLite
jest.mock('react-native-sqlite-storage', () => ({
  openDatabase: jest.fn(),
  enablePromise: jest.fn(),
}));

const mockSQLite = SQLite as jest.Mocked<typeof SQLite>;

describe('StorageService', () => {
  let mockDb: any;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockDb = {
      executeSql: jest.fn(() => Promise.resolve([{ rows: { length: 0, item: jest.fn() } }])),
      close: jest.fn(() => Promise.resolve()),
    };
    
    mockSQLite.openDatabase.mockReturnValue(mockDb as any);
  });

  describe('initialize', () => {
    it('should initialize database successfully', async () => {
      // Act
      await storageService.initialize();

      // Assert
      expect(mockSQLite.openDatabase).toHaveBeenCalledWith({
        name: 'ArxOSMobile.db',
        location: 'default',
        createFromLocation: '~www/ArxOSMobile.db',
      });
      expect(mockDb.executeSql).toHaveBeenCalled();
    });

    it('should not initialize if already initialized', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.initialize();

      // Assert
      expect(mockSQLite.openDatabase).toHaveBeenCalledTimes(1);
    });
  });

  describe('saveEquipment', () => {
    it('should save equipment successfully', async () => {
      // Arrange
      const equipment: EquipmentRecord = {
        id: '1',
        name: 'Test Equipment',
        type: 'HVAC',
        location: 'Building A',
        status: 'Active',
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z',
        isDirty: false,
      };

      await storageService.initialize();

      // Act
      await storageService.saveEquipment(equipment);

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith(
        expect.stringContaining('INSERT OR REPLACE INTO equipment'),
        expect.arrayContaining([
          equipment.id,
          equipment.name,
          equipment.type,
          equipment.location,
          equipment.status,
          null, // lastMaintenance
          null, // nextMaintenance
          null, // specifications
          null, // photos
          null, // notes
          equipment.createdAt,
          equipment.updatedAt,
          null, // syncedAt
          0, // isDirty
        ])
      );
    });
  });

  describe('getEquipment', () => {
    it('should get equipment by ID successfully', async () => {
      // Arrange
      const mockRow = {
        id: '1',
        name: 'Test Equipment',
        type: 'HVAC',
        location: 'Building A',
        status: 'Active',
        lastMaintenance: null,
        nextMaintenance: null,
        specifications: null,
        photos: null,
        notes: null,
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z',
        syncedAt: null,
        isDirty: 0,
      };

      mockDb.executeSql.mockResolvedValueOnce([{
        rows: {
          length: 1,
          item: jest.fn(() => mockRow),
        },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getEquipment('1');

      // Assert
      expect(result).toEqual({
        id: '1',
        name: 'Test Equipment',
        type: 'HVAC',
        location: 'Building A',
        status: 'Active',
        lastMaintenance: undefined,
        nextMaintenance: undefined,
        specifications: undefined,
        photos: [],
        notes: undefined,
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z',
        syncedAt: undefined,
        isDirty: false,
      });
    });

    it('should return null when equipment not found', async () => {
      // Arrange
      mockDb.executeSql.mockResolvedValueOnce([{
        rows: { length: 0 },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getEquipment('999');

      // Assert
      expect(result).toBeNull();
    });
  });

  describe('getAllEquipment', () => {
    it('should get all equipment successfully', async () => {
      // Arrange
      const mockRows = [
        {
          id: '1',
          name: 'Equipment 1',
          type: 'HVAC',
          location: 'Building A',
          status: 'Active',
          lastMaintenance: null,
          nextMaintenance: null,
          specifications: null,
          photos: null,
          notes: null,
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z',
          syncedAt: null,
          isDirty: 0,
        },
        {
          id: '2',
          name: 'Equipment 2',
          type: 'Electrical',
          location: 'Building B',
          status: 'Inactive',
          lastMaintenance: null,
          nextMaintenance: null,
          specifications: null,
          photos: null,
          notes: null,
          createdAt: '2023-01-02T00:00:00Z',
          updatedAt: '2023-01-02T00:00:00Z',
          syncedAt: null,
          isDirty: 0,
        },
      ];

      mockDb.executeSql.mockResolvedValueOnce([{
        rows: {
          length: 2,
          item: jest.fn((index) => mockRows[index]),
        },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getAllEquipment();

      // Assert
      expect(result).toHaveLength(2);
      expect(result[0]?.name).toBe('Equipment 1');
      expect(result[1]?.name).toBe('Equipment 2');
    });
  });

  describe('deleteEquipment', () => {
    it('should delete equipment successfully', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.deleteEquipment('1');

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith(
        'DELETE FROM equipment WHERE id = ?',
        ['1']
      );
    });
  });

  describe('addToSyncQueue', () => {
    it('should add item to sync queue successfully', async () => {
      // Arrange
      const syncItem = {
        id: 'sync-1',
        operation: 'CREATE' as const,
        table: 'equipment',
        recordId: '1',
        data: { name: 'Test Equipment' },
        retryCount: 0,
        createdAt: '2023-01-01T00:00:00Z',
      };

      await storageService.initialize();

      // Act
      await storageService.addToSyncQueue(syncItem);

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO sync_queue'),
        expect.arrayContaining([
          syncItem.id,
          syncItem.operation,
          syncItem.table,
          syncItem.recordId,
          JSON.stringify(syncItem.data),
          syncItem.retryCount,
          syncItem.createdAt,
          null, // lastAttempt
        ])
      );
    });
  });

  describe('getSyncQueue', () => {
    it('should get sync queue successfully', async () => {
      // Arrange
      const mockRows = [
        {
          id: 'sync-1',
          operation: 'CREATE',
          table: 'equipment',
          recordId: '1',
          data: '{"name":"Test Equipment"}',
          retryCount: 0,
          createdAt: '2023-01-01T00:00:00Z',
          lastAttempt: null,
        },
      ];

      mockDb.executeSql.mockResolvedValueOnce([{
        rows: {
          length: 1,
          item: jest.fn((index) => mockRows[index]),
        },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getSyncQueue();

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        id: 'sync-1',
        operation: 'CREATE',
        table: 'equipment',
        recordId: '1',
        data: { name: 'Test Equipment' },
        retryCount: 0,
        createdAt: '2023-01-01T00:00:00Z',
        lastAttempt: null,
      });
    });
  });

  describe('removeFromSyncQueue', () => {
    it('should remove item from sync queue successfully', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.removeFromSyncQueue('sync-1');

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith(
        'DELETE FROM sync_queue WHERE id = ?',
        ['sync-1']
      );
    });
  });

  describe('setSetting', () => {
    it('should set setting successfully', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.setSetting('theme', 'dark');

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith(
        expect.stringContaining('INSERT OR REPLACE INTO settings'),
        ['theme', 'dark', expect.any(String)]
      );
    });
  });

  describe('getSetting', () => {
    it('should get setting successfully', async () => {
      // Arrange
      mockDb.executeSql.mockResolvedValueOnce([{
        rows: {
          length: 1,
          item: jest.fn(() => ({ value: 'dark' })),
        },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getSetting('theme');

      // Assert
      expect(result).toBe('dark');
    });

    it('should return null when setting not found', async () => {
      // Arrange
      mockDb.executeSql.mockResolvedValueOnce([{
        rows: { length: 0 },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getSetting('nonexistent');

      // Assert
      expect(result).toBeNull();
    });
  });

  describe('clearAllData', () => {
    it('should clear all data successfully', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.clearAllData();

      // Assert
      expect(mockDb.executeSql).toHaveBeenCalledWith('DELETE FROM equipment');
      expect(mockDb.executeSql).toHaveBeenCalledWith('DELETE FROM sync_queue');
      expect(mockDb.executeSql).toHaveBeenCalledWith('DELETE FROM users');
      expect(mockDb.executeSql).toHaveBeenCalledWith('DELETE FROM settings');
    });
  });

  describe('getDatabaseSize', () => {
    it('should get database size successfully', async () => {
      // Arrange
      mockDb.executeSql.mockResolvedValueOnce([{
        rows: {
          length: 1,
          item: jest.fn(() => ({ count: 5 })),
        },
      }]);

      await storageService.initialize();

      // Act
      const result = await storageService.getDatabaseSize();

      // Assert
      expect(result).toBe(5);
    });
  });

  describe('close', () => {
    it('should close database successfully', async () => {
      // Arrange
      await storageService.initialize();

      // Act
      await storageService.close();

      // Assert
      expect(mockDb.close).toHaveBeenCalled();
    });
  });
});
