/**
 * Session store for offline session management
 */

import { create } from "zustand";
import {
  getActiveSession,
  createSession as createSessionStorage,
  updateSession,
  clearSession as clearSessionStorage,
  markSyncing,
  markMerged,
  markConflicted,
} from "../../../lib/storage/session";
import {
  createSessionBranch,
  mergeSessionBranch,
  deleteSessionBranch,
} from "../../agent/commands/session";
import {
  clearSessionCommands,
  clearSessionEdits,
} from "../../../lib/storage";
import type { Session, GitConflict, MergeResult } from "../../../lib/storage/types";

type SyncStatus = "idle" | "syncing" | "synced" | "conflicted" | "error";

interface SessionStore {
  // State
  currentSession: Session | null;
  syncStatus: SyncStatus;
  syncError: string | null;
  conflicts: GitConflict[] | null;
  isInitialized: boolean;

  // Actions
  initializeSession: () => Promise<Session>;
  syncSession: () => Promise<void>;
  resolveConflicts: (
    strategy: "ours" | "theirs",
    manualResolutions?: Map<string, string>
  ) => Promise<void>;
  clearSession: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  // Initial state
  currentSession: null,
  syncStatus: "idle",
  syncError: null,
  conflicts: null,
  isInitialized: false,

  /**
   * Initialize or restore session from storage
   */
  initializeSession: async () => {
    try {
      // Try to get existing session
      let session = await getActiveSession();

      if (!session) {
        // Create new session
        session = await createSessionStorage();

        // Only create branch if online
        if (navigator.onLine) {
          try {
            const result = await createSessionBranch(session.id);
          } catch (error) {
            console.warn(
              "Could not create session branch (agent may be offline):",
              error
            );
          }
        }
      }

      set({ currentSession: session, isInitialized: true });
      return session;
    } catch (error) {
      console.error("Failed to initialize session:", error);
      set({ syncError: (error as Error).message });
      throw error;
    }
  },

  /**
   * Sync session (merge branch to main)
   */
  syncSession: async () => {
    const { currentSession } = get();
    if (!currentSession) {
      throw new Error("No active session to sync");
    }

    set({ syncStatus: "syncing", syncError: null });

    try {
      await markSyncing();

      // Attempt to merge session branch
      const result: MergeResult = await mergeSessionBranch(currentSession.id);

      if (result.conflicts && result.conflicts.length > 0) {
        // Conflicts detected
        set({
          syncStatus: "conflicted",
          conflicts: result.conflicts,
        });
        await markConflicted();
      } else {
        // Merge successful
        await markMerged();

        // Clean up session branch
        await deleteSessionBranch(currentSession.id);

        // Clear queued commands and edits
        await clearSessionCommands(currentSession.id);
        await clearSessionEdits(currentSession.id);

        // Clear session from storage
        await clearSessionStorage();

        set({
          syncStatus: "synced",
          currentSession: null,
          conflicts: null,
        });

        // Auto-clear synced status after 3 seconds
        setTimeout(() => {
          if (get().syncStatus === "synced") {
            set({ syncStatus: "idle" });
          }
        }, 3000);
      }
    } catch (error) {
      console.error("Sync failed:", error);
      set({
        syncStatus: "error",
        syncError: (error as Error).message,
      });
    }
  },

  /**
   * Resolve conflicts and complete sync
   */
  resolveConflicts: async (
    strategy: "ours" | "theirs",
    manualResolutions?: Map<string, string>
  ) => {
    const { currentSession } = get();
    if (!currentSession) {
      throw new Error("No active session");
    }

    set({ syncStatus: "syncing", syncError: null });

    try {
      // If manual resolutions provided, apply them first
      if (manualResolutions && manualResolutions.size > 0) {
        // TODO: Send manual resolutions to agent
        // This would require a separate agent command
      }

      // Merge with strategy
      const result = await mergeSessionBranch(currentSession.id, strategy);

      if (result.success) {
        // Clean up
        await deleteSessionBranch(currentSession.id);
        await clearSessionCommands(currentSession.id);
        await clearSessionEdits(currentSession.id);
        await clearSessionStorage();

        set({
          syncStatus: "synced",
          currentSession: null,
          conflicts: null,
        });

        setTimeout(() => {
          if (get().syncStatus === "synced") {
            set({ syncStatus: "idle" });
          }
        }, 3000);
      } else {
        throw new Error(result.message || "Conflict resolution failed");
      }
    } catch (error) {
      console.error("Conflict resolution failed:", error);
      set({
        syncStatus: "error",
        syncError: (error as Error).message,
      });
    }
  },

  /**
   * Clear current session (discard all changes)
   */
  clearSession: async () => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      // Delete session branch
      await deleteSessionBranch(currentSession.id);

      // Clear queued data
      await clearSessionCommands(currentSession.id);
      await clearSessionEdits(currentSession.id);

      // Clear session from storage
      await clearSessionStorage();

      set({
        currentSession: null,
        syncStatus: "idle",
        syncError: null,
        conflicts: null,
      });
    } catch (error) {
      console.error("Failed to clear session:", error);
      set({ syncError: (error as Error).message });
    }
  },

  /**
   * Refresh session from storage
   */
  refreshSession: async () => {
    const session = await getActiveSession();
    set({ currentSession: session });
  },
}));
