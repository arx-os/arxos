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
} from '@/types/equipment';
import {SyncResult} from '@/types/sync';
import {logger} from '../utils/logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';

class EquipmentService {
  /**
   * Get equipment by building ID
   */
  async getEquipmentByBuilding(buildingId: string): Promise<Equipment[]> {
    try {
      const response = await apiService.get<Equipment[]>(`/equipment/building/${buildingId}`);
      
      // Cache equipment data locally
      await storageService.setEquipmentData(buildingId, response);
      
      return response;
    } catch (error) {
      // Fallback to cached data if available
      const cachedData = await storageService.getEquipmentData(buildingId);
      if (cachedData) {
        return cachedData;
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
      const cachedData = await storageService.getEquipmentById(equipmentId);
      if (cachedData) {
        return cachedData;
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
      
      // Update local cache
      await storageService.updateEquipmentStatus(update);
      
      return response;
    } catch (error) {
      // Store update for later sync
      await storageService.addPendingUpdate(update);
      throw error;
    }
  }
  
  /**
   * Add equipment note
   */
  async addEquipmentNote(equipmentId: string, note: string): Promise<void> {
    try {
      await apiService.post(`/equipment/${equipmentId}/notes`, {note});
      
      // Update local cache
      await storageService.addEquipmentNote(equipmentId, note);
    } catch (error) {
      // Store note for later sync
      await storageService.addPendingNote(equipmentId, note);
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
      await storageService.addPendingPhoto(equipmentId, photoUri);
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
    };
    
    try {
      // Get pending updates
      const pendingUpdates = await storageService.getPendingUpdates();
      
      for (const update of pendingUpdates) {
        try {
          await this.updateEquipmentStatus(update);
          await storageService.removePendingUpdate(update.id);
          result.synced++;
        } catch (error: any) {
          result.failed++;
          result.errors.push(`Failed to sync update ${update.id}: ${error.message}`);
        }
      }
      
      // Get pending notes
      const pendingNotes = await storageService.getPendingNotes();
      
      for (const note of pendingNotes) {
        try {
          await this.addEquipmentNote(note.equipmentId, note.note);
          await storageService.removePendingNote(note.id);
          result.synced++;
        } catch (error: any) {
          result.failed++;
          result.errors.push(`Failed to sync note ${note.id}: ${error.message}`);
        }
      }
      
      // Get pending photos
      const pendingPhotos = await storageService.getPendingPhotos();
      
      for (const photo of pendingPhotos) {
        try {
          await this.uploadEquipmentPhoto(photo.equipmentId, photo.photoUri);
          await storageService.removePendingPhoto(photo.id);
          result.synced++;
        } catch (error: any) {
          result.failed++;
          result.errors.push(`Failed to sync photo ${photo.id}: ${error.message}`);
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
    const equipment = await storageService.getEquipmentData(request.buildingId);
    
    if (!equipment) {
      return {
        equipment: [],
        total: 0,
        hasMore: false,
      };
    }
    
    // Filter equipment based on search criteria
    let filteredEquipment = equipment.filter(eq => {
      const matchesQuery = !request.query || 
        eq.name.toLowerCase().includes(request.query.toLowerCase()) ||
        eq.type.toLowerCase().includes(request.query.toLowerCase());
      
      const matchesFilters = !request.filters || (
        (!request.filters.floor || eq.location.floorId === request.filters.floor) &&
        (!request.filters.room || eq.location.roomId === request.filters.room) &&
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
      equipment: paginatedEquipment,
      total: filteredEquipment.length,
      hasMore: offset + limit < filteredEquipment.length,
    };
  }
}

export const equipmentService = new EquipmentService();
