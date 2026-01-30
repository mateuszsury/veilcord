/**
 * Message bubble component for displaying a single message.
 *
 * Displays different styles for sent (self) vs received messages.
 * Shows timestamp, edited indicator, reactions, and handles dark cosmic theme.
 * Supports context menu for actions (edit, delete, react, copy).
 * Supports inline editing mode.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { Message } from '@/stores/messages';
import { MessageContextMenu } from './MessageContextMenu';
import { api } from '@/lib/pywebview';

interface Reaction {
  emoji: string;
  count: number;
  hasSelf: boolean;
}

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
  contactId: number;
}

export function MessageBubble({ message, isOwn, contactId }: MessageBubbleProps) {
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.body);
  const [reactions, setReactions] = useState<Reaction[]>([]);
  const editInputRef = useRef<HTMLTextAreaElement>(null);

  const formattedTime = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  // Load reactions for this message
  useEffect(() => {
    const loadReactions = async () => {
      try {
        const rawReactions = await api.call((a) => a.get_reactions(message.id));
        // Group reactions by emoji
        const grouped = rawReactions.reduce<Record<string, { count: number; hasSelf: boolean }>>(
          (acc, r) => {
            const entry = acc[r.emoji] ?? { count: 0, hasSelf: false };
            entry.count++;
            if (r.senderId === 'self') {
              entry.hasSelf = true;
            }
            acc[r.emoji] = entry;
            return acc;
          },
          {}
        );

        setReactions(
          Object.entries(grouped).map(([emoji, data]) => ({
            emoji,
            count: data.count,
            hasSelf: data.hasSelf,
          }))
        );
      } catch (error) {
        // Ignore errors loading reactions
      }
    };

    loadReactions();
  }, [message.id]);

  // Focus edit input when entering edit mode
  useEffect(() => {
    if (isEditing && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.setSelectionRange(editText.length, editText.length);
    }
  }, [isEditing, editText]);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY });
  };

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(message.body);
  }, [message.body]);

  const handleReact = useCallback(
    async (emoji: string) => {
      try {
        // Check if already reacted with this emoji
        const existing = reactions.find((r) => r.emoji === emoji && r.hasSelf);
        if (existing) {
          await api.call((a) => a.remove_reaction(contactId, message.id, emoji));
          setReactions((prev) =>
            prev
              .map((r) =>
                r.emoji === emoji ? { ...r, count: r.count - 1, hasSelf: false } : r
              )
              .filter((r) => r.count > 0)
          );
        } else {
          await api.call((a) => a.add_reaction(contactId, message.id, emoji));
          setReactions((prev) => {
            const existingReaction = prev.find((r) => r.emoji === emoji);
            if (existingReaction) {
              return prev.map((r) =>
                r.emoji === emoji ? { ...r, count: r.count + 1, hasSelf: true } : r
              );
            }
            return [...prev, { emoji, count: 1, hasSelf: true }];
          });
        }
      } catch (error) {
        console.error('Failed to toggle reaction:', error);
      }
    },
    [contactId, message.id, reactions]
  );

  const handleEdit = useCallback(() => {
    setEditText(message.body);
    setIsEditing(true);
  }, [message.body]);

  const handleEditSubmit = useCallback(async () => {
    if (editText.trim() && editText !== message.body) {
      try {
        await api.call((a) => a.edit_message(contactId, message.id, editText.trim()));
      } catch (error) {
        console.error('Failed to edit message:', error);
      }
    }
    setIsEditing(false);
  }, [editText, message.body, contactId, message.id]);

  const handleEditCancel = useCallback(() => {
    setEditText(message.body);
    setIsEditing(false);
  }, [message.body]);

  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEditSubmit();
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const handleDelete = useCallback(async () => {
    try {
      await api.call((a) => a.delete_message(contactId, message.id));
    } catch (error) {
      console.error('Failed to delete message:', error);
    }
  }, [contactId, message.id]);

  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 shadow-lg backdrop-blur-sm ${
          isOwn
            ? 'bg-cosmic-accent text-white rounded-br-sm'
            : 'bg-cosmic-surface text-cosmic-text rounded-bl-sm'
        }`}
        onContextMenu={handleContextMenu}
      >
        {/* Reply indicator */}
        {message.reply_to && (
          <div className="text-xs opacity-70 border-l-2 border-white/30 pl-2 mb-1">
            Replying to message...
          </div>
        )}

        {/* Message body or edit input */}
        {isEditing ? (
          <div className="flex flex-col gap-1">
            <textarea
              ref={editInputRef}
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onKeyDown={handleEditKeyDown}
              className="w-full bg-cosmic-base/50 text-cosmic-text rounded px-2 py-1 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-cosmic-accent"
              rows={2}
            />
            <div className="flex gap-2 text-xs">
              <button
                type="button"
                onClick={handleEditSubmit}
                className="text-cosmic-success hover:underline"
              >
                Save
              </button>
              <button
                type="button"
                onClick={handleEditCancel}
                className="text-cosmic-muted hover:underline"
              >
                Cancel
              </button>
              <span className="text-cosmic-muted opacity-50">
                Enter to save, Esc to cancel
              </span>
            </div>
          </div>
        ) : (
          <p className="break-words whitespace-pre-wrap">{message.body}</p>
        )}

        {/* Reactions */}
        {reactions.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {reactions.map((reaction) => (
              <button
                key={reaction.emoji}
                type="button"
                onClick={() => handleReact(reaction.emoji)}
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs transition-colors ${
                  reaction.hasSelf
                    ? 'bg-cosmic-accent/30 border border-cosmic-accent/50'
                    : 'bg-cosmic-base/50 hover:bg-cosmic-base/70'
                }`}
              >
                <span>{reaction.emoji}</span>
                <span className="opacity-70">{reaction.count}</span>
              </button>
            ))}
          </div>
        )}

        {/* Footer: time and edited */}
        <div className="flex items-center justify-end gap-2 mt-1">
          {message.edited && (
            <span className="text-xs opacity-50">(edited)</span>
          )}
          <span className="text-xs opacity-50">{formattedTime}</span>
        </div>
      </div>

      {/* Context menu */}
      {contextMenu && (
        <MessageContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          isOwn={isOwn}
          onCopy={handleCopy}
          onReact={handleReact}
          onEdit={isOwn ? handleEdit : undefined}
          onDelete={isOwn ? handleDelete : undefined}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
}
