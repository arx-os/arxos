/**
 * GitStatusPanel component tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { GitStatusPanel } from "../GitStatusPanel";
import { useGitStore } from "../../../../state/git";
import { act } from "react";

// Mock the git store
vi.mock("../../../../state/git", () => ({
  useGitStore: vi.fn(),
}));

describe("GitStatusPanel", () => {
  const mockRefreshStatus = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should show loading state initially", () => {
    vi.mocked(useGitStore).mockReturnValue({
      status: undefined,
      loading: true,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    expect(screen.getByText("Loading status...")).toBeInTheDocument();
  });

  it("should display error message", () => {
    vi.mocked(useGitStore).mockReturnValue({
      status: undefined,
      loading: false,
      error: "Failed to connect",
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    expect(screen.getByText("Error Loading Status")).toBeInTheDocument();
    expect(screen.getByText("Failed to connect")).toBeInTheDocument();
  });

  it("should display repository status", async () => {
    const mockStatus = {
      branch: "main",
      last_commit: "abc123def456",
      last_commit_message: "Initial commit",
      last_commit_time: Date.now() / 1000,
      staged_changes: 2,
      unstaged_changes: 3,
      untracked: 1,
      diff_summary: {
        files_changed: 5,
        insertions: 10,
        deletions: 3,
      },
    };

    vi.mocked(useGitStore).mockReturnValue({
      status: mockStatus,
      loading: false,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText("main")).toBeInTheDocument();
      expect(screen.getByText("Initial commit")).toBeInTheDocument();
      expect(screen.getByText("abc123de")).toBeInTheDocument(); // First 8 chars
    });
  });

  it("should display change counts correctly", async () => {
    const mockStatus = {
      branch: "feature",
      last_commit: "xyz",
      last_commit_message: "Add feature",
      last_commit_time: Date.now() / 1000,
      staged_changes: 5,
      unstaged_changes: 3,
      untracked: 2,
      diff_summary: {
        files_changed: 10,
        insertions: 20,
        deletions: 5,
      },
    };

    vi.mocked(useGitStore).mockReturnValue({
      status: mockStatus,
      loading: false,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    await waitFor(() => {
      // Check that the change section labels are present
      expect(screen.getByText("Staged")).toBeInTheDocument();
      expect(screen.getByText("Unstaged")).toBeInTheDocument();
      expect(screen.getByText("Untracked")).toBeInTheDocument();
      expect(screen.getByText("Total Changes")).toBeInTheDocument();

      // Total should be 5 + 3 + 2 = 10
      const numbers = screen.getAllByText("10");
      expect(numbers.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("should display diff summary", async () => {
    const mockStatus = {
      branch: "main",
      last_commit: "abc",
      last_commit_message: "Test",
      last_commit_time: Date.now() / 1000,
      staged_changes: 0,
      unstaged_changes: 0,
      untracked: 0,
      diff_summary: {
        files_changed: 3,
        insertions: 15,
        deletions: 7,
      },
    };

    vi.mocked(useGitStore).mockReturnValue({
      status: mockStatus,
      loading: false,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    await waitFor(() => {
      expect(screen.getByText("Diff Summary")).toBeInTheDocument();

      // Files changed = 3
      const filesLabels = screen.getAllByText("Files");
      expect(filesLabels.length).toBeGreaterThanOrEqual(1);

      // Insertions and deletions
      expect(screen.getByText("+15")).toBeInTheDocument(); // Insertions
      expect(screen.getByText("-7")).toBeInTheDocument(); // Deletions
    });
  });

  it("should show no repository message when status is null", () => {
    vi.mocked(useGitStore).mockReturnValue({
      status: null,
      loading: false,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    expect(screen.getByText("No Git repository found")).toBeInTheDocument();
  });

  it("should call refreshStatus on mount", () => {
    vi.mocked(useGitStore).mockReturnValue({
      status: undefined,
      loading: false,
      error: undefined,
      refreshStatus: mockRefreshStatus,
      clearError: mockClearError,
    } as any);

    render(<GitStatusPanel />);

    expect(mockRefreshStatus).toHaveBeenCalledTimes(1);
  });
});
