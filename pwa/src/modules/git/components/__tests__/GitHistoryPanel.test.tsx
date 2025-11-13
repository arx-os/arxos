/**
 * GitHistoryPanel component tests
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { GitHistoryPanel } from "../GitHistoryPanel";
import * as gitCommands from "../../../agent/commands/git";

// Mock the git commands
vi.mock("../../../agent/commands/git", () => ({
  gitLog: vi.fn(),
}));

describe("GitHistoryPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading state initially", () => {
    vi.mocked(gitCommands.gitLog).mockReturnValue(
      new Promise(() => {}) // Never resolves
    );

    render(<GitHistoryPanel />);

    expect(screen.getByText("Loading history...")).toBeInTheDocument();
  });

  it("should display commit history", async () => {
    const mockCommits = [
      {
        hash: "abc123def456",
        message: "Initial commit",
        author: "John Doe",
        timestamp: new Date().toISOString(),
      },
      {
        hash: "def456ghi789",
        message: "Add feature",
        author: "Jane Smith",
        timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      },
    ];

    vi.mocked(gitCommands.gitLog).mockResolvedValue(mockCommits);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText("Initial commit")).toBeInTheDocument();
      expect(screen.getByText("Add feature")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
      expect(screen.getByText("abc123de")).toBeInTheDocument(); // First 8 chars
      expect(screen.getByText("def456gh")).toBeInTheDocument();
    });
  });

  it("should display error message", async () => {
    vi.mocked(gitCommands.gitLog).mockRejectedValue(
      new Error("Failed to load history")
    );

    render(<GitHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText("Error Loading History")).toBeInTheDocument();
      expect(screen.getByText("Failed to load history")).toBeInTheDocument();
    });
  });

  it("should show empty state when no commits", async () => {
    vi.mocked(gitCommands.gitLog).mockResolvedValue([]);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText("No commit history found")).toBeInTheDocument();
    });
  });

  it("should handle pagination", async () => {
    const page1Commits = Array.from({ length: 20 }, (_, i) => ({
      hash: `hash${i}`,
      message: `Commit ${i}`,
      author: "Author",
      timestamp: new Date().toISOString(),
    }));

    const page2Commits = Array.from({ length: 20 }, (_, i) => ({
      hash: `hash${i + 20}`,
      message: `Commit ${i + 20}`,
      author: "Author",
      timestamp: new Date().toISOString(),
    }));

    vi.mocked(gitCommands.gitLog)
      .mockResolvedValueOnce(page1Commits)
      .mockResolvedValueOnce(page2Commits);

    render(<GitHistoryPanel />);

    // Wait for first page to load
    await waitFor(() => {
      expect(screen.getByText("Commit 0")).toBeInTheDocument();
    });

    // Click next button
    const nextButton = screen.getByText("Next");
    fireEvent.click(nextButton);

    // Wait for second page to load
    await waitFor(() => {
      expect(screen.getByText("Commit 20")).toBeInTheDocument();
    });

    // Verify page number
    expect(screen.getByText("Page 2")).toBeInTheDocument();

    // Click previous button
    const prevButton = screen.getByText("Previous");
    fireEvent.click(prevButton);

    // Should be back to page 1
    await waitFor(() => {
      expect(screen.getByText("Page 1")).toBeInTheDocument();
    });
  });

  it("should disable next button when no more commits", async () => {
    const commits = Array.from({ length: 10 }, (_, i) => ({
      hash: `hash${i}`,
      message: `Commit ${i}`,
      author: "Author",
      timestamp: new Date().toISOString(),
    }));

    vi.mocked(gitCommands.gitLog).mockResolvedValue(commits);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      const nextButton = screen.getByRole("button", { name: /next/i });
      expect(nextButton).toBeDisabled();
    });
  });

  it("should disable previous button on first page", async () => {
    const commits = [
      {
        hash: "abc123",
        message: "Test commit",
        author: "Author",
        timestamp: new Date().toISOString(),
      },
    ];

    vi.mocked(gitCommands.gitLog).mockResolvedValue(commits);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      const prevButton = screen.getByRole("button", { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });
  });

  it("should format recent timestamps correctly", async () => {
    const now = new Date();
    const commits = [
      {
        hash: "abc123",
        message: "Recent commit",
        author: "Author",
        timestamp: now.toISOString(),
      },
      {
        hash: "def456",
        message: "Older commit",
        author: "Author",
        timestamp: new Date(now.getTime() - 3600000).toISOString(),
      },
      {
        hash: "ghi789",
        message: "Old commit",
        author: "Author",
        timestamp: new Date(now.getTime() - 172800000).toISOString(),
      },
    ];

    vi.mocked(gitCommands.gitLog).mockResolvedValue(commits);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      // Check that timestamp formatting exists (may appear as "Just now", "1 hour ago", etc.)
      const timestamps = screen.getAllByText(/ago|Just now/i);
      expect(timestamps.length).toBeGreaterThanOrEqual(3);
    });
  });

  it("should call gitLog with correct pagination params", async () => {
    const commits = Array.from({ length: 20 }, (_, i) => ({
      hash: `hash${i}`,
      message: `Commit ${i}`,
      author: "Author",
      timestamp: new Date().toISOString(),
    }));

    vi.mocked(gitCommands.gitLog).mockResolvedValue(commits);

    render(<GitHistoryPanel />);

    await waitFor(() => {
      expect(gitCommands.gitLog).toHaveBeenCalledWith({
        limit: 20,
        offset: 0,
      });
    });

    // Go to next page
    const nextButton = screen.getByText("Next");
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(gitCommands.gitLog).toHaveBeenCalledWith({
        limit: 20,
        offset: 20,
      });
    });
  });
});
