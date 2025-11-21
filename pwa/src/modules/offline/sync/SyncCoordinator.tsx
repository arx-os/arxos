/**
 * Sync Coordinator
 *
 * Orchestrates offline/online transitions and automatic syncing.
 * This component should be mounted at the app root level.
 */

import { useEffect, useRef } from "react";
import { useOnlineStatusChange } from "../hooks/useOnlineStatus";
import { useSessionStore } from "../state/sessionStore";
import { getQueueManager } from "./CommandQueueManager";

export function SyncCoordinator() {
  const { initializeSession, syncSession, currentSession, syncStatus } =
    useSessionStore();
  const hasInitialized = useRef(false);
  const syncInProgress = useRef(false);

  // Initialize session on mount
  useEffect(() => {
    if (!hasInitialized.current) {
      initializeSession().catch((error) => {
        console.error("Failed to initialize session:", error);
      });
      hasInitialized.current = true;
    }
  }, [initializeSession]);

  // Handle online/offline transitions
  useOnlineStatusChange(
    // On transition to online
    async () => {

      if (syncInProgress.current) {
        return;
      }

      if (!currentSession) {
        return;
      }

      try {
        syncInProgress.current = true;

        // First, process queued commands
        const queueManager = getQueueManager();
        const queueResult = await queueManager.processQueue();


        // If queue had errors, don't attempt session sync yet
        if (queueResult.failed > 0) {
          console.warn(
            `SyncCoordinator: ${queueResult.failed} commands failed, skipping session sync`
          );
          return;
        }

        // Then sync the session (merge branch)
        if (currentSession.commandCount > 0) {
          await syncSession();
        } else {
        }
      } catch (error) {
        console.error("SyncCoordinator: Sync failed", error);
      } finally {
        syncInProgress.current = false;
      }
    },
    // On transition to offline
    () => {
      // Nothing to do on offline transition
      // Commands will automatically queue
    }
  );

  // Log sync status changes
  useEffect(() => {
  }, [syncStatus]);

  // This component doesn't render anything
  return null;
}
