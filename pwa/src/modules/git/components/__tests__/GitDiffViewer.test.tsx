/**
 * GitDiffViewer component tests
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { GitDiffViewer } from "../GitDiffViewer";
import { useGitStore } from "../../../../state/git";

// Mock the git store
vi.mock("../../../../state/git", () => ({
  useGitStore: vi.fn(),
}));

describe("GitDiffViewer", () => {
  const mockLoadDiff = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading state initially", () => {
    vi.mocked(useGitStore).mockReturnValue({
      diff: undefined,
      loading: true,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    expect(screen.getByText("Loading diff...")).toBeInTheDocument();
  });

  it("should display error message", () => {
    vi.mocked(useGitStore).mockReturnValue({
      diff: undefined,
      loading: false,
      error: "Failed to load diff",
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    expect(screen.getByText("Error Loading Diff")).toBeInTheDocument();
    expect(screen.getByText("Failed to load diff")).toBeInTheDocument();
  });

  it("should show no changes message when diff is empty", () => {
    vi.mocked(useGitStore).mockReturnValue({
      diff: {
        commit_hash: "HEAD",
        compare_hash: "HEAD~1",
        files_changed: 0,
        insertions: 0,
        deletions: 0,
        files: [],
      },
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    expect(screen.getByText("No changes to display")).toBeInTheDocument();
  });

  it("should display diff summary", async () => {
    const mockDiff = {
      commit_hash: "HEAD",
      compare_hash: "HEAD~1",
      files_changed: 2,
      insertions: 10,
      deletions: 5,
      files: [
        {
          file_path: "src/test.ts",
          line_number: 1,
          kind: "addition",
          content: "const foo = 'bar';",
        },
      ],
    };

    vi.mocked(useGitStore).mockReturnValue({
      diff: mockDiff,
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    await waitFor(() => {
      expect(screen.getByText("Changes")).toBeInTheDocument();
      expect(screen.getByText("+10")).toBeInTheDocument();
      expect(screen.getByText("-5")).toBeInTheDocument();
      expect(screen.getByText("2 files")).toBeInTheDocument();
    });
  });

  it("should group lines by file", async () => {
    const mockDiff = {
      commit_hash: "HEAD",
      compare_hash: "HEAD~1",
      files_changed: 2,
      insertions: 2,
      deletions: 1,
      files: [
        {
          file_path: "src/file1.ts",
          line_number: 1,
          kind: "addition",
          content: "line 1",
        },
        {
          file_path: "src/file1.ts",
          line_number: 2,
          kind: "deletion",
          content: "line 2",
        },
        {
          file_path: "src/file2.ts",
          line_number: 1,
          kind: "addition",
          content: "line 3",
        },
      ],
    };

    vi.mocked(useGitStore).mockReturnValue({
      diff: mockDiff,
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    await waitFor(() => {
      expect(screen.getByText("src/file1.ts")).toBeInTheDocument();
      expect(screen.getByText("src/file2.ts")).toBeInTheDocument();
    });
  });

  it("should expand and collapse files", async () => {
    const mockDiff = {
      commit_hash: "HEAD",
      compare_hash: "HEAD~1",
      files_changed: 1,
      insertions: 1,
      deletions: 0,
      files: [
        {
          file_path: "src/test.ts",
          line_number: 1,
          kind: "addition",
          content: "const foo = 'bar';",
        },
      ],
    };

    vi.mocked(useGitStore).mockReturnValue({
      diff: mockDiff,
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    // File should be collapsed initially
    const fileName = screen.getByText("src/test.ts");
    expect(screen.queryByText("const foo = 'bar';")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(fileName);

    await waitFor(() => {
      expect(screen.getByText("const foo = 'bar';")).toBeInTheDocument();
    });

    // Click to collapse
    fireEvent.click(fileName);

    await waitFor(() => {
      expect(screen.queryByText("const foo = 'bar';")).not.toBeInTheDocument();
    });
  });

  it("should calculate file stats correctly", async () => {
    const mockDiff = {
      commit_hash: "HEAD",
      compare_hash: "HEAD~1",
      files_changed: 1,
      insertions: 3,
      deletions: 2,
      files: [
        {
          file_path: "src/test.ts",
          line_number: 1,
          kind: "addition",
          content: "line 1",
        },
        {
          file_path: "src/test.ts",
          line_number: 2,
          kind: "addition",
          content: "line 2",
        },
        {
          file_path: "src/test.ts",
          line_number: 3,
          kind: "deletion",
          content: "line 3",
        },
        {
          file_path: "src/test.ts",
          line_number: 4,
          kind: "deletion",
          content: "line 4",
        },
        {
          file_path: "src/test.ts",
          line_number: 5,
          kind: "addition",
          content: "line 5",
        },
      ],
    };

    vi.mocked(useGitStore).mockReturnValue({
      diff: mockDiff,
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    await waitFor(() => {
      // Should show +3 and -2 (may appear multiple times in header and file stats)
      const additions = screen.getAllByText("+3");
      const deletions = screen.getAllByText("-2");
      expect(additions.length).toBeGreaterThanOrEqual(1);
      expect(deletions.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("should call loadDiff on mount", () => {
    vi.mocked(useGitStore).mockReturnValue({
      diff: undefined,
      loading: false,
      error: undefined,
      loadDiff: mockLoadDiff,
      clearError: mockClearError,
    } as any);

    render(<GitDiffViewer />);

    expect(mockLoadDiff).toHaveBeenCalledTimes(1);
  });
});
