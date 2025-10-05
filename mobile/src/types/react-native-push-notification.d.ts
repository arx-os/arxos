declare module 'react-native-push-notification' {
  interface PushNotificationOptions {
    onRegister?: (token: string) => void;
    onNotification?: (notification: any) => void;
    onAction?: (notification: any) => void;
    onRegistrationError?: (error: any) => void;
    onRemoteFetch?: (notificationData: any) => void;
    permissions?: {
      alert?: boolean;
      badge?: boolean;
      sound?: boolean;
    };
    popInitialNotification?: boolean;
    requestPermissions?: boolean;
  }

  interface PushNotification {
    configure(options: PushNotificationOptions): void;
    localNotification(details: any): void;
    localNotificationSchedule(details: any): void;
    scheduleLocalNotification(details: any): void;
    cancelLocalNotifications(details: any): void;
    cancelAllLocalNotifications(): void;
    removeAllDeliveredNotifications(): void;
    getDeliveredNotifications(callback: (notifications: any[]) => void): void;
    getScheduledLocalNotifications(callback: (notifications: any[]) => void): void;
    setApplicationIconBadgeNumber(number: number): void;
    getApplicationIconBadgeNumber(callback: (badgeCount: number) => void): void;
    popInitialNotification(callback: (notification: any) => void): void;
    requestPermissions(): void;
    abandonPermissions(): void;
    checkPermissions(callback: (permissions: any) => void): void;
    getChannels(callback: (channels: any[]) => void): void;
    channelExists(channelId: string, callback: (exists: boolean) => void): void;
    createChannel(channel: any, callback: (created: boolean) => void): void;
    channelBlocked(channelId: string, callback: (blocked: boolean) => void): void;
    deleteChannel(channelId: string, callback: (deleted: boolean) => void): void;
  }

  const PushNotification: PushNotification;
  export default PushNotification;
}
