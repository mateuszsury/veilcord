/**
 * ChannelList - Secondary navigation panel (240px width)
 *
 * Switches content based on active section:
 * - home: HomePanel (welcome/branding)
 * - contacts: ContactList (list of contacts)
 * - groups: GroupList (list of groups)
 * - settings: placeholder
 *
 * Uses AnimatePresence for smooth slide transitions between panels.
 */

import { AnimatePresence, motion } from 'framer-motion';
import { useUIStore } from '@/stores/ui';
import { ContactList } from './ContactList';
import { GroupList } from './GroupList';
import { HomePanel } from './HomePanel';

const slideVariants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};

const slideTransition = {
  duration: 0.15,
  ease: [0.3, 0, 0, 1] as const,
};

export function ChannelList() {
  const activeSection = useUIStore((s) => s.activeSection);

  const renderContent = () => {
    switch (activeSection) {
      case 'home':
        return <HomePanel key="home" />;
      case 'contacts':
        return <ContactList key="contacts" />;
      case 'groups':
        return <GroupList key="groups" />;
      case 'settings':
        return (
          <div key="settings" className="p-4 text-discord-text-muted">
            Settings
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <aside className="w-60 h-full bg-discord-bg-secondary border-r border-discord-bg-tertiary flex flex-col overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={activeSection}
          variants={slideVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={slideTransition}
          className="flex-1 overflow-y-auto"
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>
    </aside>
  );
}
