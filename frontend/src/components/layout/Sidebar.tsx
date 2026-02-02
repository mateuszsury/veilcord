import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { useUIStore } from '@/stores/ui';
import { useNetworkStore } from '@/stores/network';
import { useGroupStore } from '@/stores/groups';
import { useDiscoveryStore } from '@/stores/discovery';
import { StatusSelector } from './StatusSelector';
import { ConnectionIndicator } from './ConnectionIndicator';
import { CreateGroupDialog, JoinGroupDialog } from '@/components/groups';
import { api } from '@/lib/pywebview';
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

  const discoveryEnabled = useDiscoveryStore((s) => s.enabled);
  const discoveredUsers = useDiscoveryStore((s) => s.users);
  const loadDiscoveryState = useDiscoveryStore((s) => s.loadState);

  const setContacts = useContactsStore((s) => s.setContacts);

  const [addingUser, setAddingUser] = useState<string | null>(null);

  // Initialize network store, groups, and discovery on mount
  useEffect(() => {
    loadNetworkState();
    loadGroups();
    loadDiscoveryState();
  }, [loadNetworkState, loadGroups, loadDiscoveryState]);

  const handleAddDiscoveredUser = async (publicKey: string, displayName: string) => {
    setAddingUser(publicKey);
    try {
      await api.call((a) => a.add_contact(publicKey, displayName));
      const contacts = await api.call((a) => a.get_contacts());
      setContacts(contacts);
    } catch (e) {
      console.error('Failed to add contact:', e);
    } finally {
      setAddingUser(null);
    }
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-full bg-discord-bg-secondary border-r border-discord-bg-tertiary flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-discord-bg-tertiary">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-lg font-semibold text-discord-text-primary">DiscordOpus</h1>
        </div>
        <p className="text-xs text-discord-text-muted mb-2">Secure P2P Messenger</p>
        <StatusSelector />
      </div>

      {/* Contacts and Groups list */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Contacts Section */}
        <div className="text-xs uppercase text-discord-text-muted px-2 py-1 mb-1">
          Contacts
        </div>
        {contacts.length === 0 ? (
          <p className="text-sm text-discord-text-muted px-2 py-4 text-center">
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
                      ? 'bg-accent-red/20 text-accent-red-text'
                      : 'hover:bg-discord-bg-modifier-hover text-discord-text-primary'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDotColor(contact.onlineStatus)}`}
                      title={contact.onlineStatus}
                    />
                    <span className="font-medium truncate">{contact.displayName}</span>
                  </div>
                  <div className="text-xs text-discord-text-muted truncate pl-4">
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
            <span className="text-xs uppercase text-discord-text-muted">Groups</span>
            <div className="flex gap-1">
              <button
                onClick={() => setShowJoinGroup(true)}
                className="p-1 text-discord-text-muted hover:text-discord-text-primary transition-colors"
                title="Join group"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
              </button>
              <button
                onClick={() => setShowCreateGroup(true)}
                className="p-1 text-discord-text-muted hover:text-discord-text-primary transition-colors"
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
                    ? 'bg-accent-red/20 text-accent-red-text'
                    : 'text-discord-text-primary hover:bg-discord-bg-modifier-hover'
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-accent-red/50 flex items-center justify-center text-sm font-medium">
                  {group.name.charAt(0).toUpperCase()}
                </div>
                <span className="truncate">{group.name}</span>
              </button>
            ))}

            {groups.length === 0 && (
              <p className="text-sm text-discord-text-muted px-2 py-4 text-center">
                No groups yet. Create or join one!
              </p>
            )}
          </div>
        </div>

        {/* Discovery Section - only show if enabled */}
        {discoveryEnabled && (
          <div className="mt-6">
            <div className="flex items-center justify-between px-2 mb-2">
              <span className="text-xs uppercase text-discord-text-muted">Discovery</span>
              <span className="text-xs text-green-400">
                {discoveredUsers.length} online
              </span>
            </div>

            <div className="space-y-1">
              {discoveredUsers.map((user) => {
                const isAlreadyContact = contacts.some(
                  (c) => c.publicKey === user.publicKey || user.publicKey.includes(c.publicKey) || c.publicKey.includes(user.publicKey)
                );
                const isAdding = addingUser === user.publicKey;

                return (
                  <div
                    key={user.publicKey}
                    className="flex items-center justify-between px-2 py-2 rounded-lg hover:bg-discord-bg-modifier-hover transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDotColor(user.status)}`}
                      />
                      <span className="text-sm text-discord-text-primary truncate">
                        {user.displayName}
                      </span>
                    </div>
                    {isAlreadyContact ? (
                      <span className="text-xs text-discord-text-muted">Added</span>
                    ) : (
                      <button
                        onClick={() => handleAddDiscoveredUser(user.publicKey, user.displayName)}
                        disabled={isAdding}
                        className="text-xs px-2 py-1 bg-accent-red/20 text-accent-red-text rounded hover:bg-accent-red/30 disabled:opacity-50 transition-colors"
                      >
                        {isAdding ? '...' : 'Add'}
                      </button>
                    )}
                  </div>
                );
              })}

              {discoveredUsers.length === 0 && (
                <p className="text-sm text-discord-text-muted px-2 py-4 text-center">
                  No users discovered yet
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Group Dialogs */}
      <CreateGroupDialog isOpen={showCreateGroup} onClose={() => setShowCreateGroup(false)} />
      <JoinGroupDialog isOpen={showJoinGroup} onClose={() => setShowJoinGroup(false)} />

      {/* Footer with connection status and settings */}
      <div className="p-2 border-t border-discord-bg-tertiary">
        <ConnectionIndicator />
        <button
          onClick={() => setActivePanel('settings')}
          className="w-full px-3 py-2 text-left text-sm text-discord-text-muted hover:text-discord-text-primary hover:bg-discord-bg-modifier-hover rounded-md transition-colors mt-1"
        >
          Settings
        </button>
      </div>
    </motion.aside>
  );
}
