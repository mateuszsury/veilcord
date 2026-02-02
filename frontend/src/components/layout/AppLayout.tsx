import { IconBar } from './IconBar';
import { ChannelList } from './ChannelList';
import { MainPanel } from './MainPanel';
import { UpdatePrompt } from './UpdatePrompt';
import { IncomingCallPopup } from '@/components/call/IncomingCallPopup';
import { ActiveCallOverlay } from '@/components/call/ActiveCallOverlay';

/**
 * Main application layout using CSS Grid three-column Discord-style structure.
 *
 * Layout columns:
 * - IconBar: 80px (--sidebar-icon-width) - primary navigation icons
 * - ChannelList: 240px (--sidebar-channel-width) - contacts/groups/settings list
 * - MainPanel: 1fr - main content area (chat, settings, etc.)
 *
 * Uses Discord dark theme background (bg-discord-bg-primary).
 *
 * Global components (UpdatePrompt, IncomingCallPopup, ActiveCallOverlay)
 * use fixed/absolute positioning and don't affect the grid layout.
 */
export function AppLayout() {
  return (
    <div className="grid grid-cols-discord h-screen w-screen overflow-hidden bg-discord-bg-primary">
      {/* Global overlays - use fixed/absolute positioning */}
      <UpdatePrompt />
      <IncomingCallPopup />
      <ActiveCallOverlay />

      {/* Three-column layout */}
      <IconBar />
      <ChannelList />
      <MainPanel />
    </div>
  );
}
