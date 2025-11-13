/**
 * Online status hook tests
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useOnlineStatus } from "../../modules/offline/hooks/useOnlineStatus";
import { useAgentStore } from "../../modules/agent/state/agentStore";

// Mock agent store
vi.mock("../../modules/agent/state/agentStore", () => ({
  useAgentStore: vi.fn(() => ({
    connectionState: { status: "connected" },
  })),
}));

describe("useOnlineStatus hook", () => {
  beforeEach(() => {
    // Reset navigator.onLine mock
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: true,
    });

    // Reset agent store mock
    vi.mocked(useAgentStore).mockReturnValue({
      connectionState: { status: "connected" },
    } as any);
  });

  it("should return online when both browser and agent are connected", () => {
    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(true);
    expect(result.current.browserOnline).toBe(true);
    expect(result.current.agentConnected).toBe(true);
  });

  it("should return offline when browser is offline", () => {
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.browserOnline).toBe(false);
    expect(result.current.agentConnected).toBe(true);
  });

  it("should return offline when agent is disconnected", () => {
    vi.mocked(useAgentStore).mockReturnValue({
      connectionState: { status: "disconnected" },
    } as any);

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.browserOnline).toBe(true);
    expect(result.current.agentConnected).toBe(false);
  });

  it("should return offline when both are disconnected", () => {
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: false,
    });

    vi.mocked(useAgentStore).mockReturnValue({
      connectionState: { status: "disconnected" },
    } as any);

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.browserOnline).toBe(false);
    expect(result.current.agentConnected).toBe(false);
  });

  it("should handle agent connecting state as offline", () => {
    vi.mocked(useAgentStore).mockReturnValue({
      connectionState: { status: "connecting" },
    } as any);

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.agentConnected).toBe(false);
  });

  it("should handle agent reconnecting state as offline", () => {
    vi.mocked(useAgentStore).mockReturnValue({
      connectionState: { status: "reconnecting" },
    } as any);

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);
    expect(result.current.agentConnected).toBe(false);
  });

  it("should respond to online events", async () => {
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(false);

    // Simulate going online
    act(() => {
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        value: true,
      });
      window.dispatchEvent(new Event("online"));
    });

    await waitFor(() => {
      expect(result.current.browserOnline).toBe(true);
    });
  });

  it("should respond to offline events", async () => {
    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current.isOnline).toBe(true);

    // Simulate going offline
    act(() => {
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        value: false,
      });
      window.dispatchEvent(new Event("offline"));
    });

    await waitFor(() => {
      expect(result.current.browserOnline).toBe(false);
    });
  });

  it("should track last online timestamp", async () => {
    const { result } = renderHook(() => useOnlineStatus());

    const initialLastOnline = result.current.lastOnline;
    expect(initialLastOnline).toBeDefined();

    // Wait a bit
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Go offline then online
    act(() => {
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        value: false,
      });
      window.dispatchEvent(new Event("offline"));
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    act(() => {
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        value: true,
      });
      window.dispatchEvent(new Event("online"));
    });

    await waitFor(() => {
      expect(result.current.lastOnline).not.toBe(initialLastOnline);
    });
  });
});
