import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { useUIStore } from '@/stores/ui';
import { useNetworkStore } from '@/stores/network';
import { StatusSelector } from './StatusSelector';
import { ConnectionIndicator } from './ConnectionIndicator';
import type { UserStatus } from '@/lib/pywebview';

function getStatusDotColor(status: UserStatus): string {
  switch (status) {
    case 'online':
      return 'bg-green-500';
    case 'away':
      return 'bg-yellow-500';
    case 'busy':
      return 'bg-red-500';
    case 'invisible':
      return 'bg-gray-500';
    case 'offline':
    case 'unknown':
    default:
      return 'bg-gray-600';
  }
}

export function Sidebar() {
  const contacts = useContactsStore((s) => s.contacts);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const setSelectedContact = useUIStore((s) => s.setSelectedContact);
  const setActivePanel = useUIStore((s) => s.setActivePanel);
  const loadNetworkState = useNetworkStore((s) => s.loadInitialState);

  // Initialize network store on mount
  useEffect(() => {
    loadNetworkState();
  }, [loadNetworkState]);

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-full bg-cosmic-surface border-r border-cosmic-border flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-cosmic-border">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-lg font-semibold text-cosmic-text">DiscordOpus</h1>
        </div>
        <p className="text-xs text-cosmic-muted mb-2">Secure P2P Messenger</p>
        <StatusSelector />
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
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDotColor(contact.onlineStatus)}`}
                      title={contact.onlineStatus}
                    />
                    <span className="font-medium truncate">{contact.displayName}</span>
                  </div>
                  <div className="text-xs text-cosmic-muted truncate pl-4">
                    {contact.fingerprint.slice(0, 16)}...
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer with connection status and settings */}
      <div className="p-2 border-t border-cosmic-border">
        <ConnectionIndicator />
        <button
          onClick={() => setActivePanel('settings')}
          className="w-full px-3 py-2 text-left text-sm text-cosmic-muted hover:text-cosmic-text hover:bg-cosmic-border rounded-md transition-colors mt-1"
        >
          Settings
        </button>
      </div>
    </motion.aside>
  );
}
