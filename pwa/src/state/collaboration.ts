import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { nanoid } from "nanoid";
import { get as idbGet, set as idbSet, del as idbDel } from "idb-keyval";
import {
  invokeAgent,
  type CollabConfig,
  type CollabSyncResponse,
  type CollabSyncSuccess
} from "../lib/agent";

export type CollaborationMessage = {
  id: string;
  buildingId: string;
  author: string;
  content: string;
  timestamp: number;
  status: "pending" | "sent" | "error";
  remoteId?: number;
  remoteUrl?: string;
  syncedAt?: number;
  errorReason?: string;
};

type CollaborationQueueItem = Omit<CollaborationMessage, "status" | "remoteId" | "remoteUrl" | "syncedAt" | "errorReason">;

type AgentStatus = "idle" | "connecting" | "connected" | "error";

type CollaborationStore = {
  online: boolean;
  messages: CollaborationMessage[];
  queue: CollaborationQueueItem[];
  token: string;
  agentStatus: AgentStatus;
  lastSync?: number;
  syncTarget?: CollabConfig;
  isSyncing: boolean;
  setOnline: (value: boolean) => void;
  setToken: (value: string) => void;
  configureTarget: (config: CollabConfig) => Promise<void>;
  enqueue: (message: Omit<CollaborationQueueItem, "id" | "timestamp">) => void;
  hydrate: () => Promise<void>;
  flushQueue: () => Promise<void>;
  retryMessage: (id: string) => void;
};

const indexedDbStorage = () => {
  if (typeof indexedDB === "undefined") {
    return {
      getItem: (name: string) => Promise.resolve(localStorage.getItem(name)),
      setItem: (name: string, value: string) => {
        localStorage.setItem(name, value);
        return Promise.resolve();
      },
      removeItem: (name: string) => {
        localStorage.removeItem(name);
        return Promise.resolve();
      }
    } satisfies StorageLike;
  }

  return {
    getItem: (name: string) => idbGet<string>(name).then((value) => value ?? null),
    setItem: (name: string, value: string) => idbSet(name, value),
    removeItem: (name: string) => idbDel(name)
  } satisfies StorageLike;
};

type StorageLike = {
  getItem: (key: string) => string | null | Promise<string | null>;
  setItem: (key: string, value: string) => void | Promise<void>;
  removeItem: (key: string) => void | Promise<void>;
};

function serializeQueueEntry(entry: CollaborationQueueItem) {
  return {
    id: entry.id,
    buildingId: entry.buildingId,
    author: entry.author,
    content: entry.content,
    timestamp: entry.timestamp
  };
}

function parseSyncedAt(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export const useCollaborationStore = create<CollaborationStore>()(
  persist(
    (set, get) => ({
      online: typeof navigator !== "undefined" ? navigator.onLine : true,
      messages: [],
      queue: [],
      token: "did:key:zexample",
      agentStatus: "idle",
      lastSync: undefined,
      syncTarget: undefined,
      isSyncing: false,
      setOnline: (value) => set({ online: value }),
      setToken: (value) =>
        set(() => ({
          token: value.trim(),
          agentStatus: "idle"
        })),
      configureTarget: async (config) => {
        const token = get().token;
        if (!token.startsWith("did:key:")) {
          throw new Error("Agent token is required before configuring collaboration");
        }
        set({ agentStatus: "connecting" });
        const response = await invokeAgent<{ config?: CollabConfig }>(token, "collab.config.set", config);
        if (response.status === "error") {
          set({ agentStatus: "error" });
          throw new Error(
            typeof response.payload === "object" && response.payload !== null
              ? (response.payload as Record<string, unknown>).error?.toString() ?? "Failed to save collaboration config"
              : "Failed to save collaboration config"
          );
        }
        const saved = response.payload?.config ?? config;
        set({ syncTarget: saved, agentStatus: "connected" });
        await get().flushQueue();
      },
      enqueue: ({ buildingId, author, content }) => {
        const item: CollaborationQueueItem = {
          id: nanoid(12),
          buildingId,
          author,
          content,
          timestamp: Date.now()
        };
        set((state) => ({
          queue: [...state.queue, item],
          messages: [
            { ...item, status: "pending" as const } as CollaborationMessage,
            ...state.messages
          ].slice(0, 100)
        }));
        const state = get();
        if (state.online && !state.isSyncing) {
          void state.flushQueue();
        }
      },
      hydrate: async () => {
        const token = get().token;
        if (!token.startsWith("did:key:")) {
          return;
        }

        try {
          const configResponse = await invokeAgent<{ config?: CollabConfig }>(token, "collab.config.get");
          if (configResponse.status === "ok" && configResponse.payload?.config) {
            set({ syncTarget: configResponse.payload.config });
          }
        } catch (error) {
          console.warn("Failed to load collaboration config", error);
        }

        const state = get();
        if (!state.online || state.queue.length === 0) {
          return;
        }

        await state.flushQueue();
      },
      flushQueue: async () => {
        const state = get();
        if (state.isSyncing || state.queue.length === 0) {
          return;
        }
        const token = state.token;
        if (!token.startsWith("did:key:")) {
          return;
        }
        if (!state.syncTarget) {
          set({ agentStatus: "error" });
          return;
        }

        set({ agentStatus: "connecting", isSyncing: true });

        try {
          const payload = {
            messages: state.queue.map(serializeQueueEntry)
          };

          const response = await invokeAgent<CollabSyncResponse | Record<string, unknown>>(
            token,
            "collab.sync",
            payload
          );

          if (response.status === "error") {
            set({ agentStatus: "error", isSyncing: false });
            return;
          }

          const outcome = response.payload as CollabSyncResponse;
          const successMap = new Map(outcome.successes.map((success) => [success.id, success]));
          const errorMap = new Map(outcome.errors.map((error) => [error.id, error.error]));

          set((current) => {
            const remainingQueue = current.queue.filter(
              (item) => !successMap.has(item.id) && !errorMap.has(item.id)
            );

            const updatedMessages: CollaborationMessage[] = current.messages.map((message) => {
              if (successMap.has(message.id)) {
                const success = successMap.get(message.id) as CollabSyncSuccess;
                return {
                  ...message,
                  status: "sent" as const,
                  remoteId: success.remoteId,
                  remoteUrl: success.remoteUrl,
                  syncedAt: parseSyncedAt(success.syncedAt),
                  errorReason: undefined
                } satisfies CollaborationMessage;
              }

              if (errorMap.has(message.id)) {
                return {
                  ...message,
                  status: "error" as const,
                  errorReason: errorMap.get(message.id)
                } satisfies CollaborationMessage;
              }

              return message;
            });

            const messages = updatedMessages.slice(0, 100);

            const hasErrors = errorMap.size > 0;
            const lastSync = successMap.size > 0 ? Date.now() : current.lastSync;

            return {
              queue: remainingQueue,
              messages,
              agentStatus: hasErrors ? "error" : "connected",
              lastSync,
              isSyncing: false
            };
          });
        } catch (error) {
          console.warn("Failed to synchronise collaboration queue", error);
          set({ agentStatus: "error", isSyncing: false });
        }
      },
      retryMessage: (id) => {
        const state = get();
        const existing = state.messages.find((message) => message.id === id);
        if (!existing) {
          return;
        }

        const retried: CollaborationQueueItem = {
          id,
          buildingId: existing.buildingId,
          author: existing.author,
          content: existing.content,
          timestamp: Date.now()
        };

        set((current) => ({
          queue: [...current.queue, retried],
          messages: current.messages.map((message) =>
            message.id === id
              ? {
                  ...message,
                  status: "pending" as const,
                  timestamp: retried.timestamp,
                  errorReason: undefined
                }
              : message
          )
        }));

        if (state.online && !get().isSyncing) {
          void get().flushQueue();
        }
      }
    }),
    {
      name: "arxos-collaboration",
      storage: createJSONStorage(() => indexedDbStorage())
    }
  )
);

