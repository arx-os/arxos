/**
 * Authentication modal for DID:key token input
 */

import { useState } from "react";
import { AlertCircle, CheckCircle, Loader2, Key, ExternalLink } from "lucide-react";
import { useAuthStore } from "../state";
import { useAgentStore } from "../state";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [token, setToken] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const authStore = useAuthStore();
  const agentStore = useAgentStore();

  const handleConnect = async () => {
    setError(null);
    setSuccess(false);

    // Validate token format
    const isValid = authStore.validateToken(token);
    if (!isValid) {
      setError("Invalid DID:key format. Must start with 'did:key:z'");
      return;
    }

    setIsConnecting(true);

    try {
      // Store token
      authStore.setToken(token);

      // Initialize agent client
      await agentStore.initialize(token);

      // Test connection
      await agentStore.send("ping");

      setSuccess(true);
      setError(null);

      // Close modal after short delay
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect to agent. Make sure the agent is running."
      );
      setSuccess(false);
      authStore.clearToken();
    } finally {
      setIsConnecting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && token && !isConnecting) {
      handleConnect();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-2xl w-full max-w-md p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-cyan-600/20 rounded-lg">
            <Key size={24} className="text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-100">
              Connect to ArxOS Agent
            </h2>
            <p className="text-sm text-slate-400">
              Enter your DID:key token to authenticate
            </p>
          </div>
        </div>

        {/* Info box */}
        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 mb-4">
          <p className="text-sm text-slate-300 mb-2">
            The ArxOS desktop agent must be running to use editing features.
          </p>
          <a
            href="https://github.com/joelpate/arxos#agent-setup"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            Setup instructions
            <ExternalLink size={14} />
          </a>
        </div>

        {/* Token input */}
        <div className="mb-4">
          <label htmlFor="token" className="block text-sm font-medium text-slate-300 mb-2">
            DID:key Token
          </label>
          <input
            id="token"
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="did:key:z6Mk..."
            disabled={isConnecting || success}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed font-mono text-sm"
          />
          <p className="text-xs text-slate-400 mt-1">
            Example: did:key:z6MkTestToken123456789
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-3 mb-4 flex items-start gap-2">
            <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-300">Connection failed</p>
              <p className="text-xs text-red-400 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Success message */}
        {success && (
          <div className="bg-green-900/20 border border-green-700 rounded-lg p-3 mb-4 flex items-center gap-2">
            <CheckCircle size={18} className="text-green-400" />
            <p className="text-sm text-green-300">Connected successfully!</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isConnecting}
            className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={!token || isConnecting || success}
            className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isConnecting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Connecting...
              </>
            ) : success ? (
              "Connected"
            ) : (
              "Connect"
            )}
          </button>
        </div>

        {/* Helper text */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-xs text-slate-400">
            Token is stored in session storage and cleared when you close the browser.
          </p>
        </div>
      </div>
    </div>
  );
}
