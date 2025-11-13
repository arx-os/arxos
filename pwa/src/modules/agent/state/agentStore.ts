/**
 * Zustand store for agent connection state
 */

import { create } from "zustand";
import { AgentClient } from "../client/AgentClient";
import type { AgentConnectionState, AgentAction } from "../client/types";

interface AgentStore {
  // Connection state
  connectionState: AgentConnectionState;
  isInitialized: boolean;

  // Actions
  initialize: (token: string) => Promise<void>;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: <T = unknown>(action: AgentAction, payload?: unknown) => Promise<T>;

  // Internal
  updateConnectionState: (state: AgentConnectionState) => void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  connectionState: {
    status: "disconnected",
    quality: "offline",
    reconnectAttempts: 0,
  },
  isInitialized: false,

  initialize: async (token: string) => {
    const client = AgentClient.getInstance({ token, debug: true });

    // Subscribe to connection state changes
    client.onConnectionStateChange((state) => {
      get().updateConnectionState(state);
    });

    set({ isInitialized: true });

    // Auto-connect
    await client.connect();
  },

  connect: async () => {
    if (!get().isInitialized) {
      throw new Error("Agent not initialized. Call initialize() first.");
    }

    const client = AgentClient.getInstance();
    await client.connect();
  },

  disconnect: () => {
    if (!get().isInitialized) {
      return;
    }

    const client = AgentClient.getInstance();
    client.disconnect();
  },

  send: async <T = unknown>(action: AgentAction, payload?: unknown): Promise<T> => {
    if (!get().isInitialized) {
      throw new Error("Agent not initialized. Call initialize() first.");
    }

    const client = AgentClient.getInstance();
    return client.send<T>(action, payload);
  },

  updateConnectionState: (state: AgentConnectionState) => {
    set({ connectionState: state });
  },
}));
