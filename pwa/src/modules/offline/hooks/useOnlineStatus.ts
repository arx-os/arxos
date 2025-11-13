/**
 * Online/Offline status detection hook
 *
 * Combines browser online status with agent connection state
 * to provide accurate connectivity information.
 */

import { useState, useEffect } from "react";
import { useAgentStore } from "../../agent/state/agentStore";

export interface OnlineStatus {
  /** True if browser reports online AND agent is connected */
  isOnline: boolean;
  /** Browser's navigator.onLine status */
  browserOnline: boolean;
  /** Agent connection status */
  agentConnected: boolean;
  /** Last time we were fully online */
  lastOnline: Date | null;
}

/**
 * Hook to track online/offline status
 *
 * Considers the app "online" only when:
 * 1. Browser reports online (navigator.onLine)
 * 2. Agent WebSocket is connected
 */
export function useOnlineStatus(): OnlineStatus {
  const [browserOnline, setBrowserOnline] = useState(navigator.onLine);
  const [lastOnline, setLastOnline] = useState<Date | null>(
    navigator.onLine ? new Date() : null
  );

  const { connectionState } = useAgentStore();
  const agentConnected = connectionState?.status === "connected";

  // Listen to browser online/offline events
  useEffect(() => {
    const handleOnline = () => {
      setBrowserOnline(true);
      console.log("Browser online event detected");
    };

    const handleOffline = () => {
      setBrowserOnline(false);
      console.log("Browser offline event detected");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Track last online time
  useEffect(() => {
    if (browserOnline && agentConnected) {
      setLastOnline(new Date());
    }
  }, [browserOnline, agentConnected]);

  const isOnline = browserOnline && agentConnected;

  return {
    isOnline,
    browserOnline,
    agentConnected,
    lastOnline,
  };
}

/**
 * Hook that triggers a callback on online/offline transitions
 */
export function useOnlineStatusChange(
  onOnline?: () => void,
  onOffline?: () => void
) {
  const { isOnline } = useOnlineStatus();
  const [previousStatus, setPreviousStatus] = useState(isOnline);

  useEffect(() => {
    if (isOnline !== previousStatus) {
      if (isOnline && onOnline) {
        console.log("Transitioned to online");
        onOnline();
      } else if (!isOnline && onOffline) {
        console.log("Transitioned to offline");
        onOffline();
      }
      setPreviousStatus(isOnline);
    }
  }, [isOnline, previousStatus, onOnline, onOffline]);
}
