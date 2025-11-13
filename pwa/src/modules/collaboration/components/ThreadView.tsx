/**
 * Thread View
 *
 * Displays messages in a conversation thread with timestamps,
 * authors, and context highlighting.
 */

import { useEffect, useRef } from "react";
import { useCollaborationStore } from "../state/collaborationStore";
import {
  CheckCheck,
  Check,
  Clock,
  AlertCircle,
  MapPin,
} from "lucide-react";
import type { CollaborationMessage, ElementReference } from "../types";

interface ThreadViewProps {
  roomId: string;
  onElementClick?: (ref: ElementReference) => void;
}

export function ThreadView({ roomId, onElementClick }: ThreadViewProps) {
  const { messages, users } = useCollaborationStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const roomMessages = messages.get(roomId) || [];

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [roomMessages.length]);

  if (roomMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500">
        <div className="text-center">
          <p className="text-sm">No messages yet</p>
          <p className="text-xs mt-1">Start the conversation!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {roomMessages.map((message, index) => {
        const prevMessage = index > 0 ? roomMessages[index - 1] : null;
        const showHeader =
          !prevMessage ||
          prevMessage.envelope.from !== message.envelope.from ||
          message.envelope.timestamp - prevMessage.envelope.timestamp > 60000; // 1 minute gap

        return (
          <MessageItem
            key={message.envelope.id}
            message={message}
            showHeader={showHeader}
            onElementClick={onElementClick}
          />
        );
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}

interface MessageItemProps {
  message: CollaborationMessage;
  showHeader: boolean;
  onElementClick?: (ref: ElementReference) => void;
}

function MessageItem({
  message,
  showHeader,
  onElementClick,
}: MessageItemProps) {
  const { users } = useCollaborationStore();
  const { envelope, status } = message;

  const user = users.get(envelope.from);
  const displayName = user?.displayName || envelope.from.slice(0, 8);

  // Format timestamp
  const date = new Date(envelope.timestamp);
  const time = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  // Get message content based on type
  const getContent = () => {
    if (envelope.type === "chat" || envelope.type === "comment") {
      return (envelope.payload as { content: string }).content;
    }
    return "";
  };

  // Get element reference if comment
  const getElementRef = (): ElementReference | null => {
    if (envelope.type === "comment") {
      return (envelope.payload as { elementRef: ElementReference }).elementRef;
    }
    return null;
  };

  const content = getContent();
  const elementRef = getElementRef();

  // Status indicator
  const getStatusIcon = () => {
    switch (status) {
      case "read":
        return <CheckCheck className="h-3 w-3 text-blue-400" />;
      case "delivered":
        return <CheckCheck className="h-3 w-3 text-slate-500" />;
      case "sent":
        return <Check className="h-3 w-3 text-slate-500" />;
      case "pending":
        return <Clock className="h-3 w-3 text-slate-500 animate-pulse" />;
      case "failed":
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="group">
      {showHeader && (
        <div className="flex items-center gap-2 mb-1">
          <div className="h-6 w-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-semibold text-blue-400">
              {displayName.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <span className="text-sm font-semibold text-slate-200">
            {displayName}
          </span>
          <span className="text-xs text-slate-500">{time}</span>
        </div>
      )}

      <div className={`${showHeader ? "ml-8" : "ml-8"}`}>
        {/* Element reference badge (for comments) */}
        {elementRef && (
          <button
            onClick={() => onElementClick?.(elementRef)}
            className="inline-flex items-center gap-1 px-2 py-1 mb-2 rounded-md bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-colors"
          >
            <MapPin className="h-3 w-3 text-purple-400" />
            <span className="text-xs text-purple-300">
              {elementRef.type}: {elementRef.name || elementRef.id}
            </span>
          </button>
        )}

        {/* Message content */}
        <div className="flex items-start gap-2">
          <div className="flex-1">
            <div className="text-sm text-slate-200 whitespace-pre-wrap break-words">
              {content}
            </div>
          </div>

          {/* Status icon */}
          <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            {getStatusIcon()}
          </div>
        </div>

        {/* Timestamp on hover (if no header) */}
        {!showHeader && (
          <div className="text-xs text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity mt-1">
            {time}
          </div>
        )}
      </div>
    </div>
  );
}
