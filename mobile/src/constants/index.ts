/**
 * Application Constants
 * Centralized constants for ArxOS Mobile
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: __DEV__ ? 'http://localhost:8080/api/v1' : 'https://api.arxos.com/v1',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Sync Configuration
export const SYNC_CONFIG = {
  AUTO_SYNC_INTERVAL: 300000, // 5 minutes
  MAX_RETRIES: 3,
  RETRY_DELAY: 5000,
  BATCH_SIZE: 50,
  COMPRESSION_ENABLED: true,
};

// AR Configuration
export const AR_CONFIG = {
  PLANE_DETECTION: true,
  LIGHT_ESTIMATION: true,
  WORLD_ALIGNMENT: 'gravity' as const,
  MAX_TRACKED_IMAGES: 10,
  ENABLE_AUTO_FOCUS: true,
  ENABLE_DEPTH: false,
};

// Camera Configuration
export const CAMERA_CONFIG = {
  DEFAULT_QUALITY: 0.8,
  MAX_WIDTH: 1920,
  MAX_HEIGHT: 1080,
  ALLOWS_EDITING: false,
  MEDIA_TYPE: 'photo' as const,
};

// Storage Configuration
export const STORAGE_CONFIG = {
  DATABASE_NAME: 'ArxOSMobile.db',
  DATABASE_VERSION: 1,
  MAX_SIZE: 100 * 1024 * 1024, // 100MB
  BACKUP_ENABLED: true,
};

// Security Configuration
export const SECURITY_CONFIG = {
  AUTO_LOCK_TIMEOUT: 300000, // 5 minutes
  SESSION_TIMEOUT: 3600000, // 1 hour
  REQUIRE_PASSWORD_ON_STARTUP: false,
  BIOMETRIC_ENABLED: false,
};

// Notification Configuration
export const NOTIFICATION_CONFIG = {
  CHANNEL_ID: 'arxos-default',
  CHANNEL_NAME: 'ArxOS Default',
  CHANNEL_DESCRIPTION: 'Default notification channel for ArxOS',
  IMPORTANCE: 4,
  VIBRATE: true,
  SOUND_NAME: 'default',
};

// Theme Configuration
export const THEME_CONFIG = {
  PRIMARY_COLOR: '#007AFF',
  SECONDARY_COLOR: '#5856D6',
  SUCCESS_COLOR: '#4CAF50',
  WARNING_COLOR: '#FF9800',
  ERROR_COLOR: '#F44336',
  INFO_COLOR: '#2196F3',
  BACKGROUND_COLOR: '#F5F5F5',
  SURFACE_COLOR: '#FFFFFF',
  TEXT_PRIMARY: '#333333',
  TEXT_SECONDARY: '#666666',
  TEXT_DISABLED: '#999999',
  BORDER_COLOR: '#E0E0E0',
  SHADOW_COLOR: '#000000',
};

// Layout Configuration
export const LAYOUT_CONFIG = {
  HEADER_HEIGHT: 60,
  TAB_BAR_HEIGHT: 60,
  DRAWER_WIDTH: 280,
  BORDER_RADIUS: 8,
  SHADOW_OFFSET: {width: 0, height: 2},
  SHADOW_OPACITY: 0.1,
  SHADOW_RADIUS: 4,
  ELEVATION: 3,
};

// Animation Configuration
export const ANIMATION_CONFIG = {
  DURATION_SHORT: 200,
  DURATION_MEDIUM: 300,
  DURATION_LONG: 500,
  EASING: 'ease-in-out',
  SPRING_CONFIG: {
    tension: 100,
    friction: 8,
  },
};

// Equipment Status Configuration
export const EQUIPMENT_STATUS = {
  NORMAL: 'normal',
  NEEDS_REPAIR: 'needs-repair',
  FAILED: 'failed',
  OFFLINE: 'offline',
  MAINTENANCE: 'maintenance',
} as const;

export const EQUIPMENT_STATUS_COLORS = {
  [EQUIPMENT_STATUS.NORMAL]: '#4CAF50',
  [EQUIPMENT_STATUS.NEEDS_REPAIR]: '#FF9800',
  [EQUIPMENT_STATUS.FAILED]: '#F44336',
  [EQUIPMENT_STATUS.OFFLINE]: '#9E9E9E',
  [EQUIPMENT_STATUS.MAINTENANCE]: '#2196F3',
} as const;

// Sync Status Configuration
export const SYNC_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export const SYNC_STATUS_COLORS = {
  [SYNC_STATUS.PENDING]: '#2196F3',
  [SYNC_STATUS.PROCESSING]: '#FF9800',
  [SYNC_STATUS.COMPLETED]: '#4CAF50',
  [SYNC_STATUS.FAILED]: '#F44336',
  [SYNC_STATUS.CANCELLED]: '#999999',
} as const;

// AR Tracking State Configuration
export const AR_TRACKING_STATE = {
  NORMAL: 'normal',
  LIMITED: 'limited',
  NOT_AVAILABLE: 'notAvailable',
} as const;

export const AR_TRACKING_STATE_COLORS = {
  [AR_TRACKING_STATE.NORMAL]: '#4CAF50',
  [AR_TRACKING_STATE.LIMITED]: '#FF9800',
  [AR_TRACKING_STATE.NOT_AVAILABLE]: '#F44336',
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection error. Please check your internet connection.',
  AUTHENTICATION_ERROR: 'Authentication failed. Please check your credentials.',
  AUTHORIZATION_ERROR: 'You do not have permission to perform this action.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNKNOWN_ERROR: 'An unknown error occurred. Please try again.',
  CAMERA_PERMISSION_DENIED: 'Camera permission is required to take photos.',
  LOCATION_PERMISSION_DENIED: 'Location permission is required for this feature.',
  STORAGE_PERMISSION_DENIED: 'Storage permission is required to save files.',
  AR_NOT_SUPPORTED: 'Augmented Reality is not supported on this device.',
  AR_PERMISSION_DENIED: 'Camera permission is required for AR features.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Login successful!',
  LOGOUT_SUCCESS: 'Logout successful!',
  SYNC_SUCCESS: 'Data synced successfully!',
  PHOTO_UPLOAD_SUCCESS: 'Photo uploaded successfully!',
  STATUS_UPDATE_SUCCESS: 'Equipment status updated successfully!',
  NOTE_ADDED_SUCCESS: 'Note added successfully!',
  SETTINGS_SAVED_SUCCESS: 'Settings saved successfully!',
  ANCHOR_CREATED_SUCCESS: 'Spatial anchor created successfully!',
  ANCHOR_UPDATED_SUCCESS: 'Spatial anchor updated successfully!',
  ANCHOR_DELETED_SUCCESS: 'Spatial anchor deleted successfully!',
} as const;

// Validation Rules
export const VALIDATION_RULES = {
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 50,
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_MAX_LENGTH: 100,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_REGEX: /^\+?[\d\s\-\(\)]+$/,
  EQUIPMENT_NAME_MIN_LENGTH: 1,
  EQUIPMENT_NAME_MAX_LENGTH: 100,
  NOTE_MAX_LENGTH: 1000,
  SEARCH_QUERY_MIN_LENGTH: 1,
  SEARCH_QUERY_MAX_LENGTH: 100,
} as const;

// File Configuration
export const FILE_CONFIG = {
  MAX_PHOTO_SIZE: 10 * 1024 * 1024, // 10MB
  SUPPORTED_PHOTO_TYPES: ['image/jpeg', 'image/png', 'image/webp'],
  MAX_PHOTOS_PER_EQUIPMENT: 10,
  PHOTO_COMPRESSION_QUALITY: 0.8,
  THUMBNAIL_SIZE: 200,
} as const;

// Performance Configuration
export const PERFORMANCE_CONFIG = {
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 1000,
  CACHE_SIZE: 100,
  CACHE_TTL: 300000, // 5 minutes
  MAX_CONCURRENT_REQUESTS: 5,
  REQUEST_TIMEOUT: 30000,
} as const;
