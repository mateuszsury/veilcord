import { motion } from 'framer-motion';
import { useUIStore } from '@/stores/ui';
import { useContactsStore } from '@/stores/contacts';

export function MainPanel() {
  const activePanel = useUIStore((s) => s.activePanel);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const contacts = useContactsStore((s) => s.contacts);

  const selectedContact = contacts.find((c) => c.id === selectedContactId);

  return (
    <motion.main
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex-1 h-full bg-cosmic-bg flex flex-col overflow-hidden"
    >
      {activePanel === 'settings' ? (
        <div className="flex-1 p-6">
          <h2 className="text-xl font-semibold mb-4">Settings</h2>
          <p className="text-cosmic-muted">
            Settings panel will be implemented in the next plan.
          </p>
        </div>
      ) : selectedContact ? (
        <div className="flex-1 flex flex-col">
          {/* Chat header */}
          <div className="p-4 border-b border-cosmic-border">
            <h2 className="font-semibold">{selectedContact.displayName}</h2>
            <p className="text-xs text-cosmic-muted">
              {selectedContact.verified ? 'Verified' : 'Unverified'}
            </p>
          </div>
          {/* Chat messages - placeholder */}
          <div className="flex-1 p-4 overflow-y-auto">
            <p className="text-cosmic-muted text-center py-8">
              Chat functionality coming in Phase 3
            </p>
          </div>
          {/* Message input - placeholder */}
          <div className="p-4 border-t border-cosmic-border">
            <div className="bg-cosmic-surface rounded-lg p-3 text-cosmic-muted">
              Message input coming in Phase 3...
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-cosmic-muted">
          <div className="text-center">
            <p className="text-lg">Select a contact to start chatting</p>
            <p className="text-sm mt-2">Or add a new contact in Settings</p>
          </div>
        </div>
      )}
    </motion.main>
  );
}
