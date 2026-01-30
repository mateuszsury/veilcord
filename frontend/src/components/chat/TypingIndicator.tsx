/**
 * Typing indicator component with animated bouncing dots.
 *
 * Shows when a contact is currently typing a message.
 */

interface TypingIndicatorProps {
  displayName?: string;
}

export function TypingIndicator({ displayName }: TypingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-cosmic-muted text-sm">
      <div className="flex items-center gap-1">
        <span
          className="w-2 h-2 bg-cosmic-muted rounded-full animate-bounce"
          style={{ animationDelay: '0ms', animationDuration: '600ms' }}
        />
        <span
          className="w-2 h-2 bg-cosmic-muted rounded-full animate-bounce"
          style={{ animationDelay: '150ms', animationDuration: '600ms' }}
        />
        <span
          className="w-2 h-2 bg-cosmic-muted rounded-full animate-bounce"
          style={{ animationDelay: '300ms', animationDuration: '600ms' }}
        />
      </div>
      <span className="opacity-70">
        {displayName ? `${displayName} is typing...` : 'Typing...'}
      </span>
    </div>
  );
}
