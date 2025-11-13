import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";

// Mock the agent commands
vi.mock("../modules/agent/commands/git", () => ({
  gitStatus: vi.fn(),
  gitDiff: vi.fn(),
  gitCommit: vi.fn(),
}));

// Mock the agent store
vi.mock("../modules/agent/state/agentStore", () => ({
  useAgentStore: {
    getState: () => ({
      isInitialized: true,
      connectionState: { status: "connected" },
    }),
  },
}));

import { gitStatus } from "../modules/agent/commands/git";
import { useGitStore } from "../state/git";

describe("git store", () => {
  afterEach(() => {
    useGitStore.setState({
      status: undefined,
      diff: undefined,
      file: undefined,
      loading: false,
      error: undefined
    });
    vi.resetAllMocks();
  });

  it("hydrates status from agent", async () => {
    vi.mocked(gitStatus).mockResolvedValue({
      branch: "main",
      last_commit: "abc",
      last_commit_message: "Init",
      last_commit_time: 1,
      staged_changes: 0,
      unstaged_changes: 1,
      untracked: 2,
      diff_summary: {
        files_changed: 1,
        insertions: 3,
        deletions: 0,
      },
    } as any);

    await act(async () => {
      await useGitStore.getState().refreshStatus();
    });

    expect(useGitStore.getState().status?.branch).toBe("main");
  });

  it("records error when agent fails", async () => {
    vi.mocked(gitStatus).mockRejectedValue(new Error("boom"));

    await act(async () => {
      await useGitStore.getState().refreshStatus();
    });

    expect(useGitStore.getState().error).toContain("boom");
  });
});
