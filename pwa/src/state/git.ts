import { create } from "zustand";
import { invokeAgent } from "../lib/agent";
import { useCollaborationStore } from "./collaboration";

export type GitStatus = {
  branch: string;
  last_commit: string;
  last_commit_message: string;
  last_commit_time: number;
  staged_changes: number;
  unstaged_changes: number;
  untracked: number;
  diff_summary: {
    files_changed: number;
    insertions: number;
    deletions: number;
  };
};

export type GitDiff = {
  commit_hash: string;
  compare_hash: string;
  files_changed: number;
  insertions: number;
  deletions: number;
  files: Array<{
    file_path: string;
    line_number: number;
    kind: string;
    content: string;
  }>;
};

export type GitCommitResult = {
  commit_id: string;
  staged_files: number;
};

export type FileContent = {
  path: string;
  content: string;
};

type GitStore = {
  status?: GitStatus;
  diff?: GitDiff;
  file?: FileContent;
  loading: boolean;
  error?: string;
  refreshStatus: () => Promise<void>;
  loadDiff: (params?: { commit?: string; file?: string }) => Promise<void>;
  commit: (message: string, stageAll?: boolean) => Promise<GitCommitResult | undefined>;
  readFile: (path: string) => Promise<void>;
  clearError: () => void;
};

function getAgentToken(): string {
  const token = useCollaborationStore.getState().token;
  if (!token.startsWith("did:key:")) {
    throw new Error("Agent token missing or invalid");
  }
  return token;
}

export const useGitStore = create<GitStore>((set) => ({
  status: undefined,
  diff: undefined,
  file: undefined,
  loading: false,
  error: undefined,
  refreshStatus: async () => {
    try {
      set({ loading: true, error: undefined });
      const token = getAgentToken();
      const response = await invokeAgent<GitStatus>(token, "git.status");
      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }
      set({ status: response.payload, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  loadDiff: async (params) => {
    try {
      set({ loading: true, error: undefined });
      const token = getAgentToken();
      const response = await invokeAgent<GitDiff>(token, "git.diff", {
        commit: params?.commit,
        file: params?.file
      });
      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }
      set({ diff: response.payload, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  commit: async (message, stageAll = false) => {
    try {
      set({ loading: true, error: undefined });
      const token = getAgentToken();
      const response = await invokeAgent<GitCommitResult>(token, "git.commit", {
        message,
        stage_all: stageAll
      });
      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }
      await useGitStore.getState().refreshStatus();
      return response.payload;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  readFile: async (path) => {
    try {
      set({ loading: true, error: undefined });
      const token = getAgentToken();
      const response = await invokeAgent<FileContent>(token, "files.read", { path });
      if (response.status !== "ok") {
        throw new Error(
          typeof response.payload === "object" && response.payload !== null
            ? (response.payload as Record<string, unknown>).error?.toString() ?? "Agent error"
            : "Agent error"
        );
      }
      set({ file: response.payload, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  clearError: () => set({ error: undefined }),
}));
