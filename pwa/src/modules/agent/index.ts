// Client exports
export { AgentClient } from "./client";
export type { AgentClientConfig } from "./client";

// State exports
export { useAgentStore, useAuthStore } from "./state";

// Component exports
export { AuthModal, ConnectionIndicator } from "./components";

// Type exports
export type {
  AgentAction,
  AgentConnectionState,
  AgentCapabilities,
  GitStatus,
  GitCommitOptions,
  GitCommitResult,
  ValidationResult,
  ValidationError,
  ValidationWarning,
  EditOperation,
  ApplyEditsRequest,
  ApplyEditsResult,
  ConnectionStatus,
  ConnectionQuality,
} from "./client/types";
