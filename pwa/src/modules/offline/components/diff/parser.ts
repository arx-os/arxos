/**
 * Git conflict parsing utilities
 */

import { v4 as uuidv4 } from "uuid";
import type { ConflictFile, ConflictHunk, DiffLine } from "./types";

/**
 * Parse a file's content into lines with metadata
 */
function parseLines(content: string): DiffLine[] {
  const lines = content.split("\n");
  return lines.map((line, index) => ({
    lineNumber: index + 1,
    content: line,
    type: "unchanged" as const,
  }));
}

/**
 * Parse a Git conflict structure into our ConflictFile format
 */
export function parseGitConflict(
  filePath: string,
  base: string,
  theirs: string,
  mine: string
): ConflictFile {
  const baseLines = parseLines(base);
  const theirsLines = parseLines(theirs);
  const mineLines = parseLines(mine);

  // Create a single hunk for the entire file
  // In a more sophisticated implementation, we'd detect specific conflict regions
  const hunk: ConflictHunk = {
    id: uuidv4(),
    startLine: 1,
    endLine: Math.max(baseLines.length, theirsLines.length, mineLines.length),
    base: baseLines,
    theirs: theirsLines,
    mine: mineLines,
    resolution: null,
  };

  return {
    filePath,
    hunks: [hunk],
    base,
    theirs,
    mine,
  };
}

/**
 * Detect changes between two sets of lines
 */
export function detectChanges(
  baseLines: DiffLine[],
  changedLines: DiffLine[]
): DiffLine[] {
  // Simple line-by-line comparison
  // In production, you'd use a proper diff algorithm (e.g., Myers diff)
  const maxLength = Math.max(baseLines.length, changedLines.length);
  const result: DiffLine[] = [];

  for (let i = 0; i < maxLength; i++) {
    const baseLine = baseLines[i];
    const changedLine = changedLines[i];

    if (!baseLine && changedLine) {
      // Line was added
      result.push({ ...changedLine, type: "added" });
    } else if (baseLine && !changedLine) {
      // Line was removed
      result.push({ ...baseLine, type: "removed" });
    } else if (baseLine && changedLine) {
      if (baseLine.content === changedLine.content) {
        // Line unchanged
        result.push({ ...changedLine, type: "unchanged" });
      } else {
        // Line modified (treat as removed + added)
        result.push({ ...baseLine, type: "removed" });
        result.push({ ...changedLine, type: "added" });
      }
    }
  }

  return result;
}

/**
 * Parse Git conflict markers in content
 * Format:
 * <<<<<<< HEAD (theirs)
 * their content
 * ||||||| base
 * base content
 * =======
 * my content
 * >>>>>>> branch (mine)
 */
export function parseConflictMarkers(content: string): ConflictHunk[] {
  const lines = content.split("\n");
  const hunks: ConflictHunk[] = [];
  let currentHunk: Partial<ConflictHunk> | null = null;
  let section: "theirs" | "base" | "mine" | null = null;
  let startLine = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith("<<<<<<<")) {
      // Start of conflict
      currentHunk = {
        id: uuidv4(),
        startLine: i + 1,
        theirs: [],
        base: [],
        mine: [],
        resolution: null,
      };
      section = "theirs";
      startLine = i;
    } else if (line.startsWith("|||||||")) {
      // Base section
      section = "base";
    } else if (line.startsWith("=======")) {
      // Mine section
      section = "mine";
    } else if (line.startsWith(">>>>>>>")) {
      // End of conflict
      if (currentHunk) {
        currentHunk.endLine = i + 1;
        hunks.push(currentHunk as ConflictHunk);
        currentHunk = null;
        section = null;
      }
    } else if (currentHunk && section) {
      // Content line
      const diffLine: DiffLine = {
        lineNumber: i - startLine,
        content: line,
        type: "conflict",
      };

      if (section === "theirs") {
        currentHunk.theirs!.push(diffLine);
      } else if (section === "base") {
        currentHunk.base!.push(diffLine);
      } else if (section === "mine") {
        currentHunk.mine!.push(diffLine);
      }
    }
  }

  return hunks;
}

/**
 * Apply resolution to a hunk
 */
export function resolveHunk(
  hunk: ConflictHunk,
  resolution: "base" | "theirs" | "mine" | "both" | "neither"
): string {
  switch (resolution) {
    case "base":
      return hunk.base.map((l) => l.content).join("\n");
    case "theirs":
      return hunk.theirs.map((l) => l.content).join("\n");
    case "mine":
      return hunk.mine.map((l) => l.content).join("\n");
    case "both":
      // Concatenate mine then theirs
      return [
        ...hunk.mine.map((l) => l.content),
        ...hunk.theirs.map((l) => l.content),
      ].join("\n");
    case "neither":
      // Use base as fallback for "neither"
      return hunk.base.map((l) => l.content).join("\n");
    default:
      return "";
  }
}

/**
 * Generate the final merged content from all hunk resolutions
 */
export function generateMergedContent(
  originalContent: string,
  hunks: ConflictHunk[]
): string {
  const lines = originalContent.split("\n");
  const result: string[] = [];
  let lastEndLine = 0;

  for (const hunk of hunks) {
    // Add unchanged lines before this hunk
    for (let i = lastEndLine; i < hunk.startLine - 1; i++) {
      result.push(lines[i]);
    }

    // Add resolved content
    if (hunk.resolution) {
      const resolved = resolveHunk(hunk, hunk.resolution);
      result.push(resolved);
    }

    lastEndLine = hunk.endLine;
  }

  // Add remaining unchanged lines
  for (let i = lastEndLine; i < lines.length; i++) {
    result.push(lines[i]);
  }

  return result.join("\n");
}

/**
 * Calculate diff statistics
 */
export function calculateDiffStats(files: ConflictFile[]) {
  let totalConflicts = 0;
  let resolvedConflicts = 0;
  let linesAdded = 0;
  let linesRemoved = 0;

  for (const file of files) {
    for (const hunk of file.hunks) {
      totalConflicts++;
      if (hunk.resolution !== null) {
        resolvedConflicts++;
      }

      // Count changes in "mine" vs "theirs"
      const addedInMine = hunk.mine.filter((l) => l.type === "added").length;
      const removedInMine = hunk.mine.filter((l) => l.type === "removed").length;

      linesAdded += addedInMine;
      linesRemoved += removedInMine;
    }
  }

  return {
    totalConflicts,
    resolvedConflicts,
    filesWithConflicts: files.length,
    linesAdded,
    linesRemoved,
  };
}
