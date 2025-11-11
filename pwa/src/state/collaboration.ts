import { create } from "zustand";
import { persist } from "zustand/middleware";
import { nanoid } from "nanoid";

const AGENT_ENDPOINT = "ws://127.0.0.1:8787/ws";

export type CollaborationMessage = {
  id: string;
  buildingId: string;
  author: string;
  content: string;
  timestamp: number;
  status: "pending" | "sent" | "error";
};

type AgentStatus = "idle" | "connecting" | "connected" | "error";

type CollaborationStore = {
  online: boolean;
  messages: CollaborationMessage[];
  queue: CollaborationMessage[];
  token: string;
  agentStatus: AgentStatus;
  setOnline: (value: boolean) => void;
  setToken: (value: string) => void;
  enqueue: (message: Omit<CollaborationMessage, "id" | "timestamp" | "status">) => void;
  markSent: (id: string) => void;
  markError: (id: string) => void;
  hydrate: () => Promise<void>;
};

async function sendViaAgent(message: CollaborationMessage, token: string): Promise<void> {
  if (!token.startsWith("did:key:")) {
    throw new Error("Agent token must be a DID:key");
  }

  return new Promise((resolve, reject) => {
    let acknowledged = false;
    const socket = new WebSocket(`${AGENT_ENDPOINT}?token=${encodeURIComponent(token)}`);

    socket.addEventListener("open", () => {
      socket.send(
        JSON.stringify({
          id: message.id,
          action: "ping",
          payload: {
            buildingId: message.buildingId,
            author: message.author,
            content: message.content,
            timestamp: message.timestamp
          }
        })
      );
    });

    socket.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.payload?.message === "connected") {
          return; // initial handshake
        }
        if (data?.status === "ok") {
          acknowledged = true;
          resolve();
          socket.close();
        } else {
          reject(new Error(data?.payload?.error ?? "Agent rejected message"));
          socket.close();
        }
      } catch (error) {
        reject(error instanceof Error ? error : new Error(String(error)));
        socket.close();
      }
    });

    socket.addEventListener("error", () => {
      if (!acknowledged) {
        reject(new Error("Unable to reach ArxOS agent"));
      }
    });

    socket.addEventListener("close", () => {
      if (!acknowledged) {
        reject(new Error("Agent connection closed"));
      }
    });
  });
}

export const useCollaborationStore = create<CollaborationStore>()(
  persist(
    (set, get) => ({
      online: typeof navigator !== "undefined" ? navigator.onLine : true,
      messages: [],
      queue: [],
      token: "did:key:zexample",
      agentStatus: "idle",
      setOnline: (value) => set({ online: value }),
      setToken: (value) => set({ token: value.trim() }),
      enqueue: ({ buildingId, author, content }) => {
        const item: CollaborationMessage = {
          id: nanoid(12),
          buildingId,
          author,
          content,
          timestamp: Date.now(),
          status: "pending"
        };
        set((state) => ({
          queue: [...state.queue, item],
          messages: [item, ...state.messages].slice(0, 50)
        }));
      },
      markSent: (id) =>
        set((state) => ({
          queue: state.queue.filter((item) => item.id !== id),
          messages: state.messages.map((item) =>
            item.id === id ? { ...item, status: "sent", timestamp: Date.now() } : item
          )
        })),
      markError: (id) =>
        set((state) => ({
          messages: state.messages.map((item) =>
            item.id === id ? { ...item, status: "error" } : item
          )
        })),
      hydrate: async () => {
        const state = get();
        if (!state.online || state.queue.length === 0) {
          return;
        }
        set({ agentStatus: "connecting" });
        for (const message of state.queue) {
          try {
            await sendViaAgent(message, get().token);
            get().markSent(message.id);
          } catch (error) {
            console.warn("Failed to sync message", error);
            get().markError(message.id);
            set({ agentStatus: "error" });
            return;
          }
        }
        set({ agentStatus: "connected" });
      }
    }),
    { name: "arxos-collaboration" }
  )
);

