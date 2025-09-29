/**
 * Settings Redux Slice
 * Manages app settings and preferences
 */

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

// Settings state interface
interface SettingsState {
  // App settings
  theme: 'light' | 'dark' | 'auto';
  language: string;
  fontSize: 'small' | 'medium' | 'large';
  
  // Sync settings
  autoSync: boolean;
  syncInterval: number;
  maxRetries: number;
  retryDelay: number;
  batchSize: number;
  compressionEnabled: boolean;
  
  // AR settings
  arEnabled: boolean;
  planeDetection: boolean;
  lightEstimation: boolean;
  worldAlignment: 'gravity' | 'gravityAndHeading' | 'camera';
  
  // Camera settings
  cameraQuality: 'low' | 'medium' | 'high';
  autoFocus: boolean;
  flashEnabled: boolean;
  
  // Security settings
  biometricEnabled: boolean;
  autoLockTimeout: number;
  requirePasswordOnStartup: boolean;
  sessionTimeout: number;
  
  // Notification settings
  pushNotifications: boolean;
  emailNotifications: boolean;
  syncNotifications: boolean;
  errorNotifications: boolean;
  
  // Debug settings
  debugMode: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  performanceMonitoring: boolean;
}

// Initial state
const initialState: SettingsState = {
  // App settings
  theme: 'auto',
  language: 'en',
  fontSize: 'medium',
  
  // Sync settings
  autoSync: true,
  syncInterval: 300000, // 5 minutes
  maxRetries: 3,
  retryDelay: 5000, // 5 seconds
  batchSize: 50,
  compressionEnabled: true,
  
  // AR settings
  arEnabled: true,
  planeDetection: true,
  lightEstimation: true,
  worldAlignment: 'gravity',
  
  // Camera settings
  cameraQuality: 'medium',
  autoFocus: true,
  flashEnabled: false,
  
  // Security settings
  biometricEnabled: false,
  autoLockTimeout: 300000, // 5 minutes
  requirePasswordOnStartup: false,
  sessionTimeout: 3600000, // 1 hour
  
  // Notification settings
  pushNotifications: true,
  emailNotifications: false,
  syncNotifications: true,
  errorNotifications: true,
  
  // Debug settings
  debugMode: __DEV__,
  logLevel: __DEV__ ? 'debug' : 'info',
  performanceMonitoring: false,
};

// Settings slice
const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    // App settings
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    setFontSize: (state, action: PayloadAction<'small' | 'medium' | 'large'>) => {
      state.fontSize = action.payload;
    },
    
    // Sync settings
    setAutoSync: (state, action: PayloadAction<boolean>) => {
      state.autoSync = action.payload;
    },
    setSyncInterval: (state, action: PayloadAction<number>) => {
      state.syncInterval = action.payload;
    },
    setMaxRetries: (state, action: PayloadAction<number>) => {
      state.maxRetries = action.payload;
    },
    setRetryDelay: (state, action: PayloadAction<number>) => {
      state.retryDelay = action.payload;
    },
    setBatchSize: (state, action: PayloadAction<number>) => {
      state.batchSize = action.payload;
    },
    setCompressionEnabled: (state, action: PayloadAction<boolean>) => {
      state.compressionEnabled = action.payload;
    },
    
    // AR settings
    setAREnabled: (state, action: PayloadAction<boolean>) => {
      state.arEnabled = action.payload;
    },
    setPlaneDetection: (state, action: PayloadAction<boolean>) => {
      state.planeDetection = action.payload;
    },
    setLightEstimation: (state, action: PayloadAction<boolean>) => {
      state.lightEstimation = action.payload;
    },
    setWorldAlignment: (state, action: PayloadAction<'gravity' | 'gravityAndHeading' | 'camera'>) => {
      state.worldAlignment = action.payload;
    },
    
    // Camera settings
    setCameraQuality: (state, action: PayloadAction<'low' | 'medium' | 'high'>) => {
      state.cameraQuality = action.payload;
    },
    setAutoFocus: (state, action: PayloadAction<boolean>) => {
      state.autoFocus = action.payload;
    },
    setFlashEnabled: (state, action: PayloadAction<boolean>) => {
      state.flashEnabled = action.payload;
    },
    
    // Security settings
    setBiometricEnabled: (state, action: PayloadAction<boolean>) => {
      state.biometricEnabled = action.payload;
    },
    setAutoLockTimeout: (state, action: PayloadAction<number>) => {
      state.autoLockTimeout = action.payload;
    },
    setRequirePasswordOnStartup: (state, action: PayloadAction<boolean>) => {
      state.requirePasswordOnStartup = action.payload;
    },
    setSessionTimeout: (state, action: PayloadAction<number>) => {
      state.sessionTimeout = action.payload;
    },
    
    // Notification settings
    setPushNotifications: (state, action: PayloadAction<boolean>) => {
      state.pushNotifications = action.payload;
    },
    setEmailNotifications: (state, action: PayloadAction<boolean>) => {
      state.emailNotifications = action.payload;
    },
    setSyncNotifications: (state, action: PayloadAction<boolean>) => {
      state.syncNotifications = action.payload;
    },
    setErrorNotifications: (state, action: PayloadAction<boolean>) => {
      state.errorNotifications = action.payload;
    },
    
    // Debug settings
    setDebugMode: (state, action: PayloadAction<boolean>) => {
      state.debugMode = action.payload;
    },
    setLogLevel: (state, action: PayloadAction<'error' | 'warn' | 'info' | 'debug'>) => {
      state.logLevel = action.payload;
    },
    setPerformanceMonitoring: (state, action: PayloadAction<boolean>) => {
      state.performanceMonitoring = action.payload;
    },
    
    // Reset settings
    resetSettings: (state) => {
      return initialState;
    },
    
    // Update multiple settings at once
    updateSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      return {...state, ...action.payload};
    },
  },
});

export const {
  // App settings
  setTheme,
  setLanguage,
  setFontSize,
  
  // Sync settings
  setAutoSync,
  setSyncInterval,
  setMaxRetries,
  setRetryDelay,
  setBatchSize,
  setCompressionEnabled,
  
  // AR settings
  setAREnabled,
  setPlaneDetection,
  setLightEstimation,
  setWorldAlignment,
  
  // Camera settings
  setCameraQuality,
  setAutoFocus,
  setFlashEnabled,
  
  // Security settings
  setBiometricEnabled,
  setAutoLockTimeout,
  setRequirePasswordOnStartup,
  setSessionTimeout,
  
  // Notification settings
  setPushNotifications,
  setEmailNotifications,
  setSyncNotifications,
  setErrorNotifications,
  
  // Debug settings
  setDebugMode,
  setLogLevel,
  setPerformanceMonitoring,
  
  // Reset settings
  resetSettings,
  updateSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
