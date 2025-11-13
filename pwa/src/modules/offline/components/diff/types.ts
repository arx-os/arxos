/**
 * Three-way diff viewer types
 */

export type DiffSide = "base" | "theirs" | "mine";
export type HunkResolution = "base" | "theirs" | "mine" | "both" | "neither";

/**
 * Represents a line in a diff
 */
export interface DiffLine {
  lineNumber: number;
  content: string;
  type: "added" | "removed" | "unchanged" | "conflict";
}

/**
 * Represents a conflict hunk (a section with conflicts)
 */
export interface ConflictHunk {
  id: string;
  startLine: number;
  endLine: number;
  base: DiffLine[];
  theirs: DiffLine[];
  mine: DiffLine[];
  resolution: HunkResolution | null;
}

/**
 * Represents a file with conflicts
 */
export interface ConflictFile {
  filePath: string;
  hunks: ConflictHunk[];
  // Original conflict data from Git
  base: string;
  theirs: string;
  mine: string;
}

/**
 * User's resolution for a specific hunk
 */
export interface HunkResolutionChoice {
  hunkId: string;
  resolution: HunkResolution;
  customContent?: string; // For manual edits
}

/**
 * Complete resolution state for a file
 */
export interface FileResolution {
  filePath: string;
  hunks: HunkResolutionChoice[];
  resolvedContent: string;
}

/**
 * Diff statistics
 */
export interface DiffStats {
  totalConflicts: number;
  resolvedConflicts: number;
  filesWithConflicts: number;
  linesAdded: number;
  linesRemoved: number;
}
