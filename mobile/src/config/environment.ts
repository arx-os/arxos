/**
 * Environment Configuration
 * Centralized configuration management for ArxOS Mobile
 */

export interface EnvironmentConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;
  
  // Development Settings
  debugMode: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  
  // Sync Configuration
  autoSyncInterval: number;
  maxRetries: number;
  batchSize: number;
  
  // AR Configuration
  arEnabled: boolean;
  planeDetection: boolean;
  lightEstimation: boolean;
  
  // Camera Configuration
  cameraQuality: number;
  maxPhotoSize: number;
  
  // Storage Configuration
  databaseName: string;
  maxStorageSize: number;
  
  // Security Configuration
  sessionTimeout: number;
  autoLockTimeout: number;
  
  // Notification Configuration
  pushNotifications: boolean;
  syncNotifications: boolean;
}

// Default configuration
const defaultConfig: EnvironmentConfig = {
  // API Configuration
  apiBaseUrl: 'http://localhost:8080/api/v1',
  apiTimeout: 30000,
  
  // Development Settings
  debugMode: __DEV__,
  logLevel: __DEV__ ? 'debug' : 'info',
  
  // Sync Configuration
  autoSyncInterval: 300000, // 5 minutes
  maxRetries: 3,
  batchSize: 50,
  
  // AR Configuration
  arEnabled: true,
  planeDetection: true,
  lightEstimation: true,
  
  // Camera Configuration
  cameraQuality: 0.8,
  maxPhotoSize: 10 * 1024 * 1024, // 10MB
  
  // Storage Configuration
  databaseName: 'ArxOSMobile.db',
  maxStorageSize: 100 * 1024 * 1024, // 100MB
  
  // Security Configuration
  sessionTimeout: 3600000, // 1 hour
  autoLockTimeout: 300000, // 5 minutes
  
  // Notification Configuration
  pushNotifications: true,
  syncNotifications: true,
};

// Environment-specific overrides
const getEnvironmentConfig = (): Partial<EnvironmentConfig> => {
  if (__DEV__) {
    return {
      apiBaseUrl: 'http://localhost:8080/api/v1',
      debugMode: true,
      logLevel: 'debug',
    };
  }
  
  return {
    apiBaseUrl: 'https://api.arxos.com/v1',
    debugMode: false,
    logLevel: 'info',
  };
};

// Merge default config with environment-specific overrides
export const environment: EnvironmentConfig = {
  ...defaultConfig,
  ...getEnvironmentConfig(),
};

// Validation function
export const validateEnvironment = (): boolean => {
  try {
    // Validate required fields
    if (!environment.apiBaseUrl) {
      console.error('Environment validation failed: API base URL is required');
      return false;
    }
    
    if (environment.apiTimeout <= 0) {
      console.error('Environment validation failed: API timeout must be positive');
      return false;
    }
    
    if (environment.cameraQuality < 0 || environment.cameraQuality > 1) {
      console.error('Environment validation failed: Camera quality must be between 0 and 1');
      return false;
    }
    
    if (environment.maxPhotoSize <= 0) {
      console.error('Environment validation failed: Max photo size must be positive');
      return false;
    }
    
    if (environment.sessionTimeout <= 0) {
      console.error('Environment validation failed: Session timeout must be positive');
      return false;
    }
    
    if (environment.autoLockTimeout <= 0) {
      console.error('Environment validation failed: Auto lock timeout must be positive');
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Environment validation failed:', error);
    return false;
  }
};

// Initialize environment validation
if (!validateEnvironment()) {
  throw new Error('Environment configuration validation failed');
}

export default environment;
