/**
 * Sync Status Toast
 *
 * Shows sync progress and completion status.
 */

import { useEffect, useState } from "react";
import { useSessionStore } from "../state/sessionStore";
import { CheckCircle, AlertCircle, Loader2, XCircle } from "lucide-react";

export function SyncStatusToast() {
  const { syncStatus, syncError } = useSessionStore();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Show toast when sync status changes
    if (syncStatus !== "idle") {
      setIsVisible(true);
    }

    // Auto-hide after sync completes
    if (syncStatus === "synced") {
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 3000);
      return () => clearTimeout(timer);
    }

    // Keep visible for error and conflicted states
    if (syncStatus === "error" || syncStatus === "conflicted") {
      setIsVisible(true);
    }
  }, [syncStatus]);

  if (!isVisible) {
    return null;
  }

  const getStatusContent = () => {
    switch (syncStatus) {
      case "syncing":
        return {
          icon: <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />,
          title: "Syncing...",
          message: "Uploading offline changes",
          bgColor: "bg-blue-500/10 border-blue-500/50",
          textColor: "text-blue-400",
        };

      case "synced":
        return {
          icon: <CheckCircle className="h-5 w-5 text-emerald-500" />,
          title: "Synced",
          message: "All changes uploaded successfully",
          bgColor: "bg-emerald-500/10 border-emerald-500/50",
          textColor: "text-emerald-400",
        };

      case "conflicted":
        return {
          icon: <AlertCircle className="h-5 w-5 text-amber-500" />,
          title: "Conflicts Detected",
          message: "Please resolve conflicts to continue",
          bgColor: "bg-amber-500/10 border-amber-500/50",
          textColor: "text-amber-400",
        };

      case "error":
        return {
          icon: <XCircle className="h-5 w-5 text-red-500" />,
          title: "Sync Failed",
          message: syncError || "An error occurred during sync",
          bgColor: "bg-red-500/10 border-red-500/50",
          textColor: "text-red-400",
        };

      default:
        return null;
    }
  };

  const content = getStatusContent();
  if (!content) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm animate-in slide-in-from-top-5">
      <div
        className={`rounded-lg border ${content.bgColor} backdrop-blur-sm p-4 shadow-lg`}
      >
        <div className="flex items-start gap-3">
          {content.icon}
          <div className="flex-1 min-w-0">
            <div className={`font-semibold ${content.textColor}`}>
              {content.title}
            </div>
            <div className="mt-1 text-sm text-slate-300">{content.message}</div>
          </div>
          {syncStatus !== "syncing" && (
            <button
              onClick={() => setIsVisible(false)}
              className="text-slate-400 hover:text-slate-200"
              aria-label="Close"
            >
              <XCircle className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
