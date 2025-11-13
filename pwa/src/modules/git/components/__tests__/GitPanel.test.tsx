/**
 * GitPanel component tests
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GitPanel } from "../GitPanel";

// Mock the sub-components
vi.mock("../GitStatusPanel", () => ({
  GitStatusPanel: () => <div data-testid="status-panel">Status Panel</div>,
}));

vi.mock("../GitDiffViewer", () => ({
  GitDiffViewer: () => <div data-testid="diff-viewer">Diff Viewer</div>,
}));

vi.mock("../GitHistoryPanel", () => ({
  GitHistoryPanel: () => <div data-testid="history-panel">History Panel</div>,
}));

describe("GitPanel", () => {
  it("should render with default status tab", () => {
    render(<GitPanel />);

    expect(screen.getByText("Git")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Changes")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.getByTestId("status-panel")).toBeInTheDocument();
  });

  it("should render with specified initial tab", () => {
    render(<GitPanel initialTab="diff" />);

    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();
  });

  it("should switch tabs when clicked", () => {
    render(<GitPanel />);

    // Initially shows status
    expect(screen.getByTestId("status-panel")).toBeInTheDocument();

    // Click on Changes tab
    const changesTab = screen.getByText("Changes");
    fireEvent.click(changesTab);

    // Should show diff viewer
    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();

    // Click on History tab
    const historyTab = screen.getByText("History");
    fireEvent.click(historyTab);

    // Should show history panel
    expect(screen.getByTestId("history-panel")).toBeInTheDocument();
  });

  it("should show close button when showCloseButton is true", () => {
    const onClose = vi.fn();
    render(<GitPanel showCloseButton={true} onClose={onClose} />);

    const closeButton = screen.getByLabelText("Close Git panel");
    expect(closeButton).toBeInTheDocument();

    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should not show close button by default", () => {
    render(<GitPanel />);

    const closeButton = screen.queryByLabelText("Close Git panel");
    expect(closeButton).not.toBeInTheDocument();
  });

  it("should have proper ARIA attributes", () => {
    render(<GitPanel />);

    const statusTab = screen.getByRole("button", { name: /view current repository status/i });
    expect(statusTab).toHaveAttribute("aria-current", "page");
    expect(statusTab).toHaveAttribute("aria-label", "View current repository status");
  });
});
