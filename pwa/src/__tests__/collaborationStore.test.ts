import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useCollaborationStore } from "../state/collaboration";
import { invokeAgent } from "../lib/agent";
import type { CollabSyncResponse } from "../lib/agent";

vi.mock("../lib/agent", () => ({
  invokeAgent: vi.fn()
}));

const mockedInvokeAgent = vi.mocked(invokeAgent);

const resetStore = () => {
  useCollaborationStore.setState({
    online: true,
    messages: [],
    queue: [],
    token: "did:key:zexample",
    agentStatus: "idle",
    lastSync: undefined,
    syncTarget: undefined,
    isSyncing: false
  });
};

beforeEach(() => {
  mockedInvokeAgent.mockReset();
  resetStore();
  localStorage.clear();
});

afterEach(() => {
  mockedInvokeAgent.mockReset();
  resetStore();
  localStorage.clear();
});

describe("collaboration store", () => {
  it("queues messages and flushes through the agent", async () => {
    const successPayload: CollabSyncResponse = {
      successes: [
        {
          id: "abc123",
          remoteId: 99,
          remoteUrl: "https://github.com/arx-os/arxos/issues/99#comment-1",
          syncedAt: new Date().toISOString()
        }
      ],
      errors: []
    };

    mockedInvokeAgent
      .mockResolvedValueOnce({
        status: "ok",
        payload: {
          config: {
            owner: "arx-os",
            repo: "arxos",
            target: { type: "issue", number: 99 }
          }
        }
      })
      .mockResolvedValueOnce({ status: "ok", payload: successPayload });

    useCollaborationStore.getState().enqueue({
      buildingId: "demo",
      author: "user",
      content: "message"
    });

    // Force deterministic id for assertion
    const queuedId = useCollaborationStore.getState().queue[0].id;
    successPayload.successes[0].id = queuedId;

    await useCollaborationStore.getState().hydrate();
    await new Promise((resolve) => setTimeout(resolve, 0));

    const state = useCollaborationStore.getState();
    expect(mockedInvokeAgent).toHaveBeenNthCalledWith(1, "did:key:zexample", "collab.config.get");
    expect(mockedInvokeAgent).toHaveBeenNthCalledWith(2, "did:key:zexample", "collab.sync", {
      messages: [
        expect.objectContaining({ id: queuedId, content: "message" })
      ]
    });
    expect(state.queue).toHaveLength(0);
    expect(state.messages[0]?.status).toBe("sent");
    expect(state.messages[0]?.remoteUrl).toContain("github.com");
    expect(state.agentStatus).toBe("connected");
    expect(state.lastSync).toBeTypeOf("number");
  });

  it("retains queue when offline", async () => {
    mockedInvokeAgent.mockRejectedValue(new Error("offline"));

    useCollaborationStore.setState((state) => ({ ...state, online: false }));
    useCollaborationStore.getState().enqueue({
      buildingId: "demo",
      author: "user",
      content: "message"
    });

    await useCollaborationStore.getState().hydrate();
    await new Promise((resolve) => setTimeout(resolve, 0));

    const offlineState = useCollaborationStore.getState();
    expect(offlineState.queue).toHaveLength(1);
    expect(offlineState.agentStatus).toBe("idle");
    expect(offlineState.lastSync).toBeUndefined();
  });

  it("marks errors and supports retry", async () => {
    mockedInvokeAgent.mockResolvedValueOnce({
      status: "ok",
      payload: {
        config: {
          owner: "arx-os",
          repo: "arxos",
          target: { type: "issue", number: 5 }
        }
      }
    });
    useCollaborationStore.getState().enqueue({
      buildingId: "demo",
      author: "user",
      content: "message"
    });

    const pendingId = useCollaborationStore.getState().queue[0].id;
    mockedInvokeAgent.mockResolvedValueOnce({
      status: "ok",
      payload: {
        successes: [],
        errors: [{ id: pendingId, error: "Forbidden" }]
      }
    }).mockResolvedValueOnce({ status: "error", payload: { error: "still failing" } });

    await useCollaborationStore.getState().hydrate();
    await new Promise((resolve) => setTimeout(resolve, 0));

    const stateAfterError = useCollaborationStore.getState();
    expect(stateAfterError.queue).toHaveLength(0);
    expect(stateAfterError.messages[0]?.status).toBe("error");
    expect(stateAfterError.messages[0]?.errorReason).toContain("Forbidden");

    stateAfterError.retryMessage(pendingId);
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(useCollaborationStore.getState().queue).toHaveLength(1);
    expect(useCollaborationStore.getState().messages[0]?.status).toBe("pending");
  });
});
