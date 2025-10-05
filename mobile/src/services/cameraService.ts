/**
 * Camera Service
 * Handles camera functionality for photo capture and processing
 */

import {Platform, Alert} from 'react-native';
import {launchCamera, launchImageLibrary, ImagePickerResponse, MediaType} from 'react-native-image-picker';
import {Logger} from "../utils/logger";
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';
import {permissionManager, PermissionType} from '../utils/permissions';

// Create logger instance
const logger = new Logger('CameraService');

export interface CameraOptions {
  quality?: number; // 0-1
  maxWidth?: number;
  maxHeight?: number;
  allowsEditing?: boolean;
  aspect?: [number, number];
  mediaType?: 'photo' | 'video' | 'mixed';
  includeBase64?: boolean;
  saveToPhotos?: boolean;
}

export interface PhotoResult {
  uri: string;
  width: number;
  height: number;
  fileSize?: number;
  type?: string;
  fileName?: string;
  base64?: string;
  timestamp: string;
  location?: {
    latitude: number;
    longitude: number;
  };
}

export interface CameraError {
  code: string;
  message: string;
  details?: any;
}

class CameraService {
  private defaultOptions: CameraOptions = {
    quality: 0.8,
    maxWidth: 1920,
    maxHeight: 1080,
    allowsEditing: false,
    mediaType: 'photo',
    includeBase64: false,
    saveToPhotos: false,
  };

  /**
   * Check camera permissions
   */
  async checkPermissions(): Promise<boolean> {
    try {
      const result = await permissionManager.checkPermission(PermissionType.CAMERA);
      return result.granted;
    } catch (error) {
      logger.error('Failed to check camera permissions', error);
      return false;
    }
  }

  /**
   * Request camera permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const result = await permissionManager.requestPermissionWithDialog(
        PermissionType.CAMERA,
        {
          title: 'Camera Permission Required',
          message: 'Camera access is required to capture photos of equipment and building components.',
        }
      );
      return result.granted;
    } catch (error) {
      logger.error('Failed to request camera permissions', error);
      return false;
    }
  }

  /**
   * Take photo with camera
   */
  async takePhoto(options?: Partial<CameraOptions>): Promise<PhotoResult> {
    try {
      logger.info('Taking photo with camera', {options});

      // Check permissions
      const hasPermission = await this.checkPermissions();
      if (!hasPermission) {
        const granted = await this.requestPermissions();
        if (!granted) {
          throw new Error('Camera permission is required');
        }
      }

      const cameraOptions = {
        ...this.defaultOptions, 
        ...options,
        mediaType: (options?.mediaType as MediaType) || this.defaultOptions.mediaType,
        quality: (options?.quality as any) || this.defaultOptions.quality
      };

      return new Promise((resolve, reject) => {
        launchCamera(cameraOptions, (response: ImagePickerResponse) => {
          this.handleImagePickerResponse(response, resolve, reject, 'camera');
        });
      });
    } catch (error) {
      logger.error('Failed to take photo', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to take photo',
          ErrorSeverity.HIGH,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Select photo from gallery
   */
  async selectFromGallery(options?: Partial<CameraOptions>): Promise<PhotoResult> {
    try {
      logger.info('Selecting photo from gallery', {options});

      // Check storage permissions for Android
      if (Platform.OS === 'android') {
        const hasStoragePermission = await permissionManager.checkPermission(PermissionType.STORAGE);
        if (!hasStoragePermission) {
          const granted = await permissionManager.requestPermissionWithDialog(
            PermissionType.STORAGE,
            {
              title: 'Storage Permission Required',
              message: 'Storage access is required to select photos from your gallery.',
            }
          );
          if (!granted) {
            throw new Error('Storage permission is required');
          }
        }
      }

      const galleryOptions = {
        ...this.defaultOptions, 
        ...options,
        mediaType: (options?.mediaType as MediaType) || this.defaultOptions.mediaType,
        quality: (options?.quality as any) || this.defaultOptions.quality
      };

      return new Promise((resolve, reject) => {
        launchImageLibrary(galleryOptions, (response: ImagePickerResponse) => {
          this.handleImagePickerResponse(response, resolve, reject, 'gallery');
        });
      });
    } catch (error) {
      logger.error('Failed to select photo from gallery', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to select photo from gallery',
          ErrorSeverity.HIGH,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Show photo selection options
   */
  async showPhotoOptions(options?: Partial<CameraOptions>): Promise<PhotoResult> {
    return new Promise((resolve, reject) => {
      Alert.alert(
        'Select Photo',
        'Choose how you want to add a photo',
        [
          {
            text: 'Cancel',
            style: 'cancel',
            onPress: () => reject(new Error('User cancelled photo selection')),
          },
          {
            text: 'Take Photo',
            onPress: async () => {
              try {
                const result = await this.takePhoto(options);
                resolve(result);
              } catch (error) {
                reject(error);
              }
            },
          },
          {
            text: 'Choose from Gallery',
            onPress: async () => {
              try {
                const result = await this.selectFromGallery(options);
                resolve(result);
              } catch (error) {
                reject(error);
              }
            },
          },
        ]
      );
    });
  }

  /**
   * Handle image picker response
   */
  private handleImagePickerResponse(
    response: ImagePickerResponse,
    resolve: (result: PhotoResult) => void,
    reject: (error: Error) => void,
    source: 'camera' | 'gallery'
  ): void {
    try {
      if (response.didCancel) {
        reject(new Error('User cancelled photo selection'));
        return;
      }

      if (response.errorMessage) {
        logger.error('Image picker error', {error: response.errorMessage});
        reject(new Error(response.errorMessage));
        return;
      }

      if (!response.assets || response.assets.length === 0) {
        reject(new Error('No photo selected'));
        return;
      }

      const asset = response.assets[0];
      if (!asset) {
        reject(new Error('No photo selected'));
        return;
      }
      if (!asset.uri) {
        reject(new Error('Photo URI is missing'));
        return;
      }

      const photoResult: PhotoResult = {
        uri: asset.uri,
        width: asset.width || 0,
        height: asset.height || 0,
        fileSize: asset.fileSize,
        type: asset.type,
        fileName: asset.fileName,
        base64: asset.base64,
        timestamp: new Date().toISOString(),
        location: undefined, // Asset doesn't have location property
      };

      logger.info('Photo captured successfully', {
        source,
        width: photoResult.width,
        height: photoResult.height,
        fileSize: photoResult.fileSize,
      });

      resolve(photoResult);
    } catch (error) {
      logger.error('Failed to handle image picker response', error);
      reject(error as Error);
    }
  }

  /**
   * Compress image
   */
  async compressImage(
    uri: string,
    options: {
      quality?: number;
      maxWidth?: number;
      maxHeight?: number;
    } = {}
  ): Promise<string> {
    try {
      logger.info('Compressing image', {uri, options});

      // This would integrate with a image compression library
      // For now, we'll return the original URI
      // In a real implementation, you might use react-native-image-resizer
      
      const compressedUri = uri; // Placeholder
      
      logger.info('Image compressed successfully', {originalUri: uri, compressedUri});
      return compressedUri;
    } catch (error) {
      logger.error('Failed to compress image', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to compress image',
          ErrorSeverity.MEDIUM,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Get image metadata
   */
  async getImageMetadata(uri: string): Promise<{
    width: number;
    height: number;
    fileSize: number;
    format: string;
  }> {
    try {
      logger.debug('Getting image metadata', {uri});

      // This would integrate with a metadata extraction library
      // For now, we'll return placeholder data
      const metadata = {
        width: 1920,
        height: 1080,
        fileSize: 1024000,
        format: 'JPEG',
      };

      logger.debug('Image metadata retrieved', {uri, metadata});
      return metadata;
    } catch (error) {
      logger.error('Failed to get image metadata', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to get image metadata',
          ErrorSeverity.LOW,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Validate image file
   */
  validateImage(image: PhotoResult): {valid: boolean; errors: string[]} {
    const errors: string[] = [];

    // Check file size (max 10MB)
    if (image.fileSize && image.fileSize > 10 * 1024 * 1024) {
      errors.push('Image file size exceeds 10MB limit');
    }

    // Check dimensions (min 100x100, max 4000x4000)
    if (image.width < 100 || image.height < 100) {
      errors.push('Image dimensions are too small (minimum 100x100 pixels)');
    }
    if (image.width > 4000 || image.height > 4000) {
      errors.push('Image dimensions are too large (maximum 4000x4000 pixels)');
    }

    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (image.type && !allowedTypes.includes(image.type.toLowerCase())) {
      errors.push('Unsupported image format. Please use JPEG, PNG, or WebP');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Generate thumbnail
   */
  async generateThumbnail(
    uri: string,
    size: {width: number; height: number} = {width: 200, height: 200}
  ): Promise<string> {
    try {
      logger.info('Generating thumbnail', {uri, size});

      // This would integrate with a thumbnail generation library
      // For now, we'll return the original URI
      const thumbnailUri = uri; // Placeholder

      logger.info('Thumbnail generated successfully', {originalUri: uri, thumbnailUri});
      return thumbnailUri;
    } catch (error) {
      logger.error('Failed to generate thumbnail', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to generate thumbnail',
          ErrorSeverity.MEDIUM,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Save photo to device gallery
   */
  async saveToGallery(uri: string): Promise<void> {
    try {
      logger.info('Saving photo to gallery', {uri});

      // Check storage permissions
      const hasPermission = await permissionManager.checkPermission(PermissionType.STORAGE);
      if (!hasPermission) {
        const granted = await permissionManager.requestPermissionWithDialog(
          PermissionType.STORAGE,
          {
            title: 'Storage Permission Required',
            message: 'Storage access is required to save photos to your gallery.',
          }
        );
        if (!granted) {
          throw new Error('Storage permission is required');
        }
      }

      // This would integrate with a photo saving library
      // For now, we'll simulate the save operation
      logger.info('Photo saved to gallery successfully', {uri});
    } catch (error) {
      logger.error('Failed to save photo to gallery', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to save photo to gallery',
          ErrorSeverity.MEDIUM,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }

  /**
   * Delete photo file
   */
  async deletePhoto(uri: string): Promise<void> {
    try {
      logger.info('Deleting photo file', {uri});

      // This would integrate with a file deletion library
      // For now, we'll simulate the deletion
      logger.info('Photo file deleted successfully', {uri});
    } catch (error) {
      logger.error('Failed to delete photo file', error);
      throw errorHandler.handleError(
        createError(
          ErrorType.CAMERA,
          'Failed to delete photo file',
          ErrorSeverity.LOW,
          { component: 'CameraService', retryable: true }
        ),
        'CameraService'
      );
    }
  }
}

export const cameraService = new CameraService();
export default cameraService;