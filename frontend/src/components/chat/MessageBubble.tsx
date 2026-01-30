/**
 * Message bubble component for displaying a single message.
 *
 * Displays different styles for sent (self) vs received messages.
 * Shows timestamp, edited indicator, and handles dark cosmic theme.
 */

import type { Message } from '@/stores/messages';

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
}

export function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  const formattedTime = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 shadow-lg backdrop-blur-sm ${
          isOwn
            ? 'bg-cosmic-accent text-white rounded-br-sm'
            : 'bg-cosmic-surface text-cosmic-text rounded-bl-sm'
        }`}
      >
        {/* Reply indicator */}
        {message.reply_to && (
          <div className="text-xs opacity-70 border-l-2 border-white/30 pl-2 mb-1">
            Replying to message...
          </div>
        )}

        {/* Message body */}
        <p className="break-words whitespace-pre-wrap">{message.body}</p>

        {/* Footer: time and edited */}
        <div className="flex items-center justify-end gap-2 mt-1">
          {message.edited && (
            <span className="text-xs opacity-50">(edited)</span>
          )}
          <span className="text-xs opacity-50">{formattedTime}</span>
        </div>
      </div>
    </div>
  );
}
