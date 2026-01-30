/**
 * Message input component with send button.
 *
 * Features:
 * - Multi-line input with auto-resize
 * - Send on Enter (Shift+Enter for newline)
 * - Typing indicator support
 * - Disabled state when not connected
 */

import { useState, useRef, type KeyboardEvent } from 'react';
import { api } from '@/lib/pywebview';

interface MessageInputProps {
  contactId: number;
  onSend: (body: string) => Promise<boolean>;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({
  contactId,
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = (value: string) => {
    setMessage(value);

    // Send typing indicator (throttled by backend)
    if (value.length > 0) {
      // Clear existing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Send typing indicator
      api.call((a) => a.send_typing(contactId, true)).catch(() => {});

      // Set timeout to send "stopped typing"
      typingTimeoutRef.current = setTimeout(() => {
        api.call((a) => a.send_typing(contactId, false)).catch(() => {});
      }, 3000);
    }
  };

  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed || sending || disabled) return;

    setSending(true);
    const success = await onSend(trimmed);

    if (success) {
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }

    setSending(false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  return (
    <div className="border-t border-cosmic-border p-4">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => {
            handleChange(e.target.value);
            handleInput();
          }}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Connect to send messages' : placeholder}
          disabled={disabled || sending}
          rows={1}
          className="flex-1 bg-cosmic-surface text-cosmic-text placeholder-cosmic-muted rounded-xl px-4 py-3
                     border border-cosmic-border focus:border-cosmic-accent focus:outline-none
                     resize-none min-h-[48px] max-h-[120px]
                     disabled:opacity-50 disabled:cursor-not-allowed"
        />

        <button
          onClick={handleSend}
          disabled={!message.trim() || sending || disabled}
          className="p-3 rounded-xl bg-cosmic-accent text-white
                     hover:bg-cosmic-accent/80 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
        >
          {/* Send icon */}
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
