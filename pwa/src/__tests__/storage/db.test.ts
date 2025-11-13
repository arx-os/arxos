/**
 * Storage layer tests - IndexedDB utilities
 */

import { describe, it, expect, beforeEach } from "vitest";
import { getItem, setItem, deleteItem, clearStorage } from "../../lib/storage/db";

describe("IndexedDB storage utilities", () => {
  beforeEach(async () => {
    // Clear storage before each test
    await clearStorage();
  });

  it("should store and retrieve a string value", async () => {
    await setItem("test-key", "test-value");
    const value = await getItem<string>("test-key");
    expect(value).toBe("test-value");
  });

  it("should store and retrieve an object", async () => {
    const testObject = { id: 1, name: "Test", active: true };
    await setItem("test-object", testObject);
    const value = await getItem<typeof testObject>("test-object");
    expect(value).toEqual(testObject);
  });

  it("should return null for non-existent keys", async () => {
    const value = await getItem<string>("non-existent");
    expect(value).toBeNull();
  });

  it("should delete items", async () => {
    await setItem("test-key", "test-value");
    await deleteItem("test-key");
    const value = await getItem<string>("test-key");
    expect(value).toBeNull();
  });

  it("should clear all items", async () => {
    await setItem("key1", "value1");
    await setItem("key2", "value2");
    await clearStorage();
    const value1 = await getItem<string>("key1");
    const value2 = await getItem<string>("key2");
    expect(value1).toBeNull();
    expect(value2).toBeNull();
  });

  it("should handle array values", async () => {
    const testArray = [1, 2, 3, 4, 5];
    await setItem("test-array", testArray);
    const value = await getItem<number[]>("test-array");
    expect(value).toEqual(testArray);
  });

  it("should handle nested objects", async () => {
    const nested = {
      level1: {
        level2: {
          level3: "deep value",
        },
      },
    };
    await setItem("nested", nested);
    const value = await getItem<typeof nested>("nested");
    expect(value).toEqual(nested);
  });
});
