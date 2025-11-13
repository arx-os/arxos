/**
 * Diff parser tests
 */

import { describe, it, expect } from "vitest";
import {
  parseGitConflict,
  detectChanges,
  resolveHunk,
  calculateDiffStats,
} from "../../../modules/offline/components/diff/parser";
import type { ConflictHunk } from "../../../modules/offline/components/diff/types";

describe("Diff Parser", () => {
  describe("parseGitConflict", () => {
    it("should parse a simple conflict", () => {
      const base = "line 1\nline 2\nline 3";
      const theirs = "line 1\nserver change\nline 3";
      const mine = "line 1\nmy change\nline 3";

      const result = parseGitConflict("test.txt", base, theirs, mine);

      expect(result.filePath).toBe("test.txt");
      expect(result.hunks).toHaveLength(1);
      expect(result.base).toBe(base);
      expect(result.theirs).toBe(theirs);
      expect(result.mine).toBe(mine);
    });

    it("should handle empty content", () => {
      const result = parseGitConflict("empty.txt", "", "", "");

      expect(result.filePath).toBe("empty.txt");
      expect(result.hunks).toHaveLength(1);
      // Empty string creates one empty line
      expect(result.hunks[0].base).toHaveLength(1);
      expect(result.hunks[0].theirs).toHaveLength(1);
      expect(result.hunks[0].mine).toHaveLength(1);
    });

    it("should create hunks with proper line numbers", () => {
      const content = "line 1\nline 2";
      const result = parseGitConflict("test.txt", content, content, content);

      const hunk = result.hunks[0];
      expect(hunk.startLine).toBe(1);
      expect(hunk.endLine).toBe(2);
    });
  });

  describe("detectChanges", () => {
    it("should detect added lines", () => {
      const base = [
        { lineNumber: 1, content: "line 1", type: "unchanged" as const },
      ];
      const changed = [
        { lineNumber: 1, content: "line 1", type: "unchanged" as const },
        { lineNumber: 2, content: "line 2", type: "unchanged" as const },
      ];

      const result = detectChanges(base, changed);

      expect(result).toHaveLength(2);
      expect(result[1].type).toBe("added");
    });

    it("should detect removed lines", () => {
      const base = [
        { lineNumber: 1, content: "line 1", type: "unchanged" as const },
        { lineNumber: 2, content: "line 2", type: "unchanged" as const },
      ];
      const changed = [
        { lineNumber: 1, content: "line 1", type: "unchanged" as const },
      ];

      const result = detectChanges(base, changed);

      expect(result[1].type).toBe("removed");
    });

    it("should detect modified lines", () => {
      const base = [
        { lineNumber: 1, content: "original", type: "unchanged" as const },
      ];
      const changed = [
        { lineNumber: 1, content: "modified", type: "unchanged" as const },
      ];

      const result = detectChanges(base, changed);

      // Modified lines are treated as removed + added
      expect(result[0].type).toBe("removed");
      expect(result[1].type).toBe("added");
    });

    it("should handle unchanged lines", () => {
      const base = [
        { lineNumber: 1, content: "same", type: "unchanged" as const },
      ];
      const changed = [
        { lineNumber: 1, content: "same", type: "unchanged" as const },
      ];

      const result = detectChanges(base, changed);

      expect(result[0].type).toBe("unchanged");
    });
  });

  describe("resolveHunk", () => {
    const mockHunk: ConflictHunk = {
      id: "test",
      startLine: 1,
      endLine: 3,
      base: [
        { lineNumber: 1, content: "base line 1", type: "unchanged" },
        { lineNumber: 2, content: "base line 2", type: "unchanged" },
      ],
      theirs: [
        { lineNumber: 1, content: "theirs line 1", type: "unchanged" },
        { lineNumber: 2, content: "theirs line 2", type: "unchanged" },
      ],
      mine: [
        { lineNumber: 1, content: "mine line 1", type: "unchanged" },
        { lineNumber: 2, content: "mine line 2", type: "unchanged" },
      ],
      resolution: null,
    };

    it('should resolve with "base" strategy', () => {
      const result = resolveHunk(mockHunk, "base");
      expect(result).toBe("base line 1\nbase line 2");
    });

    it('should resolve with "theirs" strategy', () => {
      const result = resolveHunk(mockHunk, "theirs");
      expect(result).toBe("theirs line 1\ntheirs line 2");
    });

    it('should resolve with "mine" strategy', () => {
      const result = resolveHunk(mockHunk, "mine");
      expect(result).toBe("mine line 1\nmine line 2");
    });

    it('should resolve with "both" strategy', () => {
      const result = resolveHunk(mockHunk, "both");
      expect(result).toBe("mine line 1\nmine line 2\ntheirs line 1\ntheirs line 2");
    });

    it('should resolve with "neither" strategy', () => {
      const result = resolveHunk(mockHunk, "neither");
      expect(result).toBe("base line 1\nbase line 2");
    });
  });

  describe("calculateDiffStats", () => {
    it("should calculate stats correctly", () => {
      const files = [
        parseGitConflict("file1.txt", "base", "theirs", "mine"),
        parseGitConflict("file2.txt", "base", "theirs", "mine"),
      ];

      const stats = calculateDiffStats(files);

      expect(stats.filesWithConflicts).toBe(2);
      expect(stats.totalConflicts).toBe(2);
      expect(stats.resolvedConflicts).toBe(0);
    });

    it("should count resolved conflicts", () => {
      const files = [parseGitConflict("file1.txt", "base", "theirs", "mine")];

      // Mark as resolved
      files[0].hunks[0].resolution = "mine";

      const stats = calculateDiffStats(files);

      expect(stats.totalConflicts).toBe(1);
      expect(stats.resolvedConflicts).toBe(1);
    });

    it("should handle empty files array", () => {
      const stats = calculateDiffStats([]);

      expect(stats.filesWithConflicts).toBe(0);
      expect(stats.totalConflicts).toBe(0);
      expect(stats.resolvedConflicts).toBe(0);
    });
  });
});
