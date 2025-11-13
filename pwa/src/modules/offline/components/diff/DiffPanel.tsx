/**
 * Individual diff panel showing one version (base, theirs, or mine)
 */

import type { DiffLine, DiffSide } from "./types";

interface DiffPanelProps {
  title: string;
  side: DiffSide;
  lines: DiffLine[];
  isSelected: boolean;
  onSelect: () => void;
}

export function DiffPanel({
  title,
  side,
  lines,
  isSelected,
  onSelect,
}: DiffPanelProps) {
  const getBorderColor = () => {
    if (isSelected) {
      return "border-blue-500 bg-blue-500/5";
    }
    return "border-slate-700 hover:border-slate-600";
  };

  const getTitleColor = () => {
    switch (side) {
      case "base":
        return "text-slate-400";
      case "theirs":
        return "text-purple-400";
      case "mine":
        return "text-emerald-400";
    }
  };

  const getLineStyle = (line: DiffLine) => {
    switch (line.type) {
      case "added":
        return "bg-emerald-500/10 text-emerald-300";
      case "removed":
        return "bg-red-500/10 text-red-300";
      case "conflict":
        return "bg-amber-500/10 text-amber-200";
      case "unchanged":
      default:
        return "text-slate-300";
    }
  };

  return (
    <div
      className={`flex flex-1 flex-col rounded-lg border ${getBorderColor()} transition-colors cursor-pointer`}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700 px-3 py-2">
        <div className={`text-sm font-semibold ${getTitleColor()}`}>
          {title}
        </div>
        {isSelected && (
          <div className="rounded-full bg-blue-500 px-2 py-0.5 text-xs font-semibold text-white">
            Selected
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-slate-900/50 p-3 font-mono text-xs">
        {lines.length === 0 ? (
          <div className="text-slate-500 italic">Empty</div>
        ) : (
          lines.map((line, index) => (
            <div
              key={index}
              className={`flex gap-3 px-2 py-0.5 ${getLineStyle(line)}`}
            >
              <span className="w-10 text-right text-slate-500 select-none">
                {line.lineNumber}
              </span>
              <span className="flex-1 whitespace-pre-wrap break-all">
                {line.content || " "}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-700 px-3 py-1.5 text-xs text-slate-400">
        {lines.length} line{lines.length !== 1 ? "s" : ""}
      </div>
    </div>
  );
}
