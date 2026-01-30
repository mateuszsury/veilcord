import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { useUIStore } from '@/stores/ui';

export function Sidebar() {
  const contacts = useContactsStore((s) => s.contacts);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const setSelectedContact = useUIStore((s) => s.setSelectedContact);
  const setActivePanel = useUIStore((s) => s.setActivePanel);

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-full bg-cosmic-surface border-r border-cosmic-border flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-cosmic-border">
        <h1 className="text-lg font-semibold text-cosmic-text">DiscordOpus</h1>
        <p className="text-xs text-cosmic-muted">Secure P2P Messenger</p>
      </div>

      {/* Contacts list */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="text-xs uppercase text-cosmic-muted px-2 py-1 mb-1">
          Contacts
        </div>
        {contacts.length === 0 ? (
          <p className="text-sm text-cosmic-muted px-2 py-4 text-center">
            No contacts yet
          </p>
        ) : (
          <ul className="space-y-1">
            {contacts.map((contact) => (
              <li key={contact.id}>
                <button
                  onClick={() => {
                    setSelectedContact(contact.id);
                    setActivePanel('chat');
                  }}
                  className={`w-full text-left px-2 py-2 rounded-md transition-colors ${
                    selectedContactId === contact.id
                      ? 'bg-cosmic-accent/20 text-cosmic-accent'
                      : 'hover:bg-cosmic-border text-cosmic-text'
                  }`}
                >
                  <div className="font-medium truncate">{contact.displayName}</div>
                  <div className="text-xs text-cosmic-muted truncate">
                    {contact.fingerprint.slice(0, 16)}...
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer with settings */}
      <div className="p-2 border-t border-cosmic-border">
        <button
          onClick={() => setActivePanel('settings')}
          className="w-full px-3 py-2 text-left text-sm text-cosmic-muted hover:text-cosmic-text hover:bg-cosmic-border rounded-md transition-colors"
        >
          Settings
        </button>
      </div>
    </motion.aside>
  );
}
