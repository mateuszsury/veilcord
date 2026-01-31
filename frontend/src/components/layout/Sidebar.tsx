import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { useUIStore } from '@/stores/ui';
import { useNetworkStore } from '@/stores/network';
import { useGroupStore } from '@/stores/groups';
import { StatusSelector } from './StatusSelector';
import { ConnectionIndicator } from './ConnectionIndicator';
import { CreateGroupDialog, JoinGroupDialog } from '@/components/groups';
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
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);

  const contacts = useContactsStore((s) => s.contacts);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const setSelectedContact = useUIStore((s) => s.setSelectedContact);
  const setSelectedGroup = useUIStore((s) => s.setSelectedGroup);
  const setActivePanel = useUIStore((s) => s.setActivePanel);
  const loadNetworkState = useNetworkStore((s) => s.loadInitialState);

  const groups = useGroupStore((s) => s.groups);
  const loadGroups = useGroupStore((s) => s.loadGroups);

  // Initialize network store and groups on mount
  useEffect(() => {
    loadNetworkState();
    loadGroups();
  }, [loadNetworkState, loadGroups]);

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

      {/* Contacts and Groups list */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Contacts Section */}
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

        {/* Groups Section */}
        <div className="mt-6">
          <div className="flex items-center justify-between px-2 mb-2">
            <span className="text-xs uppercase text-cosmic-muted">Groups</span>
            <div className="flex gap-1">
              <button
                onClick={() => setShowJoinGroup(true)}
                className="p-1 text-cosmic-muted hover:text-cosmic-text transition-colors"
                title="Join group"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
              </button>
              <button
                onClick={() => setShowCreateGroup(true)}
                className="p-1 text-cosmic-muted hover:text-cosmic-text transition-colors"
                title="Create group"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          </div>

          <div className="space-y-1">
            {groups.map((group) => (
              <button
                key={group.id}
                onClick={() => {
                  setSelectedGroup(group.id);
                  setActivePanel('chat');
                }}
                className={`w-full flex items-center gap-3 px-2 py-2 rounded-lg transition-colors ${
                  selectedGroupId === group.id
                    ? 'bg-cosmic-accent/20 text-cosmic-accent'
                    : 'text-cosmic-text hover:bg-cosmic-border'
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-cosmic-accent/50 flex items-center justify-center text-sm font-medium">
                  {group.name.charAt(0).toUpperCase()}
                </div>
                <span className="truncate">{group.name}</span>
              </button>
            ))}

            {groups.length === 0 && (
              <p className="text-sm text-cosmic-muted px-2 py-4 text-center">
                No groups yet. Create or join one!
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Group Dialogs */}
      <CreateGroupDialog isOpen={showCreateGroup} onClose={() => setShowCreateGroup(false)} />
      <JoinGroupDialog isOpen={showJoinGroup} onClose={() => setShowJoinGroup(false)} />

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
