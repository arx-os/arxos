/**
 * Storage Utility Functions
 * Common storage and data persistence functions
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export const setItem = async (key: string, value: any): Promise<void> => {
  try {
    const jsonValue = JSON.stringify(value);
    await AsyncStorage.setItem(key, jsonValue);
  } catch (error) {
    console.error('Error setting item:', error);
    throw error;
  }
};

export const getItem = async <T>(key: string, defaultValue?: T): Promise<T | null> => {
  try {
    const jsonValue = await AsyncStorage.getItem(key);
    if (jsonValue === null) {
      return defaultValue || null;
    }
    return JSON.parse(jsonValue);
  } catch (error) {
    console.error('Error getting item:', error);
    return defaultValue || null;
  }
};

export const removeItem = async (key: string): Promise<void> => {
  try {
    await AsyncStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing item:', error);
    throw error;
  }
};

export const clear = async (): Promise<void> => {
  try {
    await AsyncStorage.clear();
  } catch (error) {
    console.error('Error clearing storage:', error);
    throw error;
  }
};

export const getAllKeys = async (): Promise<string[]> => {
  try {
    return await AsyncStorage.getAllKeys();
  } catch (error) {
    console.error('Error getting all keys:', error);
    return [];
  }
};

export const multiGet = async (keys: string[]): Promise<[string, string | null][]> => {
  try {
    return await AsyncStorage.multiGet(keys);
  } catch (error) {
    console.error('Error multi getting items:', error);
    return [];
  }
};

export const multiSet = async (keyValuePairs: [string, string][]): Promise<void> => {
  try {
    await AsyncStorage.multiSet(keyValuePairs);
  } catch (error) {
    console.error('Error multi setting items:', error);
    throw error;
  }
};

export const multiRemove = async (keys: string[]): Promise<void> => {
  try {
    await AsyncStorage.multiRemove(keys);
  } catch (error) {
    console.error('Error multi removing items:', error);
    throw error;
  }
};

export const getStorageSize = async (): Promise<number> => {
  try {
    const keys = await getAllKeys();
    const items = await multiGet(keys);
    
    let totalSize = 0;
    for (const [key, value] of items) {
      if (value) {
        totalSize += key.length + value.length;
      }
    }
    
    return totalSize;
  } catch (error) {
    console.error('Error calculating storage size:', error);
    return 0;
  }
};

export const getStorageInfo = async (): Promise<{
  totalSize: number;
  itemCount: number;
  keys: string[];
}> => {
  try {
    const keys = await getAllKeys();
    const totalSize = await getStorageSize();
    
    return {
      totalSize,
      itemCount: keys.length,
      keys,
    };
  } catch (error) {
    console.error('Error getting storage info:', error);
    return {
      totalSize: 0,
      itemCount: 0,
      keys: [],
    };
  }
};

export const clearExpiredItems = async (maxAge: number = 7 * 24 * 60 * 60 * 1000): Promise<void> => {
  try {
    const keys = await getAllKeys();
    const items = await multiGet(keys);
    const now = Date.now();
    const expiredKeys: string[] = [];
    
    for (const [key, value] of items) {
      if (value) {
        try {
          const data = JSON.parse(value);
          if (data.timestamp && (now - data.timestamp) > maxAge) {
            expiredKeys.push(key);
          }
        } catch {
          // If we can't parse the value, skip it
        }
      }
    }
    
    if (expiredKeys.length > 0) {
      await multiRemove(expiredKeys);
    }
  } catch (error) {
    console.error('Error clearing expired items:', error);
  }
};

export const backupStorage = async (): Promise<string> => {
  try {
    const keys = await getAllKeys();
    const items = await multiGet(keys);
    const backup: {[key: string]: any} = {};
    
    for (const [key, value] of items) {
      if (value) {
        try {
          backup[key] = JSON.parse(value);
        } catch {
          backup[key] = value;
        }
      }
    }
    
    return JSON.stringify(backup, null, 2);
  } catch (error) {
    console.error('Error creating backup:', error);
    throw error;
  }
};

export const restoreStorage = async (backupData: string): Promise<void> => {
  try {
    const backup = JSON.parse(backupData);
    const keyValuePairs: [string, string][] = [];
    
    for (const [key, value] of Object.entries(backup)) {
      keyValuePairs.push([key, JSON.stringify(value)]);
    }
    
    await multiSet(keyValuePairs);
  } catch (error) {
    console.error('Error restoring backup:', error);
    throw error;
  }
};

export const exportStorage = async (): Promise<{
  data: string;
  timestamp: number;
  version: string;
}> => {
  try {
    const data = await backupStorage();
    return {
      data,
      timestamp: Date.now(),
      version: '1.0.0',
    };
  } catch (error) {
    console.error('Error exporting storage:', error);
    throw error;
  }
};

export const importStorage = async (exportData: {
  data: string;
  timestamp: number;
  version: string;
}): Promise<void> => {
  try {
    await restoreStorage(exportData.data);
  } catch (error) {
    console.error('Error importing storage:', error);
    throw error;
  }
};

export const migrateStorage = async (fromVersion: string, toVersion: string): Promise<void> => {
  try {
    // Implement migration logic based on version changes
    console.log(`Migrating storage from ${fromVersion} to ${toVersion}`);
    
    // Example migration logic
    if (fromVersion === '1.0.0' && toVersion === '1.1.0') {
      // Migrate from 1.0.0 to 1.1.0
      const keys = await getAllKeys();
      const items = await multiGet(keys);
      const newItems: [string, string][] = [];
      
      for (const [key, value] of items) {
        if (value) {
          try {
            const data = JSON.parse(value);
            // Apply migration transformations
            const migratedData = migrateData(data, fromVersion, toVersion);
            newItems.push([key, JSON.stringify(migratedData)]);
          } catch {
            newItems.push([key, value]);
          }
        }
      }
      
      await multiSet(newItems);
    }
  } catch (error) {
    console.error('Error migrating storage:', error);
    throw error;
  }
};

const migrateData = (data: any, fromVersion: string, toVersion: string): any => {
  // Implement data migration logic
  // This is a placeholder - implement actual migration logic based on your needs
  
  if (fromVersion === '1.0.0' && toVersion === '1.1.0') {
    // Example: Add new fields or transform existing data
    return {
      ...data,
      migratedAt: Date.now(),
      version: toVersion,
    };
  }
  
  return data;
};

export const validateStorage = async (): Promise<{
  isValid: boolean;
  errors: string[];
}> => {
  try {
    const keys = await getAllKeys();
    const items = await multiGet(keys);
    const errors: string[] = [];
    
    for (const [key, value] of items) {
      if (value) {
        try {
          JSON.parse(value);
        } catch {
          errors.push(`Invalid JSON for key: ${key}`);
        }
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  } catch (error) {
    console.error('Error validating storage:', error);
    return {
      isValid: false,
      errors: [`Storage validation failed: ${error}`],
    };
  }
};

export const repairStorage = async (): Promise<void> => {
  try {
    const validation = await validateStorage();
    if (validation.isValid) {
      return;
    }
    
    // Remove invalid items
    const keys = await getAllKeys();
    const items = await multiGet(keys);
    const invalidKeys: string[] = [];
    
    for (const [key, value] of items) {
      if (value) {
        try {
          JSON.parse(value);
        } catch {
          invalidKeys.push(key);
        }
      }
    }
    
    if (invalidKeys.length > 0) {
      await multiRemove(invalidKeys);
    }
  } catch (error) {
    console.error('Error repairing storage:', error);
    throw error;
  }
};

export const getStorageUsage = async (): Promise<{
  used: number;
  available: number;
  percentage: number;
}> => {
  try {
    const totalSize = await getStorageSize();
    const maxSize = 100 * 1024 * 1024; // 100MB limit
    
    return {
      used: totalSize,
      available: maxSize - totalSize,
      percentage: (totalSize / maxSize) * 100,
    };
  } catch (error) {
    console.error('Error getting storage usage:', error);
    return {
      used: 0,
      available: 0,
      percentage: 0,
    };
  }
};

export const cleanupStorage = async (): Promise<void> => {
  try {
    // Clear expired items
    await clearExpiredItems();
    
    // Repair storage if needed
    await repairStorage();
    
    // Clear old logs if storage is getting full
    const usage = await getStorageUsage();
    if (usage.percentage > 80) {
      // Clear old log entries
      const keys = await getAllKeys();
      const logKeys = keys.filter(key => key.startsWith('log_'));
      if (logKeys.length > 100) {
        // Keep only the most recent 100 log entries
        const sortedKeys = logKeys.sort();
        const keysToRemove = sortedKeys.slice(0, sortedKeys.length - 100);
        await multiRemove(keysToRemove);
      }
    }
  } catch (error) {
    console.error('Error cleaning up storage:', error);
    throw error;
  }
};
