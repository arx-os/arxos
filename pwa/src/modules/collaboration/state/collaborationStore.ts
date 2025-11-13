/**
 * Collaboration State Store
 *
 * Zustand store for managing collaboration state including
 * messages, rooms, users, and connection status.
 */

import { create } from "zustand";
import { CollaborationClient } from "../CollaborationClient";
import {
  isChatMessage,
  isCommentMessage,
  isPresenceUpdate,
} from "../types";
import type {
  CollaborationConfig,
  CollaborationMessage,
  CollaborationRoom,
  CollaborationUser,
  ConnectionState,
  MessageEnvelope,
  ChatMessagePayload,
  CommentMessagePayload,
  PresencePayload,
  MessageStatus,
  UserDID,
  ElementReference,
} from "../types";

interface CollaborationState {
  // Client instance
  client: CollaborationClient | null;

  // Connection state
  connectionState: ConnectionState;
  connectedPeers: number;

  // Rooms
  rooms: Map<string, CollaborationRoom>;
  activeRoomId: string | null;

  // Messages (keyed by room ID)
  messages: Map<string, CollaborationMessage[]>;

  // Users
  users: Map<UserDID, CollaborationUser>;

  // UI state
  sidebarOpen: boolean;
  composerDraft: string;
  selectedElementRef: ElementReference | null;

  // Actions
  initialize: (config: CollaborationConfig) => void;
  disconnect: () => void;
  setActiveRoom: (roomId: string | null) => void;
  sendMessage: (
    roomId: string,
    content: string,
    elementRef?: ElementReference
  ) => Promise<void>;
  joinRoom: (roomId: string) => Promise<void>;
  leaveRoom: (roomId: string) => Promise<void>;
  setSidebarOpen: (open: boolean) => void;
  setComposerDraft: (draft: string) => void;
  setSelectedElementRef: (ref: ElementReference | null) => void;
  updatePresence: (state: "online" | "away" | "typing") => void;
  clearUnread: (roomId: string) => void;

  // Internal helpers
  handleIncomingMessage: (envelope: MessageEnvelope) => void;
  handlePresenceUpdate: (envelope: MessageEnvelope<PresencePayload>) => void;
  addMessage: (roomId: string, message: CollaborationMessage) => void;
  updateMessageStatus: (messageId: string, status: MessageStatus) => void;
  incrementUnread: (roomId: string) => void;
}

export const useCollaborationStore = create<CollaborationState>(
  (set, get) => ({
    // Initial state
    client: null,
    connectionState: "disconnected",
    connectedPeers: 0,
    rooms: new Map(),
    activeRoomId: null,
    messages: new Map(),
    users: new Map(),
    sidebarOpen: false,
    composerDraft: "",
    selectedElementRef: null,

    /**
     * Initialize collaboration client
     */
    initialize: (config: CollaborationConfig) => {
      const { client } = get();

      // Cleanup existing client
      if (client) {
        client.destroy();
      }

      // Create new client
      const newClient = new CollaborationClient(config);

      // Setup event listeners
      newClient.on("connected", () => {
        set({ connectionState: "connected" });
        console.log("Collaboration client connected");
      });

      newClient.on("disconnected", () => {
        set({ connectionState: "disconnected", connectedPeers: 0 });
        console.log("Collaboration client disconnected");
      });

      newClient.on("message", (event) => {
        const envelope = event.data as MessageEnvelope;
        get().handleIncomingMessage(envelope);
      });

      newClient.on("presence", (event) => {
        const envelope = event.data as MessageEnvelope<PresencePayload>;
        get().handlePresenceUpdate(envelope);
      });

      newClient.on("error", (event) => {
        console.error("Collaboration error:", event.error);
        set({ connectionState: "error" });
      });

      set({
        client: newClient,
        connectionState: newClient.getConnectionState(),
      });
    },

    /**
     * Disconnect client
     */
    disconnect: () => {
      const { client } = get();
      if (client) {
        client.disconnect();
        set({ client: null, connectionState: "disconnected" });
      }
    },

    /**
     * Set active room
     */
    setActiveRoom: (roomId: string | null) => {
      set({ activeRoomId: roomId });

      if (roomId) {
        // Mark room as read
        get().clearUnread(roomId);
      }
    },

    /**
     * Send a message
     */
    sendMessage: async (
      roomId: string,
      content: string,
      elementRef?: ElementReference
    ) => {
      const { client, users } = get();
      if (!client) {
        throw new Error("Client not initialized");
      }

      const messageType = elementRef ? "comment" : "chat";
      const payload: ChatMessagePayload | CommentMessagePayload = elementRef
        ? {
            content,
            elementRef,
          }
        : {
            content,
          };

      try {
        // Optimistically add message
        const envelope: MessageEnvelope = {
          version: "1.0.0",
          id: crypto.randomUUID(),
          type: messageType,
          timestamp: Date.now(),
          from: client["config"].userDID,
          to: roomId,
          roomId,
          payload,
        };

        const message: CollaborationMessage = {
          envelope,
          status: "pending",
          localTimestamp: Date.now(),
        };

        get().addMessage(roomId, message);

        // Send via client
        await client.send(messageType, roomId, payload, {
          roomId,
          requiresAck: true,
        });

        // Update status to sent
        get().updateMessageStatus(message.envelope.id, "sent");
      } catch (error) {
        console.error("Failed to send message:", error);
        // Update status to failed
        const messages = get().messages.get(roomId) || [];
        const message = messages.find((m) => m.envelope.to === roomId);
        if (message) {
          get().updateMessageStatus(message.envelope.id, "failed");
        }
        throw error;
      }
    },

    /**
     * Join a room
     */
    joinRoom: async (roomId: string) => {
      const { client } = get();
      if (!client) return;

      try {
        await client.subscribe(roomId);

        // Send join presence
        await client.send(
          "presence",
          roomId,
          {
            state: "online",
            roomId,
          },
          { roomId }
        );
      } catch (error) {
        console.error("Failed to join room:", error);
        throw error;
      }
    },

    /**
     * Leave a room
     */
    leaveRoom: async (roomId: string) => {
      const { client } = get();
      if (!client) return;

      try {
        await client.unsubscribe(roomId);
      } catch (error) {
        console.error("Failed to leave room:", error);
        throw error;
      }
    },

    /**
     * Toggle sidebar
     */
    setSidebarOpen: (open: boolean) => {
      set({ sidebarOpen: open });
    },

    /**
     * Update composer draft
     */
    setComposerDraft: (draft: string) => {
      set({ composerDraft: draft });
    },

    /**
     * Set selected element reference
     */
    setSelectedElementRef: (ref: ElementReference | null) => {
      set({ selectedElementRef: ref });
    },

    /**
     * Update user presence
     */
    updatePresence: (state: "online" | "away" | "typing") => {
      const { client, activeRoomId } = get();
      if (!client || !activeRoomId) return;

      client.send(
        "presence",
        activeRoomId,
        {
          state,
          roomId: activeRoomId,
        },
        { roomId: activeRoomId }
      );
    },

    /**
     * Clear unread count for room
     */
    clearUnread: (roomId: string) => {
      set((state) => {
        const rooms = new Map(state.rooms);
        const room = rooms.get(roomId);
        if (room) {
          rooms.set(roomId, { ...room, unreadCount: 0 });
        }
        return { rooms };
      });
    },

    // Internal helper methods (not exposed in interface)

    /**
     * Handle incoming message
     */
    handleIncomingMessage: (envelope: MessageEnvelope) => {
      const roomId = envelope.roomId || envelope.from;

      const message: CollaborationMessage = {
        envelope,
        status: "delivered",
        localTimestamp: Date.now(),
      };

      get().addMessage(roomId, message);

      // Increment unread count if not active room
      const { activeRoomId } = get();
      if (activeRoomId !== roomId) {
        get().incrementUnread(roomId);
      }
    },

    /**
     * Handle presence update
     */
    handlePresenceUpdate: (envelope: MessageEnvelope<PresencePayload>) => {
      const { payload, from } = envelope;
      if (!isPresenceUpdate(envelope)) return;

      set((state) => {
        const users = new Map(state.users);
        const existingUser = users.get(from);

        users.set(from, {
          did: from,
          displayName: existingUser?.displayName || from.slice(0, 8),
          presence: payload.state,
          lastSeen: payload.lastSeen || Date.now(),
        });

        return { users };
      });
    },

    /**
     * Add message to room
     */
    addMessage: (roomId: string, message: CollaborationMessage) => {
      set((state) => {
        const messages = new Map(state.messages);
        const roomMessages = messages.get(roomId) || [];

        // Check for duplicates
        const exists = roomMessages.some(
          (m) => m.envelope.id === message.envelope.id
        );

        if (!exists) {
          messages.set(roomId, [...roomMessages, message]);
        }

        return { messages };
      });
    },

    /**
     * Update message status
     */
    updateMessageStatus: (messageId: string, status: MessageStatus) => {
      set((state) => {
        const messages = new Map(state.messages);

        for (const [roomId, roomMessages] of messages.entries()) {
          const index = roomMessages.findIndex(
            (m) => m.envelope.id === messageId
          );

          if (index !== -1) {
            const updated = [...roomMessages];
            updated[index] = { ...updated[index], status };
            messages.set(roomId, updated);
            break;
          }
        }

        return { messages };
      });
    },

    /**
     * Increment unread count
     */
    incrementUnread: (roomId: string) => {
      set((state) => {
        const rooms = new Map(state.rooms);
        const room = rooms.get(roomId);

        if (room) {
          rooms.set(roomId, {
            ...room,
            unreadCount: (room.unreadCount || 0) + 1,
          });
        }

        return { rooms };
      });
    },
  })
);
