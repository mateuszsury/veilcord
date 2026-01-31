import { Sidebar } from './Sidebar';
import { MainPanel } from './MainPanel';
import { UpdatePrompt } from './UpdatePrompt';
import { IncomingCallPopup } from '@/components/call/IncomingCallPopup';
import { ActiveCallOverlay } from '@/components/call/ActiveCallOverlay';

/**
 * Main application layout with sidebar and main panel.
 *
 * The starry-bg class applies the cosmic starfield background
 * defined in index.css.
 *
 * Global components (UpdatePrompt, IncomingCallPopup, ActiveCallOverlay)
 * are rendered here so they appear regardless of which panel is active.
 */
export function AppLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden starry-bg">
      <UpdatePrompt />
      <Sidebar />
      <MainPanel />
      <IncomingCallPopup />
      <ActiveCallOverlay />
    </div>
  );
}
