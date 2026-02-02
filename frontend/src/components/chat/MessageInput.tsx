/**
 * Discord-style message input component with integrated buttons.
 *
 * Features:
 * - Multi-line input with auto-resize
 * - Send on Enter (Shift+Enter for newline)
 * - Typing indicator support
 * - Disabled state when not connected
 * - Integrated file upload and voice recording buttons
 */

import { useState, useRef, type KeyboardEvent, type ReactNode } from 'react';
import { api } from '@/lib/pywebview';
import { Send, Mic } from 'lucide-react';

interface MessageInputProps {
  contactId: number;
  contactName?: string;
  onSend: (body: string) => Promise<boolean>;
  disabled?: boolean;
  placeholder?: string;
  onStartRecording?: () => void;
  fileUploadSlot?: ReactNode;
}

export function MessageInput({
  contactId,
  contactName,
  onSend,
  disabled = false,
  placeholder,
  onStartRecording,
  fileUploadSlot,
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

  const defaultPlaceholder = contactName
    ? `Message ${contactName}...`
    : 'Type a message...';

  const effectivePlaceholder = disabled
    ? 'Connect to send messages'
    : placeholder || defaultPlaceholder;

  const canSend = message.trim() && !sending && !disabled;

  return (
    <div className="flex items-center gap-2 bg-discord-bg-tertiary rounded-lg px-2">
      {/* File upload slot */}
      {fileUploadSlot}

      {/* Voice recording button */}
      {onStartRecording && (
        <button
          type="button"
          onClick={onStartRecording}
          disabled={disabled}
          className="p-2 text-discord-text-muted hover:text-discord-text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Record voice message"
        >
          <Mic className="w-5 h-5" />
        </button>
      )}

      {/* Divider */}
      {(fileUploadSlot || onStartRecording) && (
        <div className="w-px h-6 bg-discord-bg-modifier-hover" />
      )}

      {/* Text input */}
      <textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => {
          handleChange(e.target.value);
          handleInput();
        }}
        onKeyDown={handleKeyDown}
        placeholder={effectivePlaceholder}
        disabled={disabled || sending}
        rows={1}
        className="flex-1 bg-transparent text-discord-text-primary placeholder:text-discord-text-muted
                   outline-none py-3 resize-none min-h-[48px] max-h-[120px]"
      />

      {/* Send button */}
      <button
        type="button"
        onClick={handleSend}
        disabled={!canSend}
        className={`p-2 transition-all ${
          canSend
            ? 'text-accent-red hover:scale-105'
            : 'text-discord-text-muted opacity-50 cursor-not-allowed'
        }`}
        title="Send message"
      >
        <Send className="w-5 h-5" />
      </button>
    </div>
  );
}
