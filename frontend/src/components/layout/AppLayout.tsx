import { Sidebar } from './Sidebar';
import { MainPanel } from './MainPanel';
import { UpdatePrompt } from './UpdatePrompt';
import { IncomingCallPopup } from '@/components/call/IncomingCallPopup';
import { ActiveCallOverlay } from '@/components/call/ActiveCallOverlay';

/**
 * Main application layout with sidebar and main panel.
 *
 * Uses Discord dark theme background (bg-discord-bg-primary).
 *
 * Global components (UpdatePrompt, IncomingCallPopup, ActiveCallOverlay)
 * are rendered here so they appear regardless of which panel is active.
 */
export function AppLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-discord-bg-primary">
      <UpdatePrompt />
      <Sidebar />
      <MainPanel />
      <IncomingCallPopup />
      <ActiveCallOverlay />
    </div>
  );
}
