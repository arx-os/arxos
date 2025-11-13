/**
 * Floor plan edit toolbar
 *
 * Provides tools for editing floor plans including:
 * - Mode selection (Select, Draw Room, Add Equipment)
 * - Undo/Redo buttons
 * - Delete selected object
 */

import { MousePointer, Square, Wrench, Trash2, Undo, Redo } from "lucide-react";

export type EditMode = "select" | "draw-room" | "add-equipment";

export interface EditToolbarProps {
  mode: EditMode;
  onModeChange: (mode: EditMode) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  hasSelection: boolean;
  onDelete: () => void;
}

export function EditToolbar({
  mode,
  onModeChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  hasSelection,
  onDelete,
}: EditToolbarProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/90 p-2 shadow-lg">
      {/* Mode Selection */}
      <div className="flex items-center gap-1 rounded-md border border-slate-700 bg-slate-950 p-1">
        <button
          onClick={() => onModeChange("select")}
          className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-medium transition ${
            mode === "select"
              ? "bg-sky-500/30 text-sky-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          }`}
          title="Select Mode (V)"
        >
          <MousePointer className="h-4 w-4" />
          <span>Select</span>
        </button>
        <button
          onClick={() => onModeChange("draw-room")}
          className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-medium transition ${
            mode === "draw-room"
              ? "bg-sky-500/30 text-sky-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          }`}
          title="Draw Room (R)"
        >
          <Square className="h-4 w-4" />
          <span>Draw Room</span>
        </button>
        <button
          onClick={() => onModeChange("add-equipment")}
          className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-medium transition ${
            mode === "add-equipment"
              ? "bg-sky-500/30 text-sky-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          }`}
          title="Add Equipment (E)"
        >
          <Wrench className="h-4 w-4" />
          <span>Add Equipment</span>
        </button>
      </div>

      {/* Divider */}
      <div className="h-6 w-px bg-slate-700" />

      {/* Undo/Redo */}
      <div className="flex items-center gap-1">
        <button
          onClick={onUndo}
          disabled={!canUndo}
          className="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-slate-400"
          title="Undo (Ctrl+Z)"
        >
          <Undo className="h-4 w-4" />
          <span>Undo</span>
        </button>
        <button
          onClick={onRedo}
          disabled={!canRedo}
          className="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-slate-400"
          title="Redo (Ctrl+Y)"
        >
          <Redo className="h-4 w-4" />
          <span>Redo</span>
        </button>
      </div>

      {/* Divider */}
      <div className="h-6 w-px bg-slate-700" />

      {/* Delete */}
      <button
        onClick={onDelete}
        disabled={!hasSelection}
        className="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-red-900/30 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-slate-400"
        title="Delete Selected (Delete)"
      >
        <Trash2 className="h-4 w-4" />
        <span>Delete</span>
      </button>
    </div>
  );
}
