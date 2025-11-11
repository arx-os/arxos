import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";

vi.mock("../lib/agent", () => ({
  invokeAgent: vi.fn()
}));

vi.mock("../state/collaboration", () => ({
  useCollaborationStore: {
    getState: () => ({
      token: "did:key:test",
      agentStatus: "connected"
    })
  }
}));

import { invokeAgent } from "../lib/agent";
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
    vi.mocked(invokeAgent).mockResolvedValue({
      status: "ok",
      payload: {
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
          deletions: 0
        }
      }
    });

    await act(async () => {
      await useGitStore.getState().refreshStatus();
    });

    expect(useGitStore.getState().status?.branch).toBe("main");
  });

  it("records error when agent fails", async () => {
    vi.mocked(invokeAgent).mockResolvedValue({
      status: "error",
      payload: { error: "boom" }
    });

    await act(async () => {
      await useGitStore.getState().refreshStatus();
    });

    expect(useGitStore.getState().error).toContain("boom");
  });
});
