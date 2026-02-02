import { useEffect } from 'react';
import { useUIStore } from '@/stores/ui';
import { useChat } from '@/stores/chat';
import { useGroupStore } from '@/stores/groups';
import { SettingsPanel } from '@/components/settings/SettingsPanel';
import { ChatPanel } from '@/components/chat/ChatPanel';

/**
 * MainPanel - Primary content area in the CSS Grid layout.
 *
 * Fills the third column (1fr) of the grid layout.
 * Displays ChatPanel or SettingsPanel based on activePanel state.
 *
 * Uses Discord dark theme background (bg-discord-bg-primary).
 * Content components handle their own scrolling.
 */
export function MainPanel() {
  const activePanel = useUIStore((s) => s.activePanel);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const setActiveContact = useChat((s) => s.setActiveContact);
  const selectGroup = useGroupStore((s) => s.selectGroup);

  // Sync selected contact ID to chat store
  useEffect(() => {
    setActiveContact(selectedContactId);
  }, [selectedContactId, setActiveContact]);

  // Sync selected group ID to groups store
  useEffect(() => {
    selectGroup(selectedGroupId);
  }, [selectedGroupId, selectGroup]);

  return (
    <main className="h-full bg-discord-bg-primary overflow-hidden">
      {activePanel === 'settings' ? <SettingsPanel /> : <ChatPanel />}
    </main>
  );
}
