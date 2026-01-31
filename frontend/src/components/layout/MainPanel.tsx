import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useUIStore } from '@/stores/ui';
import { useChat } from '@/stores/chat';
import { useGroupStore } from '@/stores/groups';
import { SettingsPanel } from '@/components/settings/SettingsPanel';
import { ChatPanel } from '@/components/chat/ChatPanel';

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
    <motion.main
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex-1 h-full bg-cosmic-bg flex flex-col overflow-hidden"
    >
      {activePanel === 'settings' ? (
        <div className="flex-1 overflow-y-auto">
          <SettingsPanel />
        </div>
      ) : (
        <ChatPanel />
      )}
    </motion.main>
  );
}
