/**
 * HomePanel - Welcome panel for the home section
 *
 * Displays:
 * - App branding (DiscordOpus)
 * - Tagline (Secure P2P Messenger)
 * - Welcome message with instructions
 *
 * This is the default view when no specific section is active.
 */

export function HomePanel() {
  return (
    <div className="flex flex-col h-full">
      {/* Header with branding */}
      <div className="p-4 border-b border-discord-bg-tertiary">
        <h1 className="text-lg font-semibold text-discord-text-primary">
          DiscordOpus
        </h1>
        <p className="text-xs text-discord-text-muted">
          Secure P2P Messenger
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center max-w-xs">
          <p className="text-discord-text-secondary mb-2">
            Welcome to DiscordOpus
          </p>
          <p className="text-sm text-discord-text-muted leading-relaxed">
            Select a contact or group from the sidebar to start a secure,
            end-to-end encrypted conversation.
          </p>
        </div>
      </div>
    </div>
  );
}
