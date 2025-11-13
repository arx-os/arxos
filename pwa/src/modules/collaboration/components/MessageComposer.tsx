/**
 * Message Composer
 *
 * Input field with markdown support for composing messages.
 * Includes element reference attachment and send controls.
 */

import { useState, useRef, KeyboardEvent } from "react";
import { useCollaborationStore } from "../state/collaborationStore";
import { Send, X, MapPin, Loader2 } from "lucide-react";

interface MessageComposerProps {
  roomId: string;
  placeholder?: string;
}

export function MessageComposer({
  roomId,
  placeholder = "Type a message...",
}: MessageComposerProps) {
  const {
    composerDraft,
    selectedElementRef,
    sendMessage,
    setComposerDraft,
    setSelectedElementRef,
    updatePresence,
  } = useCollaborationStore();

  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setComposerDraft(e.target.value);

    // Notify typing presence
    updatePresence("typing");
  };

  const handleSend = async () => {
    if (!composerDraft.trim() || isSending) return;

    setIsSending(true);

    try {
      await sendMessage(roomId, composerDraft.trim(), selectedElementRef || undefined);
      setComposerDraft("");
      setSelectedElementRef(null);

      // Focus back on input
      textareaRef.current?.focus();

      // Update presence to online
      updatePresence("online");
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRemoveElementRef = () => {
    setSelectedElementRef(null);
  };

  return (
    <div className="border-t border-slate-700 bg-slate-900 p-4">
      {/* Element reference badge */}
      {selectedElementRef && (
        <div className="mb-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30">
          <MapPin className="h-4 w-4 text-purple-400" />
          <span className="text-sm text-purple-300">
            Attaching to: {selectedElementRef.type} -{" "}
            {selectedElementRef.name || selectedElementRef.id}
          </span>
          <button
            onClick={handleRemoveElementRef}
            className="text-purple-400 hover:text-purple-300 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={composerDraft}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isSending}
            className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            rows={3}
            maxLength={2000}
          />

          {/* Character count */}
          <div className="absolute bottom-2 right-2 text-xs text-slate-500">
            {composerDraft.length}/2000
          </div>
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!composerDraft.trim() || isSending}
          className="flex-shrink-0 h-12 w-12 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors"
          title="Send message (Enter)"
        >
          {isSending ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Markdown hint */}
      <div className="mt-2 text-xs text-slate-500">
        Supports <strong>**bold**</strong>, <em>*italic*</em>, and `code`.
        Press Shift+Enter for new line.
      </div>
    </div>
  );
}
