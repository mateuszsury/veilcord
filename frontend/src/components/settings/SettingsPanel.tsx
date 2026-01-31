import { motion } from 'framer-motion';
import { IdentitySection } from './IdentitySection';
import { NetworkSection } from './NetworkSection';
import { BackupSection } from './BackupSection';
import { ContactsSection } from './ContactsSection';
import { AudioSection } from './AudioSection';
import { VideoSection } from './VideoSection';

export function SettingsPanel() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 max-w-2xl mx-auto space-y-6"
    >
      <h2 className="text-2xl font-semibold">Settings</h2>

      <IdentitySection />
      <NetworkSection />
      <AudioSection />
      <VideoSection />
      <BackupSection />
      <ContactsSection />
    </motion.div>
  );
}
