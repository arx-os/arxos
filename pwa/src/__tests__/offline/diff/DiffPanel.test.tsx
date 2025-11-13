/**
 * DiffPanel component tests
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DiffPanel } from "../../../modules/offline/components/diff/DiffPanel";
import type { DiffLine } from "../../../modules/offline/components/diff/types";

describe("DiffPanel", () => {
  const mockLines: DiffLine[] = [
    { lineNumber: 1, content: "line 1", type: "unchanged" },
    { lineNumber: 2, content: "line 2", type: "added" },
    { lineNumber: 3, content: "line 3", type: "removed" },
  ];

  it("should render panel with title", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("Base")).toBeInTheDocument();
  });

  it("should display line count", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("3 lines")).toBeInTheDocument();
  });

  it("should show 'Selected' badge when selected", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={true}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("Selected")).toBeInTheDocument();
  });

  it("should call onSelect when clicked", () => {
    const onSelect = vi.fn();

    const { container } = render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    const panel = container.firstChild as HTMLElement;
    fireEvent.click(panel);

    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("should display all lines with line numbers", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("line 1")).toBeInTheDocument();
    expect(screen.getByText("line 2")).toBeInTheDocument();
    expect(screen.getByText("line 3")).toBeInTheDocument();
  });

  it("should show 'Empty' message when no lines", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={[]}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText("Empty")).toBeInTheDocument();
    expect(screen.getByText("0 lines")).toBeInTheDocument();
  });

  it("should use correct color for base side", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Base"
        side="base"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    const title = screen.getByText("Base");
    expect(title.className).toContain("text-slate-400");
  });

  it("should use correct color for theirs side", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Theirs"
        side="theirs"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    const title = screen.getByText("Theirs");
    expect(title.className).toContain("text-purple-400");
  });

  it("should use correct color for mine side", () => {
    const onSelect = vi.fn();

    render(
      <DiffPanel
        title="Mine"
        side="mine"
        lines={mockLines}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    const title = screen.getByText("Mine");
    expect(title.className).toContain("text-emerald-400");
  });
});
