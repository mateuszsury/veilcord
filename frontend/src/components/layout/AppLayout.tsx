import { Sidebar } from './Sidebar';
import { MainPanel } from './MainPanel';

/**
 * Main application layout with sidebar and main panel.
 *
 * The starry-bg class applies the cosmic starfield background
 * defined in index.css.
 */
export function AppLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden starry-bg">
      <Sidebar />
      <MainPanel />
    </div>
  );
}
