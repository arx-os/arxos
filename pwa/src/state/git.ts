import { create } from "zustand";
import { gitStatus, gitDiff, gitCommit } from "../modules/agent/commands/git";
import { useAgentStore } from "../modules/agent/state/agentStore";
import type { GitStatus as AgentGitStatus } from "../modules/agent/client/types";

/**
 * UI-focused Git status type with detailed change tracking
 * This extends the agent's basic GitStatus with additional fields for display
 */
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

function checkAgentConnected(): void {
  const agentState = useAgentStore.getState();
  if (!agentState.isInitialized || agentState.connectionState.status !== "connected") {
    throw new Error("Agent not connected. Please authenticate first.");
  }
}

/**
 * Convert agent's GitStatus response to UI display format
 * Maps the agent's file arrays to change counts for display
 */
function mapAgentStatusToDisplay(agentStatus: AgentGitStatus): GitStatus {
  // Calculate total files changed for diff summary
  const filesChanged = agentStatus.modified.length + agentStatus.added.length + agentStatus.deleted.length;

  return {
    branch: agentStatus.branch,
    last_commit: "HEAD", // Will be fetched separately in future
    last_commit_message: "", // Will be fetched separately in future
    last_commit_time: Date.now() / 1000, // Will be fetched separately in future
    staged_changes: agentStatus.added.length, // Added files are typically staged
    unstaged_changes: agentStatus.modified.length,
    untracked: agentStatus.untracked.length,
    diff_summary: {
      files_changed: filesChanged,
      insertions: 0, // Requires parsing diff output
      deletions: 0, // Requires parsing diff output
    },
  };
}

/**
 * Parse raw git diff output into structured format
 */
function parseDiffString(diffString: string, commit?: string): GitDiff {
  const lines = diffString.split("\n");
  const files: GitDiff["files"] = [];
  let filesChanged = 0;
  let insertions = 0;
  let deletions = 0;
  let currentFile = "";
  let lineNumber = 0;

  for (const line of lines) {
    // Parse file headers (diff --git a/file b/file)
    if (line.startsWith("diff --git")) {
      const match = line.match(/diff --git a\/(.+) b\/(.+)/);
      if (match) {
        currentFile = match[2];
        filesChanged++;
      }
    }

    // Parse hunk headers (@@ -1,5 +1,7 @@)
    if (line.startsWith("@@")) {
      const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/);
      if (match) {
        lineNumber = parseInt(match[2]);
      }
    }

    // Parse diff lines
    if (line.startsWith("+") && !line.startsWith("+++")) {
      insertions++;
      files.push({
        file_path: currentFile,
        line_number: lineNumber,
        kind: "addition",
        content: line.substring(1),
      });
      lineNumber++;
    } else if (line.startsWith("-") && !line.startsWith("---")) {
      deletions++;
      files.push({
        file_path: currentFile,
        line_number: lineNumber,
        kind: "deletion",
        content: line.substring(1),
      });
    } else if (line.startsWith(" ")) {
      files.push({
        file_path: currentFile,
        line_number: lineNumber,
        kind: "context",
        content: line.substring(1),
      });
      lineNumber++;
    }
  }

  return {
    commit_hash: "HEAD",
    compare_hash: commit || "HEAD~1",
    files_changed: filesChanged,
    insertions,
    deletions,
    files,
  };
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
      checkAgentConnected();

      const agentStatus = await gitStatus();
      const displayStatus = mapAgentStatusToDisplay(agentStatus);
      set({ status: displayStatus, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  loadDiff: async (params) => {
    try {
      set({ loading: true, error: undefined });
      checkAgentConnected();

      const diffString = await gitDiff({
        file: params?.file,
        staged: params?.commit === "staged",
      });

      // Parse diff string to extract stats and file changes
      const diff = parseDiffString(diffString, params?.commit);
      set({ diff, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  commit: async (message, stageAll = false) => {
    try {
      set({ loading: true, error: undefined });
      checkAgentConnected();

      const response = await gitCommit({
        message,
        files: stageAll ? undefined : [],
      });

      await useGitStore.getState().refreshStatus();
      return {
        commit_id: response.hash,
        staged_files: response.filesChanged,
      };
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  readFile: async (path) => {
    try {
      set({ loading: true, error: undefined });
      checkAgentConnected();

      const agentStore = useAgentStore.getState();
      const response = await agentStore.send<FileContent>("files.read", { path });

      set({ file: response, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  clearError: () => set({ error: undefined }),
}));
