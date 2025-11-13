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
      console.log("SyncCoordinator: Initializing session");
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
      console.log("SyncCoordinator: Device came online");

      if (syncInProgress.current) {
        console.log("SyncCoordinator: Sync already in progress, skipping");
        return;
      }

      if (!currentSession) {
        console.log("SyncCoordinator: No active session to sync");
        return;
      }

      try {
        syncInProgress.current = true;

        // First, process queued commands
        console.log("SyncCoordinator: Processing command queue");
        const queueManager = getQueueManager();
        const queueResult = await queueManager.processQueue();

        console.log("SyncCoordinator: Queue processed", queueResult);

        // If queue had errors, don't attempt session sync yet
        if (queueResult.failed > 0) {
          console.warn(
            `SyncCoordinator: ${queueResult.failed} commands failed, skipping session sync`
          );
          return;
        }

        // Then sync the session (merge branch)
        if (currentSession.commandCount > 0) {
          console.log("SyncCoordinator: Syncing session");
          await syncSession();
        } else {
          console.log("SyncCoordinator: No commands to sync");
        }
      } catch (error) {
        console.error("SyncCoordinator: Sync failed", error);
      } finally {
        syncInProgress.current = false;
      }
    },
    // On transition to offline
    () => {
      console.log("SyncCoordinator: Device went offline");
      // Nothing to do on offline transition
      // Commands will automatically queue
    }
  );

  // Log sync status changes
  useEffect(() => {
    console.log("SyncCoordinator: Sync status changed:", syncStatus);
  }, [syncStatus]);

  // This component doesn't render anything
  return null;
}
