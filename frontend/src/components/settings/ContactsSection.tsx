/**
 * Contacts settings section.
 *
 * Manage contacts: add, remove, and verify contacts.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { api } from '@/lib/pywebview';
import { Button } from '@/components/ui/Button';
import { Users, Trash2, Shield, ShieldCheck } from 'lucide-react';

export function ContactsSection() {
  const contacts = useContactsStore((s) => s.contacts);
  const addContact = useContactsStore((s) => s.addContact);
  const removeContact = useContactsStore((s) => s.removeContact);
  const updateContact = useContactsStore((s) => s.updateContact);

  const [publicKey, setPublicKey] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showFingerprint, setShowFingerprint] = useState<number | null>(null);

  const handleAddContact = async () => {
    setError(null);

    if (!publicKey.trim()) {
      setError('Please enter a public key');
      return;
    }
    if (!displayName.trim()) {
      setError('Please enter a display name');
      return;
    }

    try {
      const contact = await api.call((a) =>
        a.add_contact(publicKey.trim(), displayName.trim())
      );
      addContact(contact);
      setPublicKey('');
      setDisplayName('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add contact');
    }
  };

  const handleRemoveContact = async (id: number) => {
    await api.call((a) => a.remove_contact(id));
    removeContact(id);
  };

  const handleToggleVerified = async (id: number, currentVerified: boolean) => {
    await api.call((a) => a.set_contact_verified(id, !currentVerified));
    updateContact(id, { verified: !currentVerified });
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Users size={20} />
        Contacts
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      {/* Add Contact Form */}
      <div className="p-4 bg-discord-bg-tertiary rounded-lg border border-discord-bg-modifier-active">
        <h4 className="text-sm font-medium text-discord-text-primary mb-3">Add Contact</h4>
        {error && (
          <div className="mb-3 p-2 bg-status-busy/10 text-status-busy border border-status-busy/30 rounded text-sm">
            {error}
          </div>
        )}
        <div className="space-y-3">
          <input
            type="text"
            value={publicKey}
            onChange={(e) => setPublicKey(e.target.value)}
            placeholder="Paste contact's public key"
            className="
              w-full bg-discord-bg-secondary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary text-sm
              placeholder:text-discord-text-muted
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
            "
          />
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name"
            className="
              w-full bg-discord-bg-secondary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary text-sm
              placeholder:text-discord-text-muted
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
            "
          />
          <Button onClick={handleAddContact} className="w-full">
            Add Contact
          </Button>
        </div>
      </div>

      {/* Contacts List */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-discord-text-primary">
          Your Contacts ({contacts.length})
        </h4>
        {contacts.length === 0 ? (
          <p className="text-discord-text-muted text-sm">No contacts yet</p>
        ) : (
          <ul className="space-y-2">
            {contacts.map((contact) => (
              <li
                key={contact.id}
                className="p-3 bg-discord-bg-tertiary rounded-lg border border-discord-bg-modifier-active"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-discord-text-primary flex items-center gap-2">
                      {contact.displayName}
                      {contact.verified && (
                        <span className="text-xs bg-status-online/20 text-status-online px-1.5 py-0.5 rounded flex items-center gap-1">
                          <ShieldCheck size={10} />
                          Verified
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-discord-text-muted mt-1 font-mono">
                      {contact.fingerprint.slice(0, 16)}...
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        setShowFingerprint(
                          showFingerprint === contact.id ? null : contact.id
                        )
                      }
                    >
                      <Shield size={14} />
                      <span className="ml-1">Verify</span>
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRemoveContact(contact.id)}
                      className="text-status-busy hover:text-status-busy"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>

                {/* Fingerprint verification */}
                {showFingerprint === contact.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="mt-3 pt-3 border-t border-discord-bg-modifier-active"
                  >
                    <p className="text-xs text-discord-text-muted mb-2">
                      Compare this fingerprint with your contact in person:
                    </p>
                    <code className="block bg-discord-bg-secondary p-2 rounded text-xs font-mono text-discord-text-primary break-all border border-discord-bg-modifier-active">
                      {contact.fingerprintFormatted || contact.fingerprint}
                    </code>
                    <Button
                      size="sm"
                      variant={contact.verified ? 'danger' : 'secondary'}
                      onClick={() => handleToggleVerified(contact.id, contact.verified)}
                      className="mt-2"
                    >
                      {contact.verified ? 'Mark as Unverified' : 'Mark as Verified'}
                    </Button>
                  </motion.div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </motion.section>
  );
}
