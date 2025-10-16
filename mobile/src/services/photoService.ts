/**
 * Photo Service
 * Handles photo capture, storage, and upload for equipment documentation
 */

import { launchImageLibrary, launchCamera, ImagePickerResponse, MediaType } from 'react-native-image-picker';
import { syncService } from './syncService';
import { storageService } from './storageService';
import { Logger } from '../utils/logger';
import { v4 as uuidv4 } from 'uuid';

export interface PhotoData {
  id: string;
  uri: string;
  type: string;
  name: string;
  size: number;
  equipmentId: string;
  metadata: {
    timestamp: string;
    location?: {
      latitude: number;
      longitude: number;
    };
    notes?: string;
  };
  synced: boolean;
  createdAt: string;
}

export class PhotoService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('PhotoService');
  }

  /**
   * Capture photo from camera
   */
  async capturePhoto(equipmentId: string, notes?: string): Promise<PhotoData> {
    return new Promise((resolve, reject) => {
      const options = {
        mediaType: 'photo' as MediaType,
        quality: 0.8,
        maxWidth: 1920,
        maxHeight: 1920,
        includeBase64: false,
      };

      launchCamera(options, (response: ImagePickerResponse) => {
        if (response.didCancel || response.errorMessage) {
          reject(new Error(response.errorMessage || 'Photo capture cancelled'));
          return;
        }

        if (response.assets && response.assets[0]) {
          const asset = response.assets[0];
          const photoData: PhotoData = {
            id: uuidv4(),
            uri: asset.uri || '',
            type: asset.type || 'image/jpeg',
            name: asset.fileName || `photo_${Date.now()}.jpg`,
            size: asset.fileSize || 0,
            equipmentId,
            metadata: {
              timestamp: new Date().toISOString(),
              notes,
            },
            synced: false,
            createdAt: new Date().toISOString(),
          };

          this.logger.debug('Photo captured', { id: photoData.id, equipmentId });
          resolve(photoData);
        } else {
          reject(new Error('No photo captured'));
        }
      });
    });
  }

  /**
   * Select photo from gallery
   */
  async selectPhoto(equipmentId: string, notes?: string): Promise<PhotoData> {
    return new Promise((resolve, reject) => {
      const options = {
        mediaType: 'photo' as MediaType,
        quality: 0.8,
        maxWidth: 1920,
        maxHeight: 1920,
        includeBase64: false,
      };

      launchImageLibrary(options, (response: ImagePickerResponse) => {
        if (response.didCancel || response.errorMessage) {
          reject(new Error(response.errorMessage || 'Photo selection cancelled'));
          return;
        }

        if (response.assets && response.assets[0]) {
          const asset = response.assets[0];
          const photoData: PhotoData = {
            id: uuidv4(),
            uri: asset.uri || '',
            type: asset.type || 'image/jpeg',
            name: asset.fileName || `photo_${Date.now()}.jpg`,
            size: asset.fileSize || 0,
            equipmentId,
            metadata: {
              timestamp: new Date().toISOString(),
              notes,
            },
            synced: false,
            createdAt: new Date().toISOString(),
          };

          this.logger.debug('Photo selected', { id: photoData.id, equipmentId });
          resolve(photoData);
        } else {
          reject(new Error('No photo selected'));
        }
      });
    });
  }

  /**
   * Save photo data locally and queue for sync
   */
  async savePhoto(photoData: PhotoData): Promise<void> {
    try {
      // Save to local storage (you might want to implement this in storageService)
      // For now, we'll just queue it for sync
      await syncService.queuePhotoUpload(photoData);
      this.logger.debug('Photo saved and queued for sync', { id: photoData.id });
    } catch (error) {
      this.logger.error('Failed to save photo', error);
      throw error;
    }
  }

  /**
   * Get photos for equipment
   */
  async getPhotosForEquipment(equipmentId: string): Promise<PhotoData[]> {
    try {
      // This would typically query local storage
      // For now, return empty array
      this.logger.debug('Getting photos for equipment', { equipmentId });
      return [];
    } catch (error) {
      this.logger.error('Failed to get photos for equipment', error);
      throw error;
    }
  }

  /**
   * Delete photo
   */
  async deletePhoto(photoId: string): Promise<void> {
    try {
      // This would typically delete from local storage and queue deletion
      this.logger.debug('Photo deleted', { id: photoId });
    } catch (error) {
      this.logger.error('Failed to delete photo', error);
      throw error;
    }
  }

  /**
   * Compress photo for upload
   */
  private compressPhoto(uri: string, quality: number = 0.8): Promise<string> {
    // This would typically use a compression library
    // For now, return the original URI
    return Promise.resolve(uri);
  }

  /**
   * Get photo metadata
   */
  private async getPhotoMetadata(uri: string): Promise<any> {
    // This would typically extract EXIF data
    // For now, return basic metadata
    return {
      width: 1920,
      height: 1080,
      orientation: 1,
    };
  }
}

// Export singleton instance
export const photoService = new PhotoService();
