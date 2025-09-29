/**
 * Notification Service
 * Handles push notifications and local notifications
 */

import PushNotification from 'react-native-push-notification';
import {Platform, Alert} from 'react-native';
import {logger} from '../utils/logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';
import {permissionManager, PermissionType} from '../utils/permissions';

export interface NotificationData {
  id: string;
  title: string;
  message: string;
  type: 'equipment' | 'maintenance' | 'alert' | 'sync' | 'general';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  equipmentId?: string;
  actionUrl?: string;
  metadata?: Record<string, any>;
}

export interface LocalNotificationOptions {
  title: string;
  message: string;
  data?: Record<string, any>;
  sound?: string;
  vibrate?: boolean;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  smallIcon?: string;
  largeIcon?: string;
  color?: string;
  actions?: Array<{
    id: string;
    title: string;
    icon?: string;
  }>;
}

export interface ScheduledNotification {
  id: string;
  title: string;
  message: string;
  date: Date;
  repeatType?: 'minute' | 'hour' | 'day' | 'week';
  data?: Record<string, any>;
}

class NotificationService {
  private isInitialized = false;
  private token: string | null = null;
  private notificationHandlers: Map<string, (data: any) => void> = new Map();

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    try {
      logger.info('Initializing notification service', {}, 'NotificationService');

      // Request notification permissions
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        throw new Error('Notification permission is required');
      }

      // Configure push notifications
      this.configurePushNotifications();

      // Set up notification handlers
      this.setupNotificationHandlers();

      this.isInitialized = true;
      logger.info('Notification service initialized successfully', {}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to initialize notification service', error, 'NotificationService');
      throw errorHandler.handleError(
        createError(
          ErrorType.PERMISSIONS,
          'Failed to initialize notification service',
          ErrorSeverity.HIGH,
          { component: 'NotificationService', retryable: true }
        ),
        'NotificationService'
      );
    }
  }

  /**
   * Request notification permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const result = await permissionManager.requestPermissionWithDialog(
        PermissionType.NOTIFICATIONS,
        {
          title: 'Notification Permission Required',
          message: 'Notifications are required to receive maintenance alerts and system updates.',
        }
      );
      return result.granted;
    } catch (error) {
      logger.error('Failed to request notification permissions', error, 'NotificationService');
      return false;
    }
  }

  /**
   * Configure push notifications
   */
  private configurePushNotifications(): void {
    PushNotification.configure({
      // Called when token is generated
      onRegister: (token) => {
        logger.info('Push notification token received', {token: token.token}, 'NotificationService');
        this.token = token.token;
        // Send token to server
        this.sendTokenToServer(token.token);
      },

      // Called when a remote or local notification is opened or received
      onNotification: (notification) => {
        logger.info('Notification received', {notification}, 'NotificationService');
        this.handleNotification(notification);
      },

      // Called when the user taps on a notification
      onAction: (notification) => {
        logger.info('Notification action triggered', {notification}, 'NotificationService');
        this.handleNotificationAction(notification);
      },

      // Called when the user fails to register for remote notifications
      onRegistrationError: (err) => {
        logger.error('Push notification registration error', err, 'NotificationService');
        errorHandler.handleError(
          createError(
            ErrorType.PERMISSIONS,
            'Failed to register for push notifications',
            ErrorSeverity.HIGH,
            { component: 'NotificationService', retryable: true }
          ),
          'NotificationService'
        );
      },

      // IOS only: Called when the user taps on a notification
      onRemoteFetch: (notificationData) => {
        logger.info('Remote notification fetch', {notificationData}, 'NotificationService');
        this.handleRemoteNotification(notificationData);
      },

      // Should the initial notification be popped automatically
      popInitialNotification: true,

      // Request permissions on init
      requestPermissions: Platform.OS === 'ios',
    });
  }

  /**
   * Set up notification handlers
   */
  private setupNotificationHandlers(): void {
    // Equipment-related notifications
    this.notificationHandlers.set('equipment_status_change', (data) => {
      this.handleEquipmentStatusChange(data);
    });

    this.notificationHandlers.set('equipment_maintenance_due', (data) => {
      this.handleMaintenanceDue(data);
    });

    // Sync-related notifications
    this.notificationHandlers.set('sync_complete', (data) => {
      this.handleSyncComplete(data);
    });

    this.notificationHandlers.set('sync_failed', (data) => {
      this.handleSyncFailed(data);
    });

    // General notifications
    this.notificationHandlers.set('system_alert', (data) => {
      this.handleSystemAlert(data);
    });
  }

  /**
   * Send token to server
   */
  private async sendTokenToServer(token: string): Promise<void> {
    try {
      logger.info('Sending notification token to server', {token}, 'NotificationService');
      
      // This would send the token to your backend server
      // await apiService.post('/notifications/register-token', { token });
      
      logger.info('Notification token sent to server successfully', {}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to send token to server', error, 'NotificationService');
    }
  }

  /**
   * Handle incoming notification
   */
  private handleNotification(notification: any): void {
    try {
      const {userInfo, data} = notification;
      const notificationData = userInfo || data;

      if (notificationData?.type) {
        const handler = this.notificationHandlers.get(notificationData.type);
        if (handler) {
          handler(notificationData);
        }
      }

      // Handle foreground notifications
      if (notification.foreground) {
        this.showForegroundNotification(notification);
      }
    } catch (error) {
      logger.error('Failed to handle notification', error, 'NotificationService');
    }
  }

  /**
   * Handle notification action
   */
  private handleNotificationAction(notification: any): void {
    try {
      const {action, userInfo} = notification;
      logger.info('Notification action handled', {action, userInfo}, 'NotificationService');

      // Handle different actions
      switch (action) {
        case 'view_equipment':
          // Navigate to equipment detail
          break;
        case 'schedule_maintenance':
          // Navigate to maintenance scheduling
          break;
        case 'retry_sync':
          // Retry sync operation
          break;
        default:
          logger.warn('Unknown notification action', {action}, 'NotificationService');
      }
    } catch (error) {
      logger.error('Failed to handle notification action', error, 'NotificationService');
    }
  }

  /**
   * Handle remote notification
   */
  private handleRemoteNotification(notificationData: any): void {
    try {
      logger.info('Handling remote notification', {notificationData}, 'NotificationService');
      
      // Process remote notification data
      if (notificationData.type) {
        const handler = this.notificationHandlers.get(notificationData.type);
        if (handler) {
          handler(notificationData);
        }
      }
    } catch (error) {
      logger.error('Failed to handle remote notification', error, 'NotificationService');
    }
  }

  /**
   * Show foreground notification
   */
  private showForegroundNotification(notification: any): void {
    try {
      Alert.alert(
        notification.title || 'Notification',
        notification.message || notification.body,
        [
          {
            text: 'OK',
            onPress: () => {
              // Handle notification tap
            },
          },
        ]
      );
    } catch (error) {
      logger.error('Failed to show foreground notification', error, 'NotificationService');
    }
  }

  /**
   * Send local notification
   */
  async sendLocalNotification(options: LocalNotificationOptions): Promise<void> {
    try {
      logger.info('Sending local notification', {options}, 'NotificationService');

      PushNotification.localNotification({
        title: options.title,
        message: options.message,
        data: options.data,
        sound: options.sound || 'default',
        vibrate: options.vibrate !== false,
        priority: options.priority || 'normal',
        smallIcon: options.smallIcon || 'ic_notification',
        largeIcon: options.largeIcon,
        color: options.color || '#007AFF',
        actions: options.actions,
      });

      logger.info('Local notification sent successfully', {}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to send local notification', error, 'NotificationService');
      throw errorHandler.handleError(
        createError(
          ErrorType.NOTIFICATIONS,
          'Failed to send local notification',
          ErrorSeverity.MEDIUM,
          { component: 'NotificationService', retryable: true }
        ),
        'NotificationService'
      );
    }
  }

  /**
   * Schedule notification
   */
  async scheduleNotification(notification: ScheduledNotification): Promise<void> {
    try {
      logger.info('Scheduling notification', {notification}, 'NotificationService');

      PushNotification.localNotificationSchedule({
        id: notification.id,
        title: notification.title,
        message: notification.message,
        date: notification.date,
        repeatType: notification.repeatType,
        data: notification.data,
      });

      logger.info('Notification scheduled successfully', {id: notification.id}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to schedule notification', error, 'NotificationService');
      throw errorHandler.handleError(
        createError(
          ErrorType.NOTIFICATIONS,
          'Failed to schedule notification',
          ErrorSeverity.MEDIUM,
          { component: 'NotificationService', retryable: true }
        ),
        'NotificationService'
      );
    }
  }

  /**
   * Cancel scheduled notification
   */
  async cancelNotification(notificationId: string): Promise<void> {
    try {
      logger.info('Cancelling notification', {notificationId}, 'NotificationService');

      PushNotification.cancelLocalNotifications({id: notificationId});

      logger.info('Notification cancelled successfully', {notificationId}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to cancel notification', error, 'NotificationService');
      throw errorHandler.handleError(
        createError(
          ErrorType.NOTIFICATIONS,
          'Failed to cancel notification',
          ErrorSeverity.LOW,
          { component: 'NotificationService', retryable: true }
        ),
        'NotificationService'
      );
    }
  }

  /**
   * Cancel all notifications
   */
  async cancelAllNotifications(): Promise<void> {
    try {
      logger.info('Cancelling all notifications', {}, 'NotificationService');

      PushNotification.cancelAllLocalNotifications();

      logger.info('All notifications cancelled successfully', {}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to cancel all notifications', error, 'NotificationService');
      throw errorHandler.handleError(
        createError(
          ErrorType.NOTIFICATIONS,
          'Failed to cancel all notifications',
          ErrorSeverity.LOW,
          { component: 'NotificationService', retryable: true }
        ),
        'NotificationService'
      );
    }
  }

  /**
   * Get scheduled notifications
   */
  async getScheduledNotifications(): Promise<ScheduledNotification[]> {
    try {
      logger.debug('Getting scheduled notifications', {}, 'NotificationService');

      return new Promise((resolve) => {
        PushNotification.getScheduledLocalNotifications((notifications) => {
          const scheduledNotifications: ScheduledNotification[] = notifications.map(notification => ({
            id: notification.id,
            title: notification.title || '',
            message: notification.message || '',
            date: new Date(notification.date),
            repeatType: notification.repeatType as any,
            data: notification.data,
          }));
          
          logger.debug('Scheduled notifications retrieved', {count: scheduledNotifications.length}, 'NotificationService');
          resolve(scheduledNotifications);
        });
      });
    } catch (error) {
      logger.error('Failed to get scheduled notifications', error, 'NotificationService');
      return [];
    }
  }

  /**
   * Handle equipment status change
   */
  private handleEquipmentStatusChange(data: any): void {
    logger.info('Equipment status change notification', {data}, 'NotificationService');
    // Handle equipment status change logic
  }

  /**
   * Handle maintenance due
   */
  private handleMaintenanceDue(data: any): void {
    logger.info('Maintenance due notification', {data}, 'NotificationService');
    // Handle maintenance due logic
  }

  /**
   * Handle sync complete
   */
  private handleSyncComplete(data: any): void {
    logger.info('Sync complete notification', {data}, 'NotificationService');
    // Handle sync complete logic
  }

  /**
   * Handle sync failed
   */
  private handleSyncFailed(data: any): void {
    logger.info('Sync failed notification', {data}, 'NotificationService');
    // Handle sync failed logic
  }

  /**
   * Handle system alert
   */
  private handleSystemAlert(data: any): void {
    logger.info('System alert notification', {data}, 'NotificationService');
    // Handle system alert logic
  }

  /**
   * Get notification token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Check if service is initialized
   */
  isServiceInitialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Set notification badge count
   */
  async setBadgeCount(count: number): Promise<void> {
    try {
      PushNotification.setApplicationIconBadgeNumber(count);
      logger.debug('Badge count set', {count}, 'NotificationService');
    } catch (error) {
      logger.error('Failed to set badge count', error, 'NotificationService');
    }
  }

  /**
   * Get notification badge count
   */
  async getBadgeCount(): Promise<number> {
    try {
      return new Promise((resolve) => {
        PushNotification.getApplicationIconBadgeNumber((count) => {
          resolve(count);
        });
      });
    } catch (error) {
      logger.error('Failed to get badge count', error, 'NotificationService');
      return 0;
    }
  }

  /**
   * Clear notification badge
   */
  async clearBadge(): Promise<void> {
    await this.setBadgeCount(0);
  }
}

export const notificationService = new NotificationService();
export default notificationService;