/**
 * Connection status indicator
 */

import { useState } from "react";
import { Wifi, WifiOff, AlertTriangle, Loader2, Info } from "lucide-react";
import { useAgentStore } from "../state";

export function ConnectionIndicator() {
  const [showDetails, setShowDetails] = useState(false);
  const { connectionState } = useAgentStore();

  const getStatusColor = () => {
    switch (connectionState.status) {
      case "connected":
        return connectionState.quality === "excellent"
          ? "text-green-400"
          : connectionState.quality === "good"
          ? "text-yellow-400"
          : "text-orange-400";
      case "connecting":
      case "reconnecting":
        return "text-blue-400";
      case "error":
        return "text-red-400";
      case "disconnected":
      default:
        return "text-slate-500";
    }
  };

  const getStatusIcon = () => {
    switch (connectionState.status) {
      case "connected":
        return <Wifi size={18} className={getStatusColor()} />;
      case "connecting":
      case "reconnecting":
        return <Loader2 size={18} className={`${getStatusColor()} animate-spin`} />;
      case "error":
        return <AlertTriangle size={18} className={getStatusColor()} />;
      case "disconnected":
      default:
        return <WifiOff size={18} className={getStatusColor()} />;
    }
  };

  const getStatusText = () => {
    switch (connectionState.status) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return `Reconnecting (${connectionState.reconnectAttempts})`;
      case "error":
        return "Error";
      case "disconnected":
      default:
        return "Disconnected";
    }
  };

  const getQualityText = () => {
    if (connectionState.status !== "connected") return null;

    switch (connectionState.quality) {
      case "excellent":
        return "Excellent";
      case "good":
        return "Good";
      case "poor":
        return "Poor";
      default:
        return null;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-750 transition-colors"
        title="Agent connection status"
      >
        {getStatusIcon()}
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </button>

      {/* Details dropdown */}
      {showDetails && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowDetails(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-80 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Info size={16} className="text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-200">
                  Connection Details
                </h3>
              </div>
              <button
                onClick={() => setShowDetails(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ×
              </button>
            </div>

            <div className="space-y-3">
              {/* Status */}
              <div>
                <label className="text-xs text-slate-400">Status</label>
                <div className={`text-sm font-medium ${getStatusColor()}`}>
                  {getStatusText()}
                </div>
              </div>

              {/* Quality */}
              {connectionState.status === "connected" && (
                <div>
                  <label className="text-xs text-slate-400">Quality</label>
                  <div className={`text-sm ${getStatusColor()}`}>
                    {getQualityText()}
                    {connectionState.latency !== undefined &&
                      ` (${connectionState.latency}ms)`}
                  </div>
                </div>
              )}

              {/* Last connected */}
              {connectionState.lastConnected && (
                <div>
                  <label className="text-xs text-slate-400">Last Connected</label>
                  <div className="text-sm text-slate-300">
                    {connectionState.lastConnected.toLocaleTimeString()}
                  </div>
                </div>
              )}

              {/* Reconnect attempts */}
              {connectionState.reconnectAttempts > 0 && (
                <div>
                  <label className="text-xs text-slate-400">Reconnect Attempts</label>
                  <div className="text-sm text-slate-300">
                    {connectionState.reconnectAttempts}
                  </div>
                </div>
              )}

              {/* Error */}
              {connectionState.lastError && (
                <div>
                  <label className="text-xs text-slate-400">Last Error</label>
                  <div className="text-sm text-red-400">
                    {connectionState.lastError}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="pt-3 border-t border-slate-700 flex gap-2">
                {connectionState.status === "disconnected" ||
                connectionState.status === "error" ? (
                  <button
                    onClick={() => {
                      useAgentStore.getState().connect();
                      setShowDetails(false);
                    }}
                    className="flex-1 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded transition-colors"
                  >
                    Reconnect
                  </button>
                ) : connectionState.status === "connected" ? (
                  <button
                    onClick={() => {
                      useAgentStore.getState().disconnect();
                      setShowDetails(false);
                    }}
                    className="flex-1 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded transition-colors"
                  >
                    Disconnect
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
