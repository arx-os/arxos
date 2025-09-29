/**
 * Permission Utility Functions
 * Common permission handling functions
 */

import {Platform, PermissionsAndroid, Alert} from 'react-native';

export interface PermissionResult {
  granted: boolean;
  denied: boolean;
  neverAskAgain: boolean;
  error?: string;
}

export const requestCameraPermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.CAMERA,
        {
          title: 'Camera Permission',
          message: 'ArxOS needs access to your camera to capture equipment photos',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically by the image picker
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestLocationPermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        {
          title: 'Location Permission',
          message: 'ArxOS needs access to your location to track equipment positions',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically by the geolocation service
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestStoragePermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
        {
          title: 'Storage Permission',
          message: 'ArxOS needs access to your storage to save and load files',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestNotificationPermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
        {
          title: 'Notification Permission',
          message: 'ArxOS needs to send you notifications about equipment updates and sync status',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically by PushNotification
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestMicrophonePermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        {
          title: 'Microphone Permission',
          message: 'ArxOS needs access to your microphone for voice notes',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestBluetoothPermission = async (): Promise<PermissionResult> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
        {
          title: 'Bluetooth Permission',
          message: 'ArxOS needs access to Bluetooth for device connectivity',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      
      return {
        granted: granted === PermissionsAndroid.RESULTS.GRANTED,
        denied: granted === PermissionsAndroid.RESULTS.DENIED,
        neverAskAgain: granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
      };
    } catch (error: any) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        error: error.message,
      };
    }
  }
  
  // iOS permissions are handled automatically
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
  };
};

export const requestMultiplePermissions = async (permissions: string[]): Promise<{[key: string]: PermissionResult}> => {
  if (Platform.OS === 'android') {
    try {
      const results = await PermissionsAndroid.requestMultiple(permissions);
      const permissionResults: {[key: string]: PermissionResult} = {};
      
      for (const permission of permissions) {
        const result = results[permission];
        permissionResults[permission] = {
          granted: result === PermissionsAndroid.RESULTS.GRANTED,
          denied: result === PermissionsAndroid.RESULTS.DENIED,
          neverAskAgain: result === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
        };
      }
      
      return permissionResults;
    } catch (error: any) {
      const permissionResults: {[key: string]: PermissionResult} = {};
      for (const permission of permissions) {
        permissionResults[permission] = {
          granted: false,
          denied: true,
          neverAskAgain: false,
          error: error.message,
        };
      }
      return permissionResults;
    }
  }
  
  // iOS permissions are handled automatically
  const permissionResults: {[key: string]: PermissionResult} = {};
  for (const permission of permissions) {
    permissionResults[permission] = {
      granted: true,
      denied: false,
      neverAskAgain: false,
    };
  }
  return permissionResults;
};

export const checkPermission = async (permission: string): Promise<boolean> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.check(permission);
      return granted;
    } catch (error) {
      console.error('Error checking permission:', error);
      return false;
    }
  }
  
  // iOS permissions are handled automatically
  return true;
};

export const checkMultiplePermissions = async (permissions: string[]): Promise<{[key: string]: boolean}> => {
  if (Platform.OS === 'android') {
    try {
      const results: {[key: string]: boolean} = {};
      for (const permission of permissions) {
        results[permission] = await PermissionsAndroid.check(permission);
      }
      return results;
    } catch (error) {
      console.error('Error checking multiple permissions:', error);
      const results: {[key: string]: boolean} = {};
      for (const permission of permissions) {
        results[permission] = false;
      }
      return results;
    }
  }
  
  // iOS permissions are handled automatically
  const results: {[key: string]: boolean} = {};
  for (const permission of permissions) {
    results[permission] = true;
  }
  return results;
};

export const openAppSettings = (): void => {
  if (Platform.OS === 'android') {
    // Android: Open app settings
    // This would typically use react-native-permissions or similar
    console.log('Opening app settings for Android');
  } else {
    // iOS: Open app settings
    // This would typically use react-native-permissions or similar
    console.log('Opening app settings for iOS');
  }
};

export const showPermissionDeniedAlert = (permission: string): void => {
  Alert.alert(
    'Permission Denied',
    `ArxOS needs ${permission} permission to function properly. Please enable it in your device settings.`,
    [
      {text: 'Cancel', style: 'cancel'},
      {text: 'Open Settings', onPress: openAppSettings},
    ]
  );
};

export const showPermissionNeverAskAgainAlert = (permission: string): void => {
  Alert.alert(
    'Permission Required',
    `ArxOS needs ${permission} permission to function properly. Please enable it in your device settings.`,
    [
      {text: 'Cancel', style: 'cancel'},
      {text: 'Open Settings', onPress: openAppSettings},
    ]
  );
};

export const handlePermissionResult = (
  result: PermissionResult,
  permission: string,
  onGranted?: () => void,
  onDenied?: () => void
): void => {
  if (result.granted) {
    onGranted?.();
  } else if (result.neverAskAgain) {
    showPermissionNeverAskAgainAlert(permission);
    onDenied?.();
  } else {
    showPermissionDeniedAlert(permission);
    onDenied?.();
  }
};

export const requestAllRequiredPermissions = async (): Promise<{
  camera: PermissionResult;
  location: PermissionResult;
  storage: PermissionResult;
  notification: PermissionResult;
}> => {
  const [camera, location, storage, notification] = await Promise.all([
    requestCameraPermission(),
    requestLocationPermission(),
    requestStoragePermission(),
    requestNotificationPermission(),
  ]);
  
  return {
    camera,
    location,
    storage,
    notification,
  };
};

export const checkAllRequiredPermissions = async (): Promise<{
  camera: boolean;
  location: boolean;
  storage: boolean;
  notification: boolean;
}> => {
  const permissions = [
    PermissionsAndroid.PERMISSIONS.CAMERA,
    PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
    PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
    PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
  ];
  
  const results = await checkMultiplePermissions(permissions);
  
  return {
    camera: results[PermissionsAndroid.PERMISSIONS.CAMERA] || false,
    location: results[PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION] || false,
    storage: results[PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE] || false,
    notification: results[PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS] || false,
  };
};

export const getPermissionStatus = async (permission: string): Promise<{
  granted: boolean;
  denied: boolean;
  neverAskAgain: boolean;
  canAskAgain: boolean;
}> => {
  if (Platform.OS === 'android') {
    try {
      const granted = await PermissionsAndroid.check(permission);
      return {
        granted,
        denied: !granted,
        neverAskAgain: false, // This would need to be tracked separately
        canAskAgain: !granted,
      };
    } catch (error) {
      return {
        granted: false,
        denied: true,
        neverAskAgain: false,
        canAskAgain: false,
      };
    }
  }
  
  // iOS permissions are handled automatically
  return {
    granted: true,
    denied: false,
    neverAskAgain: false,
    canAskAgain: true,
  };
};

export const requestPermissionWithFallback = async (
  permission: string,
  fallbackMessage: string
): Promise<PermissionResult> => {
  try {
    if (permission === 'camera') {
      return await requestCameraPermission();
    } else if (permission === 'location') {
      return await requestLocationPermission();
    } else if (permission === 'storage') {
      return await requestStoragePermission();
    } else if (permission === 'notification') {
      return await requestNotificationPermission();
    } else if (permission === 'microphone') {
      return await requestMicrophonePermission();
    } else if (permission === 'bluetooth') {
      return await requestBluetoothPermission();
    } else {
      throw new Error(`Unknown permission: ${permission}`);
    }
  } catch (error: any) {
    return {
      granted: false,
      denied: true,
      neverAskAgain: false,
      error: error.message,
    };
  }
};
