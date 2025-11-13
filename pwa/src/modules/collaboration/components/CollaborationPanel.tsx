/**
 * Collaboration Panel
 *
 * Main panel that combines ThreadView and MessageComposer.
 * Handles context linking with floor plan elements.
 */

import { useCollaborationStore } from "../state/collaborationStore";
import { ThreadView } from "./ThreadView";
import { MessageComposer } from "./MessageComposer";
import { MessageSquare } from "lucide-react";
import type { ElementReference } from "../types";

interface CollaborationPanelProps {
  onElementClick?: (ref: ElementReference) => void;
}

export function CollaborationPanel({ onElementClick }: CollaborationPanelProps) {
  const { activeRoomId, rooms } = useCollaborationStore();

  if (!activeRoomId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="text-center text-slate-500">
          <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">Select a room to start collaborating</p>
        </div>
      </div>
    );
  }

  const room = rooms.get(activeRoomId);

  return (
    <div className="flex-1 flex flex-col bg-slate-950">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-700 bg-slate-900">
        <h2 className="text-lg font-semibold text-slate-100">
          {room?.name || "Unknown Room"}
        </h2>
        {room?.buildingPath && (
          <p className="text-xs text-slate-500 mt-1">{room.buildingPath}</p>
        )}
      </div>

      {/* Messages */}
      <ThreadView roomId={activeRoomId} onElementClick={onElementClick} />

      {/* Composer */}
      <MessageComposer roomId={activeRoomId} />
    </div>
  );
}
