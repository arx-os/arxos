/**
 * Equipment Service
 * Handles equipment data operations and synchronization
 */

import {apiService} from './apiService';
import {storageService} from './storageService';
import {
  Equipment,
  EquipmentSearchRequest,
  EquipmentSearchResponse,
  EquipmentStatusUpdate,
  EquipmentSearchResult,
  EquipmentStatus,
} from '@/types/equipment';
import {SyncResult} from '@/types/sync';
import {logger} from "../utils/logger";
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';

class EquipmentService {
  /**
   * Get equipment by building ID
   */
  async getEquipmentByBuilding(buildingId: string): Promise<Equipment[]> {
    try {
      const response = await apiService.get<{equipment: Equipment[], total: number}>(`/equipment/building/${buildingId}`);
      
      // Cache equipment data locally
      for (const equipment of response.equipment) {
        const equipmentRecord = this.convertEquipmentToRecord(equipment);
        await storageService.saveEquipment(equipmentRecord);
      }
      
      return response.equipment;
    } catch (error) {
      // Fallback to cached data if available
      const cachedData = await storageService.getAllEquipment();
      if (cachedData && cachedData.length > 0) {
        return cachedData
          .map(record => this.convertRecordToEquipment(record))
          .filter(eq => eq.buildingId === buildingId);
      }
      throw error;
    }
  }
  
  /**
   * Search equipment
   */
  async searchEquipment(request: EquipmentSearchRequest): Promise<EquipmentSearchResponse> {
    try {
      const response = await apiService.post<EquipmentSearchResponse>('/equipment/search', request);
      return response;
    } catch (error) {
      // Fallback to local search
      const localResults = await this.searchEquipmentLocally(request);
      return localResults;
    }
  }
  
  /**
   * Get equipment by ID
   */
  async getEquipmentById(equipmentId: string): Promise<Equipment> {
    try {
      const response = await apiService.get<Equipment>(`/equipment/${equipmentId}`);
      return response;
    } catch (error) {
      // Fallback to cached data
      const cachedData = await storageService.getEquipment(equipmentId);
      if (cachedData) {
        return this.convertRecordToEquipment(cachedData);
      }
      throw error;
    }
  }
  
  /**
   * Update equipment status
   */
  async updateEquipmentStatus(update: EquipmentStatusUpdate): Promise<EquipmentStatusUpdate> {
    try {
      const response = await apiService.post<EquipmentStatusUpdate>('/equipment/status', update);
      
      // Update local cache by saving the updated equipment
      const equipmentRecord = await storageService.getEquipment(update.equipmentId);
      if (equipmentRecord) {
        equipmentRecord.status = update.status;
        equipmentRecord.updatedAt = new Date().toISOString();
        await storageService.saveEquipment(equipmentRecord);
      }
      
      return response;
    } catch (error) {
      // Store update for later sync
      await storageService.addToSyncQueue({
        id: `status_${update.equipmentId}_${Date.now()}`,
        operation: 'UPDATE',
        table: 'equipment',
        recordId: update.equipmentId,
        data: update,
        retryCount: 0,
        createdAt: new Date().toISOString()
      });
      throw error;
    }
  }
  
  /**
   * Add equipment note
   */
  async addEquipmentNote(equipmentId: string, note: string): Promise<void> {
    try {
      await apiService.post(`/equipment/${equipmentId}/notes`, {note});
      
      // Update local cache by updating equipment maintenance notes
      const equipmentRecord = await storageService.getEquipment(equipmentId);
      if (equipmentRecord) {
        equipmentRecord.notes = (equipmentRecord.notes || '') + '\n' + note;
        equipmentRecord.updatedAt = new Date().toISOString();
        await storageService.saveEquipment(equipmentRecord);
      }
    } catch (error) {
      // Store note for later sync
      await storageService.addToSyncQueue({
        id: `note_${equipmentId}_${Date.now()}`,
        operation: 'UPDATE',
        table: 'equipment',
        recordId: equipmentId,
        data: {equipmentId, note},
        retryCount: 0,
        createdAt: new Date().toISOString()
      });
      throw error;
    }
  }
  
  /**
   * Upload equipment photo
   */
  async uploadEquipmentPhoto(equipmentId: string, photoUri: string): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('photo', {
        uri: photoUri,
        type: 'image/jpeg',
        name: 'photo.jpg',
      } as any);
      
      const response = await apiService.uploadFile<{photoUrl: string}>(
        `/equipment/${equipmentId}/photos`,
        formData
      );
      
      return response.photoUrl;
    } catch (error) {
      // Store photo for later upload
      await storageService.addToSyncQueue({
        id: `photo_${equipmentId}_${Date.now()}`,
        operation: 'UPDATE',
        table: 'equipment',
        recordId: equipmentId,
        data: {equipmentId, photoUri},
        retryCount: 0,
        createdAt: new Date().toISOString()
      });
      throw error;
    }
  }
  
  /**
   * Sync equipment data
   */
  async syncEquipmentData(): Promise<SyncResult> {
    const result: SyncResult = {
      synced: 0,
      failed: 0,
      errors: [],
      duration: 0
    };
    
    try {
      // Get pending updates
      const pendingUpdates = await storageService.getSyncQueue();
      
      for (const update of pendingUpdates) {
        try {
          // Process different types of sync operations
          if (update.operation === 'UPDATE' && update.table === 'equipment') {
            if (update.data.equipmentId && update.data.status) {
              // Equipment status update
              await this.updateEquipmentStatus(update.data);
            } else if (update.data.equipmentId && update.data.note) {
              // Equipment note addition
              await this.addEquipmentNote(update.data.equipmentId, update.data.note);
            } else if (update.data.equipmentId && update.data.photoUri) {
              // Equipment photo upload
              await this.uploadEquipmentPhoto(update.data.equipmentId, update.data.photoUri);
            }
          }
          await storageService.removeFromSyncQueue(update.id);
          result.synced++;
        } catch (error: any) {
          result.failed++;
          result.errors.push(`Failed to sync update ${update.id}: ${error.message}`);
        }
      }
      
    } catch (error: any) {
      result.errors.push(`Sync failed: ${error.message}`);
    }
    
    return result;
  }
  
  /**
   * Search equipment locally (offline)
   */
  private async searchEquipmentLocally(request: EquipmentSearchRequest): Promise<EquipmentSearchResponse> {
    const allEquipment = await storageService.getAllEquipment();
    const equipment = allEquipment.map(record => this.convertRecordToEquipment(record));
    
    if (!equipment || equipment.length === 0) {
      return {
        results: {
          equipment: [],
          totalCount: 0,
          searchTime: 0
        },
        success: true,
        message: 'No equipment found'
      };
    }
    
    // Filter equipment based on search criteria
    let filteredEquipment = equipment.filter(eq => {
      const matchesQuery = !request.query || 
        eq.name.toLowerCase().includes(request.query.toLowerCase()) ||
        eq.type.toLowerCase().includes(request.query.toLowerCase());
      
      const matchesFilters = !request.filters || (
        (!request.filters.floorId || eq.floorId === request.filters.floorId) &&
        (!request.filters.roomId || eq.roomId === request.filters.roomId) &&
        (!request.filters.type || eq.type === request.filters.type) &&
        (!request.filters.status || eq.status === request.filters.status)
      );
      
      return matchesQuery && matchesFilters;
    });
    
    // Apply pagination
    const offset = request.offset || 0;
    const limit = request.limit || 50;
    const paginatedEquipment = filteredEquipment.slice(offset, offset + limit);
    
    return {
      results: {
        equipment: paginatedEquipment,
        totalCount: filteredEquipment.length,
        searchTime: Date.now()
      },
      success: true,
      message: 'Search completed successfully'
    };
  }

  /**
   * Convert Equipment to EquipmentRecord for storage
   */
  private convertEquipmentToRecord(equipment: Equipment): any {
    return {
      id: equipment.id,
      name: equipment.name,
      type: equipment.type,
      location: equipment.location ? JSON.stringify(equipment.location) : '',
      status: equipment.status,
      lastMaintenance: equipment.lastMaintenance?.toISOString(),
      nextMaintenance: equipment.nextMaintenance?.toISOString(),
      specifications: '',
      photos: [],
      notes: equipment.maintenanceNotes,
      createdAt: equipment.createdAt?.toISOString() || new Date().toISOString(),
      updatedAt: equipment.updatedAt?.toISOString() || new Date().toISOString(),
      syncedAt: new Date().toISOString(),
      isDirty: false
    };
  }

  /**
   * Convert EquipmentRecord to Equipment for API usage
   */
  private convertRecordToEquipment(record: any): Equipment {
    return {
      id: record.id,
      name: record.name,
      type: record.type,
      model: record.model || '',
      manufacturer: record.manufacturer || '',
      status: record.status as EquipmentStatus,
      location: record.location ? JSON.parse(record.location) : undefined,
      buildingId: record.buildingId || '', // Default empty string since it's not in EquipmentRecord
      floorId: record.floorId || '',
      roomId: record.roomId || '',
      installationDate: record.installationDate ? new Date(record.installationDate) : undefined,
      lastMaintenance: record.lastMaintenance ? new Date(record.lastMaintenance) : undefined,
      nextMaintenance: record.nextMaintenance ? new Date(record.nextMaintenance) : undefined,
      maintenanceNotes: record.notes,
      createdAt: record.createdAt ? new Date(record.createdAt) : new Date(),
      updatedAt: record.updatedAt ? new Date(record.updatedAt) : new Date()
    };
  }
}

export const equipmentService = new EquipmentService();
