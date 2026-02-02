/**
 * Settings panel with Discord-style two-column layout.
 *
 * Left column: SettingsNav for category navigation
 * Right column: Content panel showing active category settings
 */

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { SettingsNav } from './SettingsNav';
import { IdentitySection } from './IdentitySection';
import { NetworkSection } from './NetworkSection';
import { DiscoverySection } from './DiscoverySection';
import { BackupSection } from './BackupSection';
import { ContactsSection } from './ContactsSection';
import { AudioSection } from './AudioSection';
import { VideoSection } from './VideoSection';
import { NotificationSection } from './NotificationSection';
import { DangerZoneSection } from './DangerZoneSection';

export function SettingsPanel() {
  const [activeCategory, setActiveCategory] = useState('identity');

  const renderSection = () => {
    switch (activeCategory) {
      case 'identity':
        return <IdentitySection />;
      case 'network':
        return <NetworkSection />;
      case 'discovery':
        return <DiscoverySection />;
      case 'audio':
        return <AudioSection />;
      case 'video':
        return <VideoSection />;
      case 'notifications':
        return <NotificationSection />;
      case 'backup':
        return <BackupSection />;
      case 'contacts':
        return <ContactsSection />;
      case 'danger':
        return <DangerZoneSection />;
      default:
        return <IdentitySection />;
    }
  };

  return (
    <div className="flex h-full bg-discord-bg-primary">
      {/* Left navigation */}
      <SettingsNav
        activeCategory={activeCategory}
        onCategoryChange={setActiveCategory}
      />

      {/* Right content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeCategory}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {renderSection()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
