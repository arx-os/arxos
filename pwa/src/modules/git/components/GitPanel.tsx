/**
 * Git Panel
 * Container component with tabs for Status, Diff, and History
 */

import { useState } from "react";
import { GitStatusPanel } from "./GitStatusPanel";
import { GitDiffViewer } from "./GitDiffViewer";
import { GitHistoryPanel } from "./GitHistoryPanel";
import { GitBranch, FileText, Clock, X } from "lucide-react";

type TabType = "status" | "diff" | "history";

interface GitPanelProps {
  /** Initial tab to display */
  initialTab?: TabType;
  /** Optional callback when panel is closed */
  onClose?: () => void;
  /** Whether to show the close button */
  showCloseButton?: boolean;
}

export function GitPanel({
  initialTab = "status",
  onClose,
  showCloseButton = false,
}: GitPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);

  const tabs = [
    {
      id: "status" as TabType,
      label: "Status",
      icon: GitBranch,
      description: "View current repository status",
    },
    {
      id: "diff" as TabType,
      label: "Changes",
      icon: FileText,
      description: "View file changes and diffs",
    },
    {
      id: "history" as TabType,
      label: "History",
      icon: Clock,
      description: "View commit history",
    },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800/50 px-4 py-3">
        <h2 className="text-lg font-semibold text-slate-200">Git</h2>
        {showCloseButton && onClose && (
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
            aria-label="Close Git panel"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700 bg-slate-800/30">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex-1 flex items-center justify-center gap-2 px-4 py-3
                text-sm font-medium transition-colors
                ${
                  isActive
                    ? "text-blue-400 border-b-2 border-blue-400 bg-slate-800/50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                }
              `}
              aria-label={tab.description}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "status" && <GitStatusPanel />}
        {activeTab === "diff" && <GitDiffViewer />}
        {activeTab === "history" && <GitHistoryPanel />}
      </div>
    </div>
  );
}
