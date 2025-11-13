/**
 * Authentication store tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { useAuthStore } from "../state/authStore";

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(global, "sessionStorage", {
  value: mockSessionStorage,
  writable: true,
});

beforeEach(() => {
  mockSessionStorage.clear();
  useAuthStore.setState({
    token: null,
    isAuthenticated: false,
    lastValidated: undefined,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("authStore", () => {
  describe("token validation", () => {
    it("should validate correct DID:key token", () => {
      const store = useAuthStore.getState();
      const isValid = store.validateToken("did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK");

      expect(isValid).toBe(true);
    });

    it("should reject token without did:key prefix", () => {
      const store = useAuthStore.getState();
      const isValid = store.validateToken("z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK");

      expect(isValid).toBe(false);
    });

    it("should reject empty token", () => {
      const store = useAuthStore.getState();
      const isValid = store.validateToken("");

      expect(isValid).toBe(false);
    });

    it("should reject token without identifier", () => {
      const store = useAuthStore.getState();
      const isValid = store.validateToken("did:key:");

      expect(isValid).toBe(false);
    });
  });

  describe("setToken", () => {
    it("should set valid token", () => {
      const store = useAuthStore.getState();
      const validToken = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";

      store.setToken(validToken);

      const state = useAuthStore.getState();
      expect(state.token).toBe(validToken);
      expect(state.isAuthenticated).toBe(true);
      expect(state.lastValidated).toBeInstanceOf(Date);
    });

    it("should throw on invalid token", () => {
      const store = useAuthStore.getState();

      expect(() => {
        store.setToken("invalid-token");
      }).toThrow("Invalid DID:key token format");
    });

    it("should persist token to sessionStorage", () => {
      const store = useAuthStore.getState();
      const validToken = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";

      store.setToken(validToken);

      const stored = sessionStorage.getItem("arxos-auth");
      expect(stored).toBeTruthy();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.token).toBe(validToken);
    });
  });

  describe("clearToken", () => {
    it("should clear authentication state", () => {
      const store = useAuthStore.getState();
      const validToken = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";

      store.setToken(validToken);
      store.clearToken();

      const state = useAuthStore.getState();
      expect(state.token).toBeFalsy();
      expect(state.isAuthenticated).toBe(false);
    });

    it("should remove from sessionStorage", () => {
      const store = useAuthStore.getState();
      const validToken = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";

      store.setToken(validToken);
      store.clearToken();

      const stored = sessionStorage.getItem("arxos-auth");
      const parsed = stored ? JSON.parse(stored) : null;

      expect(parsed?.state.token).toBeFalsy();
    });
  });

  describe("persistence", () => {
    it("should persist token to sessionStorage", () => {
      const validToken = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";

      const store = useAuthStore.getState();
      store.setToken(validToken);

      // Check that it was persisted
      const stored = sessionStorage.getItem("arxos-auth");
      expect(stored).toBeTruthy();

      if (stored) {
        const parsed = JSON.parse(stored);
        expect(parsed.state.token).toBe(validToken);
      }
    });
  });
});
