/**
 * Permissions Utility
 * Comprehensive permission handling for ArxOS Mobile
 */

import {Platform, Alert, Linking} from 'react-native';
import {request, check, PERMISSIONS, RESULTS, Permission} from 'react-native-permissions';
import {logger} from './logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from './errorHandler';

export enum PermissionType {
  CAMERA = 'CAMERA',
  LOCATION = 'LOCATION',
  STORAGE = 'STORAGE',
  NOTIFICATIONS = 'NOTIFICATIONS',
  MICROPHONE = 'MICROPHONE',
}

export interface PermissionResult {
  granted: boolean;
  status: string;
  canAskAgain: boolean;
}

class PermissionManager {
  private permissionMap: Record<PermissionType, Permission> = {
    [PermissionType.CAMERA]: Platform.select({
      ios: PERMISSIONS.IOS.CAMERA,
      android: PERMISSIONS.ANDROID.CAMERA,
    }) as Permission,
    [PermissionType.LOCATION]: Platform.select({
      ios: PERMISSIONS.IOS.LOCATION_WHEN_IN_USE,
      android: PERMISSIONS.ANDROID.ACCESS_FINE_LOCATION,
    }) as Permission,
    [PermissionType.STORAGE]: Platform.select({
      ios: PERMISSIONS.IOS.PHOTO_LIBRARY,
      android: PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
    }) as Permission,
    [PermissionType.NOTIFICATIONS]: Platform.select({
      ios: PERMISSIONS.IOS.NOTIFICATIONS,
      android: PERMISSIONS.ANDROID.POST_NOTIFICATIONS,
    }) as Permission,
    [PermissionType.MICROPHONE]: Platform.select({
      ios: PERMISSIONS.IOS.MICROPHONE,
      android: PERMISSIONS.ANDROID.RECORD_AUDIO,
    }) as Permission,
  };

  /**
   * Check permission status
   */
  async checkPermission(permissionType: PermissionType): Promise<PermissionResult> {
    try {
      const permission = this.permissionMap[permissionType];
      if (!permission) {
        throw new Error(`Permission not supported: ${permissionType}`);
      }

      const result = await check(permission);
      
      logger.debug('Permission check result', {
        permission: permissionType,
        status: result,
      }, 'PermissionManager');

      return {
        granted: result === RESULTS.GRANTED,
        status: result,
        canAskAgain: result !== RESULTS.DENIED,
      };
    } catch (error) {
      logger.error('Permission check failed', error, 'PermissionManager');
      throw errorHandler.handleError(
        createError(
          ErrorType.VALIDATION,
          `Failed to check ${permissionType} permission`,
          ErrorSeverity.MEDIUM,
          { component: 'PermissionManager', retryable: true }
        ),
        'PermissionManager'
      );
    }
  }

  /**
   * Request permission
   */
  async requestPermission(permissionType: PermissionType): Promise<PermissionResult> {
    try {
      const permission = this.permissionMap[permissionType];
      if (!permission) {
        throw new Error(`Permission not supported: ${permissionType}`);
      }

      const result = await request(permission);
      
      logger.info('Permission request result', {
        permission: permissionType,
        status: result,
      }, 'PermissionManager');

      return {
        granted: result === RESULTS.GRANTED,
        status: result,
        canAskAgain: result !== RESULTS.DENIED,
      };
    } catch (error) {
      logger.error('Permission request failed', error, 'PermissionManager');
      throw errorHandler.handleError(
        createError(
          ErrorType.VALIDATION,
          `Failed to request ${permissionType} permission`,
          ErrorSeverity.MEDIUM,
          { component: 'PermissionManager', retryable: true }
        ),
        'PermissionManager'
      );
    }
  }

  /**
   * Request permission with user-friendly dialog
   */
  async requestPermissionWithDialog(
    permissionType: PermissionType,
    options: {
      title: string;
      message: string;
      buttonText?: string;
      onDenied?: () => void;
    }
  ): Promise<PermissionResult> {
    try {
      // Check current status first
      const currentStatus = await this.checkPermission(permissionType);
      
      if (currentStatus.granted) {
        return currentStatus;
      }

      if (!currentStatus.canAskAgain) {
        // Permission was permanently denied, show settings dialog
        this.showSettingsDialog(permissionType, options);
        return currentStatus;
      }

      // Show permission explanation dialog
      return new Promise((resolve) => {
        Alert.alert(
          options.title,
          options.message,
          [
            {
              text: 'Cancel',
              style: 'cancel',
              onPress: () => {
                options.onDenied?.();
                resolve({
                  granted: false,
                  status: RESULTS.DENIED,
                  canAskAgain: true,
                });
              },
            },
            {
              text: options.buttonText || 'Allow',
              onPress: async () => {
                try {
                  const result = await this.requestPermission(permissionType);
                  resolve(result);
                } catch (error) {
                  logger.error('Permission request failed in dialog', error, 'PermissionManager');
                  resolve({
                    granted: false,
                    status: RESULTS.DENIED,
                    canAskAgain: false,
                  });
                }
              },
            },
          ]
        );
      });
    } catch (error) {
      logger.error('Permission dialog failed', error, 'PermissionManager');
      throw errorHandler.handleError(
        createError(
          ErrorType.VALIDATION,
          `Failed to show permission dialog for ${permissionType}`,
          ErrorSeverity.MEDIUM,
          { component: 'PermissionManager', retryable: true }
        ),
        'PermissionManager'
      );
    }
  }

  /**
   * Show settings dialog for permanently denied permissions
   */
  private showSettingsDialog(
    permissionType: PermissionType,
    options: {
      title: string;
      message: string;
    }
  ): void {
    Alert.alert(
      options.title,
      `${options.message}\n\nThis permission is required for the app to function properly. Please enable it in Settings.`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Open Settings',
          onPress: () => {
            Linking.openSettings();
          },
        },
      ]
    );
  }

  /**
   * Request multiple permissions
   */
  async requestMultiplePermissions(
    permissions: PermissionType[]
  ): Promise<Record<PermissionType, PermissionResult>> {
    const results: Record<PermissionType, PermissionResult> = {} as any;

    for (const permissionType of permissions) {
      try {
        results[permissionType] = await this.requestPermission(permissionType);
      } catch (error) {
        logger.error(`Failed to request ${permissionType} permission`, error, 'PermissionManager');
        results[permissionType] = {
          granted: false,
          status: RESULTS.DENIED,
          canAskAgain: false,
        };
      }
    }

    return results;
  }

  /**
   * Check if all required permissions are granted
   */
  async checkRequiredPermissions(
    permissions: PermissionType[]
  ): Promise<{allGranted: boolean; results: Record<PermissionType, PermissionResult>}> {
    const results = await this.requestMultiplePermissions(permissions);
    const allGranted = Object.values(results).every(result => result.granted);

    return {
      allGranted,
      results,
    };
  }

  /**
   * Get permission display name
   */
  getPermissionDisplayName(permissionType: PermissionType): string {
    switch (permissionType) {
      case PermissionType.CAMERA:
        return 'Camera';
      case PermissionType.LOCATION:
        return 'Location';
      case PermissionType.STORAGE:
        return 'Storage';
      case PermissionType.NOTIFICATIONS:
        return 'Notifications';
      case PermissionType.MICROPHONE:
        return 'Microphone';
      default:
        return 'Unknown Permission';
    }
  }

  /**
   * Get permission description
   */
  getPermissionDescription(permissionType: PermissionType): string {
    switch (permissionType) {
      case PermissionType.CAMERA:
        return 'Required to capture photos of equipment and building components';
      case PermissionType.LOCATION:
        return 'Required for AR features and location-based equipment tracking';
      case PermissionType.STORAGE:
        return 'Required to save photos and offline data';
      case PermissionType.NOTIFICATIONS:
        return 'Required to receive maintenance alerts and system notifications';
      case PermissionType.MICROPHONE:
        return 'Required for voice notes and audio recording features';
      default:
        return 'Required for app functionality';
    }
  }
}

// Create singleton instance
export const permissionManager = new PermissionManager();

// Convenience functions
export const checkPermission = (permissionType: PermissionType) =>
  permissionManager.checkPermission(permissionType);

export const requestPermission = (permissionType: PermissionType) =>
  permissionManager.requestPermission(permissionType);

export const requestPermissionWithDialog = (
  permissionType: PermissionType,
  options: {
    title: string;
    message: string;
    buttonText?: string;
    onDenied?: () => void;
  }
) => permissionManager.requestPermissionWithDialog(permissionType, options);

export const requestMultiplePermissions = (permissions: PermissionType[]) =>
  permissionManager.requestMultiplePermissions(permissions);

export const checkRequiredPermissions = (permissions: PermissionType[]) =>
  permissionManager.checkRequiredPermissions(permissions);

export default permissionManager;
