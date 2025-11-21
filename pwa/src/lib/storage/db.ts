/**
 * IndexedDB initialization and utilities
 */

import { get, set, del, clear, keys, entries } from "idb-keyval";
import type {
  QueuedCommand,
  Session,
  PersistedEdit,
  STORAGE_KEYS,
} from "./types";

/**
 * Get a value from IndexedDB with type safety
 */
export async function getItem<T>(key: string): Promise<T | null> {
  try {
    const value = await get<T>(key);
    return value ?? null;
  } catch (error) {
    console.error(`Failed to get item from storage: ${key}`, error);
    return null;
  }
}

/**
 * Set a value in IndexedDB
 */
export async function setItem<T>(key: string, value: T): Promise<void> {
  try {
    await set(key, value);
  } catch (error) {
    console.error(`Failed to set item in storage: ${key}`, error);
    throw error;
  }
}

/**
 * Delete a value from IndexedDB
 */
export async function deleteItem(key: string): Promise<void> {
  try {
    await del(key);
  } catch (error) {
    console.error(`Failed to delete item from storage: ${key}`, error);
    throw error;
  }
}

/**
 * Clear all storage
 */
export async function clearStorage(): Promise<void> {
  try {
    await clear();
  } catch (error) {
    console.error("Failed to clear storage", error);
    throw error;
  }
}

/**
 * Get all keys from storage
 */
export async function getAllKeys(): Promise<IDBValidKey[]> {
  try {
    return await keys();
  } catch (error) {
    console.error("Failed to get all keys", error);
    return [];
  }
}

/**
 * Get all entries from storage
 */
export async function getAllEntries<T>(): Promise<[IDBValidKey, T][]> {
  try {
    return (await entries()) as [IDBValidKey, T][];
  } catch (error) {
    console.error("Failed to get all entries", error);
    return [];
  }
}

/**
 * Initialize storage (create any necessary indexes)
 */
export async function initializeStorage(): Promise<void> {
  try {
    // Verify storage is accessible
    await set("arxos:init-test", true);
    await del("arxos:init-test");
  } catch (error) {
    console.error("Failed to initialize IndexedDB", error);
    throw new Error(
      "IndexedDB is not available. Offline functionality will not work."
    );
  }
}

/**
 * Check if storage is available
 */
export async function isStorageAvailable(): Promise<boolean> {
  try {
    await set("arxos:test", true);
    const result = await get("arxos:test");
    await del("arxos:test");
    return result === true;
  } catch {
    return false;
  }
}
