/**
 * Device Utility Functions
 * Common device information and capabilities functions
 */

import {Platform, Dimensions, PixelRatio} from 'react-native';
import DeviceInfo from 'react-native-device-info';

export interface DeviceInfo {
  platform: string;
  version: string;
  deviceId: string;
  model: string;
  osVersion: string;
  brand: string;
  manufacturer: string;
  isTablet: boolean;
  isEmulator: boolean;
  hasNotch: boolean;
  screenWidth: number;
  screenHeight: number;
  pixelRatio: number;
  fontScale: number;
  totalMemory: number;
  usedMemory: number;
  batteryLevel: number;
  isCharging: boolean;
  isLocationEnabled: boolean;
  isBluetoothEnabled: boolean;
  isWifiEnabled: boolean;
  isCellularEnabled: boolean;
  timezone: string;
  locale: string;
  country: string;
  currency: string;
  language: string;
}

export const getDeviceInfo = async (): Promise<DeviceInfo> => {
  try {
    const [
      deviceId,
      model,
      osVersion,
      brand,
      manufacturer,
      isTablet,
      isEmulator,
      hasNotch,
      totalMemory,
      usedMemory,
      batteryLevel,
      isCharging,
      isLocationEnabled,
      isBluetoothEnabled,
      isWifiEnabled,
      isCellularEnabled,
      timezone,
      locale,
      country,
      currency,
      language,
    ] = await Promise.all([
      DeviceInfo.getUniqueId(),
      DeviceInfo.getModel(),
      DeviceInfo.getSystemVersion(),
      DeviceInfo.getBrand(),
      DeviceInfo.getManufacturer(),
      DeviceInfo.isTablet(),
      DeviceInfo.isEmulator(),
      DeviceInfo.hasNotch(),
      DeviceInfo.getTotalMemory(),
      DeviceInfo.getUsedMemory(),
      DeviceInfo.getBatteryLevel(),
      DeviceInfo.isBatteryCharging(),
      DeviceInfo.isLocationEnabled(),
      DeviceInfo.isBluetoothEnabled(),
      DeviceInfo.isWifiEnabled(),
      DeviceInfo.isCellularEnabled(),
      DeviceInfo.getTimezone(),
      DeviceInfo.getLocale(),
      DeviceInfo.getCountry(),
      DeviceInfo.getCurrency(),
      DeviceInfo.getLanguage(),
    ]);
    
    const {width, height} = Dimensions.get('window');
    
    return {
      platform: Platform.OS,
      version: Platform.Version.toString(),
      deviceId,
      model,
      osVersion,
      brand,
      manufacturer,
      isTablet,
      isEmulator,
      hasNotch,
      screenWidth: width,
      screenHeight: height,
      pixelRatio: PixelRatio.get(),
      fontScale: PixelRatio.getFontScale(),
      totalMemory,
      usedMemory,
      batteryLevel,
      isCharging,
      isLocationEnabled,
      isBluetoothEnabled,
      isWifiEnabled,
      isCellularEnabled,
      timezone,
      locale,
      country,
      currency,
      language,
    };
  } catch (error) {
    console.error('Error getting device info:', error);
    throw error;
  }
};

export const getDeviceId = async (): Promise<string> => {
  try {
    return await DeviceInfo.getUniqueId();
  } catch (error) {
    console.error('Error getting device ID:', error);
    return 'unknown';
  }
};

export const getDeviceModel = async (): Promise<string> => {
  try {
    return await DeviceInfo.getModel();
  } catch (error) {
    console.error('Error getting device model:', error);
    return 'unknown';
  }
};

export const getOSVersion = async (): Promise<string> => {
  try {
    return await DeviceInfo.getSystemVersion();
  } catch (error) {
    console.error('Error getting OS version:', error);
    return Platform.Version.toString();
  }
};

export const getDeviceBrand = async (): Promise<string> => {
  try {
    return await DeviceInfo.getBrand();
  } catch (error) {
    console.error('Error getting device brand:', error);
    return 'unknown';
  }
};

export const getDeviceManufacturer = async (): Promise<string> => {
  try {
    return await DeviceInfo.getManufacturer();
  } catch (error) {
    console.error('Error getting device manufacturer:', error);
    return 'unknown';
  }
};

export const isTablet = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isTablet();
  } catch (error) {
    console.error('Error checking if device is tablet:', error);
    return false;
  }
};

export const isEmulator = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isEmulator();
  } catch (error) {
    console.error('Error checking if device is emulator:', error);
    return false;
  }
};

export const hasNotch = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.hasNotch();
  } catch (error) {
    console.error('Error checking if device has notch:', error);
    return false;
  }
};

export const getScreenDimensions = (): {width: number; height: number} => {
  const {width, height} = Dimensions.get('window');
  return {width, height};
};

export const getScreenSize = (): 'small' | 'medium' | 'large' | 'xlarge' => {
  const {width, height} = Dimensions.get('window');
  const screenWidth = Math.min(width, height);
  
  if (screenWidth < 600) return 'small';
  if (screenWidth < 900) return 'medium';
  if (screenWidth < 1200) return 'large';
  return 'xlarge';
};

export const getPixelRatio = (): number => {
  return PixelRatio.get();
};

export const getFontScale = (): number => {
  return PixelRatio.getFontScale();
};

export const getTotalMemory = async (): Promise<number> => {
  try {
    return await DeviceInfo.getTotalMemory();
  } catch (error) {
    console.error('Error getting total memory:', error);
    return 0;
  }
};

export const getUsedMemory = async (): Promise<number> => {
  try {
    return await DeviceInfo.getUsedMemory();
  } catch (error) {
    console.error('Error getting used memory:', error);
    return 0;
  }
};

export const getMemoryUsage = async (): Promise<{
  total: number;
  used: number;
  free: number;
  percentage: number;
}> => {
  try {
    const total = await DeviceInfo.getTotalMemory();
    const used = await DeviceInfo.getUsedMemory();
    const free = total - used;
    const percentage = (used / total) * 100;
    
    return {
      total,
      used,
      free,
      percentage,
    };
  } catch (error) {
    console.error('Error getting memory usage:', error);
    return {
      total: 0,
      used: 0,
      free: 0,
      percentage: 0,
    };
  }
};

export const getBatteryLevel = async (): Promise<number> => {
  try {
    return await DeviceInfo.getBatteryLevel();
  } catch (error) {
    console.error('Error getting battery level:', error);
    return 0;
  }
};

export const isBatteryCharging = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isBatteryCharging();
  } catch (error) {
    console.error('Error checking if battery is charging:', error);
    return false;
  }
};

export const getBatteryInfo = async (): Promise<{
  level: number;
  isCharging: boolean;
  status: 'charging' | 'discharging' | 'full' | 'unknown';
}> => {
  try {
    const level = await DeviceInfo.getBatteryLevel();
    const isCharging = await DeviceInfo.isBatteryCharging();
    
    let status: 'charging' | 'discharging' | 'full' | 'unknown' = 'unknown';
    if (isCharging) {
      status = level >= 1 ? 'full' : 'charging';
    } else {
      status = 'discharging';
    }
    
    return {
      level,
      isCharging,
      status,
    };
  } catch (error) {
    console.error('Error getting battery info:', error);
    return {
      level: 0,
      isCharging: false,
      status: 'unknown',
    };
  }
};

export const isLocationEnabled = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isLocationEnabled();
  } catch (error) {
    console.error('Error checking if location is enabled:', error);
    return false;
  }
};

export const isBluetoothEnabled = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isBluetoothEnabled();
  } catch (error) {
    console.error('Error checking if Bluetooth is enabled:', error);
    return false;
  }
};

export const isWifiEnabled = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isWifiEnabled();
  } catch (error) {
    console.error('Error checking if WiFi is enabled:', error);
    return false;
  }
};

export const isCellularEnabled = async (): Promise<boolean> => {
  try {
    return await DeviceInfo.isCellularEnabled();
  } catch (error) {
    console.error('Error checking if cellular is enabled:', error);
    return false;
  }
};

export const getTimezone = async (): Promise<string> => {
  try {
    return await DeviceInfo.getTimezone();
  } catch (error) {
    console.error('Error getting timezone:', error);
    return 'UTC';
  }
};

export const getLocale = async (): Promise<string> => {
  try {
    return await DeviceInfo.getLocale();
  } catch (error) {
    console.error('Error getting locale:', error);
    return 'en-US';
  }
};

export const getCountry = async (): Promise<string> => {
  try {
    return await DeviceInfo.getCountry();
  } catch (error) {
    console.error('Error getting country:', error);
    return 'US';
  }
};

export const getCurrency = async (): Promise<string> => {
  try {
    return await DeviceInfo.getCurrency();
  } catch (error) {
    console.error('Error getting currency:', error);
    return 'USD';
  }
};

export const getLanguage = async (): Promise<string> => {
  try {
    return await DeviceInfo.getLanguage();
  } catch (error) {
    console.error('Error getting language:', error);
    return 'en';
  }
};

export const getDeviceCapabilities = async (): Promise<{
  camera: boolean;
  microphone: boolean;
  location: boolean;
  bluetooth: boolean;
  wifi: boolean;
  cellular: boolean;
  accelerometer: boolean;
  gyroscope: boolean;
  magnetometer: boolean;
  barometer: boolean;
  proximity: boolean;
  ambientLight: boolean;
  fingerprint: boolean;
  faceId: boolean;
  nfc: boolean;
  usb: boolean;
}> => {
  try {
    const [
      location,
      bluetooth,
      wifi,
      cellular,
    ] = await Promise.all([
      DeviceInfo.isLocationEnabled(),
      DeviceInfo.isBluetoothEnabled(),
      DeviceInfo.isWifiEnabled(),
      DeviceInfo.isCellularEnabled(),
    ]);
    
    return {
      camera: true, // Assume camera is available
      microphone: true, // Assume microphone is available
      location,
      bluetooth,
      wifi,
      cellular,
      accelerometer: true, // Assume accelerometer is available
      gyroscope: true, // Assume gyroscope is available
      magnetometer: true, // Assume magnetometer is available
      barometer: true, // Assume barometer is available
      proximity: true, // Assume proximity sensor is available
      ambientLight: true, // Assume ambient light sensor is available
      fingerprint: true, // Assume fingerprint sensor is available
      faceId: true, // Assume face ID is available
      nfc: true, // Assume NFC is available
      usb: true, // Assume USB is available
    };
  } catch (error) {
    console.error('Error getting device capabilities:', error);
    return {
      camera: false,
      microphone: false,
      location: false,
      bluetooth: false,
      wifi: false,
      cellular: false,
      accelerometer: false,
      gyroscope: false,
      magnetometer: false,
      barometer: false,
      proximity: false,
      ambientLight: false,
      fingerprint: false,
      faceId: false,
      nfc: false,
      usb: false,
    };
  }
};

export const getDevicePerformance = async (): Promise<{
  cpuCount: number;
  totalMemory: number;
  usedMemory: number;
  memoryUsage: number;
  batteryLevel: number;
  isCharging: boolean;
  performance: 'low' | 'medium' | 'high' | 'unknown';
}> => {
  try {
    const [
      totalMemory,
      usedMemory,
      batteryLevel,
      isCharging,
    ] = await Promise.all([
      DeviceInfo.getTotalMemory(),
      DeviceInfo.getUsedMemory(),
      DeviceInfo.getBatteryLevel(),
      DeviceInfo.isBatteryCharging(),
    ]);
    
    const memoryUsage = (usedMemory / totalMemory) * 100;
    
    let performance: 'low' | 'medium' | 'high' | 'unknown' = 'unknown';
    if (totalMemory >= 4000000000) { // 4GB
      performance = 'high';
    } else if (totalMemory >= 2000000000) { // 2GB
      performance = 'medium';
    } else {
      performance = 'low';
    }
    
    return {
      cpuCount: 0, // This would need to be implemented
      totalMemory,
      usedMemory,
      memoryUsage,
      batteryLevel,
      isCharging,
      performance,
    };
  } catch (error) {
    console.error('Error getting device performance:', error);
    return {
      cpuCount: 0,
      totalMemory: 0,
      usedMemory: 0,
      memoryUsage: 0,
      batteryLevel: 0,
      isCharging: false,
      performance: 'unknown',
    };
  }
};

export const getDeviceSecurity = async (): Promise<{
  isEmulator: boolean;
  isRooted: boolean;
  isJailbroken: boolean;
  hasNotch: boolean;
  securityLevel: 'low' | 'medium' | 'high' | 'unknown';
}> => {
  try {
    const [
      isEmulator,
      isRooted,
      isJailbroken,
      hasNotch,
    ] = await Promise.all([
      DeviceInfo.isEmulator(),
      DeviceInfo.isRooted(),
      DeviceInfo.isJailbroken(),
      DeviceInfo.hasNotch(),
    ]);
    
    let securityLevel: 'low' | 'medium' | 'high' | 'unknown' = 'unknown';
    if (isEmulator || isRooted || isJailbroken) {
      securityLevel = 'low';
    } else if (hasNotch) {
      securityLevel = 'high';
    } else {
      securityLevel = 'medium';
    }
    
    return {
      isEmulator,
      isRooted,
      isJailbroken,
      hasNotch,
      securityLevel,
    };
  } catch (error) {
    console.error('Error getting device security:', error);
    return {
      isEmulator: false,
      isRooted: false,
      isJailbroken: false,
      hasNotch: false,
      securityLevel: 'unknown',
    };
  }
};

export const getDeviceSummary = async (): Promise<{
  platform: string;
  model: string;
  osVersion: string;
  brand: string;
  isTablet: boolean;
  screenSize: string;
  memory: string;
  battery: string;
  capabilities: string[];
  performance: string;
  security: string;
}> => {
  try {
    const [
      deviceInfo,
      capabilities,
      performance,
      security,
    ] = await Promise.all([
      getDeviceInfo(),
      getDeviceCapabilities(),
      getDevicePerformance(),
      getDeviceSecurity(),
    ]);
    
    const memory = `${Math.round(deviceInfo.totalMemory / 1000000000)}GB`;
    const battery = `${Math.round(deviceInfo.batteryLevel * 100)}%`;
    const capabilityList = Object.entries(capabilities)
      .filter(([_, enabled]) => enabled)
      .map(([capability, _]) => capability);
    
    return {
      platform: deviceInfo.platform,
      model: deviceInfo.model,
      osVersion: deviceInfo.osVersion,
      brand: deviceInfo.brand,
      isTablet: deviceInfo.isTablet,
      screenSize: getScreenSize(),
      memory,
      battery,
      capabilities: capabilityList,
      performance: performance.performance,
      security: security.securityLevel,
    };
  } catch (error) {
    console.error('Error getting device summary:', error);
    return {
      platform: 'unknown',
      model: 'unknown',
      osVersion: 'unknown',
      brand: 'unknown',
      isTablet: false,
      screenSize: 'unknown',
      memory: 'unknown',
      battery: 'unknown',
      capabilities: [],
      performance: 'unknown',
      security: 'unknown',
    };
  }
};
