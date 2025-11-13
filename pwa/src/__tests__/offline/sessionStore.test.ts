/**
 * Session store tests - Zustand state management for offline sessions
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useSessionStore } from "../../modules/offline/state/sessionStore";
import { clearStorage } from "../../lib/storage/db";

// Mock agent commands
vi.mock("../../modules/agent/commands/session", () => ({
  createSessionBranch: vi.fn().mockResolvedValue({ success: true }),
  mergeSessionBranch: vi.fn().mockResolvedValue({
    success: true,
    conflicts: [],
    commitHash: "abc123",
  }),
  deleteSessionBranch: vi.fn().mockResolvedValue({ success: true }),
}));

describe("Session Store", () => {
  beforeEach(async () => {
    await clearStorage();
    // Reset store state
    const { result } = renderHook(() => useSessionStore());
    act(() => {
      result.current.currentSession = null;
      result.current.syncStatus = "idle";
      result.current.conflicts = [];
      result.current.syncError = null;
      result.current.isInitialized = false;
    });
  });

  it("should initialize with default state", () => {
    const { result } = renderHook(() => useSessionStore());

    expect(result.current.currentSession).toBeNull();
    expect(result.current.syncStatus).toBe("idle");
    expect(result.current.conflicts).toEqual([]);
    expect(result.current.syncError).toBeNull();
    expect(result.current.isInitialized).toBe(false);
  });

  it("should initialize a new session", async () => {
    const { result } = renderHook(() => useSessionStore());

    await act(async () => {
      await result.current.initializeSession();
    });

    await waitFor(() => {
      expect(result.current.currentSession).toBeDefined();
      expect(result.current.currentSession?.status).toBe("active");
      expect(result.current.isInitialized).toBe(true);
    });
  });

  it("should reuse existing active session", async () => {
    const { result } = renderHook(() => useSessionStore());

    // Initialize first time
    await act(async () => {
      await result.current.initializeSession();
    });

    const firstSessionId = result.current.currentSession?.id;

    // Initialize again
    await act(async () => {
      await result.current.initializeSession();
    });

    expect(result.current.currentSession?.id).toBe(firstSessionId);
  });

  it("should clear session", async () => {
    const { result } = renderHook(() => useSessionStore());

    await act(async () => {
      await result.current.initializeSession();
    });

    expect(result.current.currentSession).toBeDefined();

    await act(async () => {
      await result.current.clearSession();
    });

    await waitFor(() => {
      expect(result.current.currentSession).toBeNull();
    });
  });

  it("should update sync status", () => {
    const { result } = renderHook(() => useSessionStore());

    act(() => {
      result.current.syncStatus = "syncing";
    });

    expect(result.current.syncStatus).toBe("syncing");

    act(() => {
      result.current.syncStatus = "synced";
    });

    expect(result.current.syncStatus).toBe("synced");
  });

  it("should handle sync errors", async () => {
    const { result } = renderHook(() => useSessionStore());

    await act(async () => {
      await result.current.initializeSession();
    });

    act(() => {
      result.current.syncStatus = "error";
      result.current.syncError = "Network error";
    });

    expect(result.current.syncStatus).toBe("error");
    expect(result.current.syncError).toBe("Network error");
  });

  it("should store conflicts", () => {
    const { result } = renderHook(() => useSessionStore());

    const mockConflicts = [
      {
        filePath: "file1.txt",
        base: "base content",
        theirs: "their content",
        mine: "my content",
      },
    ];

    act(() => {
      result.current.conflicts = mockConflicts;
      result.current.syncStatus = "conflicted";
    });

    expect(result.current.conflicts).toEqual(mockConflicts);
    expect(result.current.syncStatus).toBe("conflicted");
  });

  it("should track initialization state", async () => {
    const { result } = renderHook(() => useSessionStore());

    expect(result.current.isInitialized).toBe(false);

    await act(async () => {
      await result.current.initializeSession();
    });

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(true);
    });
  });
});
