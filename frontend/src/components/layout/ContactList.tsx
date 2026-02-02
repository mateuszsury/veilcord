/**
 * ContactList - Contact list for the contacts section
 *
 * Displays all contacts with:
 * - Avatar with online status indicator
 * - Display name
 * - Fingerprint snippet
 * - Selection highlight (red accent when selected)
 *
 * Integrates with contactsStore for data and uiStore for selection.
 */

import { useContactsStore } from '@/stores/contacts';
import { useUIStore } from '@/stores/ui';
import { Avatar } from '@/components/ui/Avatar';
import type { StatusType } from '@/components/ui/Badge';
import type { UserStatus } from '@/lib/pywebview';

/**
 * Maps backend UserStatus to UI StatusType.
 * StatusBadge only supports: online, away, busy, offline
 */
function mapUserStatusToStatusType(status: UserStatus): StatusType {
  switch (status) {
    case 'online':
      return 'online';
    case 'away':
      return 'away';
    case 'busy':
      return 'busy';
    case 'invisible':
    case 'offline':
    case 'unknown':
    default:
      return 'offline';
  }
}

export function ContactList() {
  const contacts = useContactsStore((s) => s.contacts);
  const selectedContactId = useUIStore((s) => s.selectedContactId);
  const setSelectedContact = useUIStore((s) => s.setSelectedContact);
  const setActivePanel = useUIStore((s) => s.setActivePanel);

  const handleContactClick = (contactId: number) => {
    setSelectedContact(contactId);
    setActivePanel('chat');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 pb-2">
        <h2 className="text-xs uppercase text-discord-text-muted tracking-wide font-semibold">
          Contacts
        </h2>
      </div>

      {/* Contact list */}
      <div className="flex-1 overflow-y-auto px-2">
        {contacts.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-discord-text-muted text-center px-4">
              No contacts yet.
              <br />
              Add someone to start chatting.
            </p>
          </div>
        ) : (
          <ul className="space-y-0.5">
            {contacts.map((contact) => {
              const isSelected = selectedContactId === contact.id;
              const statusType = mapUserStatusToStatusType(contact.onlineStatus);

              return (
                <li key={contact.id}>
                  <button
                    onClick={() => handleContactClick(contact.id)}
                    className={`
                      w-full text-left px-2 py-2 rounded-lg transition-colors
                      flex items-center gap-3
                      ${
                        isSelected
                          ? 'bg-accent-red/20 text-accent-red-text'
                          : 'hover:bg-discord-bg-modifier-hover text-discord-text-primary'
                      }
                    `.trim().replace(/\s+/g, ' ')}
                  >
                    <Avatar
                      name={contact.displayName}
                      size="sm"
                      status={statusType}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {contact.displayName}
                      </div>
                      <div className="text-xs text-discord-text-muted truncate">
                        {contact.fingerprint.slice(0, 16)}...
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
