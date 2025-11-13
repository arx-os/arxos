/**
 * Zustand store for authentication state
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthStore {
  // State
  token: string | null;
  isAuthenticated: boolean;
  lastValidated?: Date;

  // Actions
  setToken: (token: string) => void;
  clearToken: () => void;
  validateToken: (token: string) => boolean;
}

/**
 * Validate DID:key token format
 */
function validateDidKeyFormat(token: string): boolean {
  // DID:key format: did:key:z{base58}
  const didKeyRegex = /^did:key:z[1-9A-HJ-NP-Za-km-z]+$/;
  return didKeyRegex.test(token);
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      token: null,
      isAuthenticated: false,

      setToken: (token: string) => {
        const isValid = get().validateToken(token);

        if (!isValid) {
          throw new Error("Invalid DID:key token format");
        }

        set({
          token,
          isAuthenticated: true,
          lastValidated: new Date(),
        });
      },

      clearToken: () => {
        set({
          token: null,
          isAuthenticated: false,
          lastValidated: undefined,
        });
      },

      validateToken: (token: string) => {
        return validateDidKeyFormat(token);
      },
    }),
    {
      name: "arxos-auth",
      // Only persist in sessionStorage (ephemeral)
      storage: {
        getItem: (name) => {
          const value = sessionStorage.getItem(name);
          return value ? JSON.parse(value) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
    }
  )
);
