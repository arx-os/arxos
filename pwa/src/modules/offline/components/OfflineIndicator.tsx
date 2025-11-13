/**
 * Offline Indicator
 *
 * Shows when the app is offline and displays pending sync count.
 */

import { useEffect, useState } from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { getPendingCount } from "../../../lib/storage/commandQueue";
import { WifiOff, RefreshCw } from "lucide-react";
import { getQueueManager } from "../sync/CommandQueueManager";

export function OfflineIndicator() {
  const { isOnline, browserOnline, agentConnected } = useOnlineStatus();
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  // Update pending count periodically
  useEffect(() => {
    const updateCount = async () => {
      const count = await getPendingCount();
      setPendingCount(count);
    };

    updateCount();
    const interval = setInterval(updateCount, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleManualSync = async () => {
    if (!isOnline) {
      alert("Cannot sync while offline");
      return;
    }

    setIsSyncing(true);
    try {
      const queueManager = getQueueManager();
      await queueManager.processQueue();
    } catch (error) {
      console.error("Manual sync failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  // Don't show if online
  if (isOnline) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 max-w-sm">
      <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 backdrop-blur-sm p-4 shadow-lg">
        <div className="flex items-start gap-3">
          <WifiOff className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-amber-400">Working Offline</div>
            <div className="mt-1 text-sm text-amber-300/80">
              {!browserOnline && "No internet connection"}
              {browserOnline && !agentConnected && "Agent not connected"}
            </div>
            {pendingCount > 0 && (
              <div className="mt-2 text-sm text-amber-200">
                {pendingCount} change{pendingCount > 1 ? "s" : ""} pending sync
              </div>
            )}
          </div>
          {pendingCount > 0 && isOnline && (
            <button
              onClick={handleManualSync}
              disabled={isSyncing}
              className="rounded-md bg-amber-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
              aria-label="Sync now"
            >
              {isSyncing ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                "Sync"
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
