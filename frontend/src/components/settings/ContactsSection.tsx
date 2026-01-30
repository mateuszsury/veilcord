import { useState } from 'react';
import { motion } from 'framer-motion';
import { useContactsStore } from '@/stores/contacts';
import { api } from '@/lib/pywebview';

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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-cosmic-surface rounded-lg p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Contacts</h3>

      {/* Add Contact Form */}
      <div className="mb-6 p-4 bg-cosmic-bg rounded-lg">
        <h4 className="text-sm font-medium mb-3">Add Contact</h4>
        {error && (
          <div className="mb-3 p-2 bg-red-900/30 text-red-400 rounded text-sm">
            {error}
          </div>
        )}
        <div className="space-y-3">
          <input
            type="text"
            value={publicKey}
            onChange={(e) => setPublicKey(e.target.value)}
            placeholder="Paste contact's public key"
            className="w-full bg-cosmic-surface border border-cosmic-border rounded-md px-3 py-2 text-cosmic-text text-sm focus:outline-none focus:border-cosmic-accent"
          />
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name"
            className="w-full bg-cosmic-surface border border-cosmic-border rounded-md px-3 py-2 text-cosmic-text text-sm focus:outline-none focus:border-cosmic-accent"
          />
          <button
            onClick={handleAddContact}
            className="w-full px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent-hover text-white rounded-md text-sm"
          >
            Add Contact
          </button>
        </div>
      </div>

      {/* Contacts List */}
      <div>
        <h4 className="text-sm font-medium mb-3">
          Your Contacts ({contacts.length})
        </h4>
        {contacts.length === 0 ? (
          <p className="text-cosmic-muted text-sm">No contacts yet</p>
        ) : (
          <ul className="space-y-2">
            {contacts.map((contact) => (
              <li
                key={contact.id}
                className="p-3 bg-cosmic-bg rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium flex items-center gap-2">
                      {contact.displayName}
                      {contact.verified && (
                        <span className="text-xs bg-green-900/30 text-green-400 px-1.5 py-0.5 rounded">
                          Verified
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-cosmic-muted mt-1">
                      {contact.fingerprint.slice(0, 16)}...
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() =>
                        setShowFingerprint(
                          showFingerprint === contact.id ? null : contact.id
                        )
                      }
                      className="text-xs text-cosmic-muted hover:text-cosmic-text"
                    >
                      Verify
                    </button>
                    <button
                      onClick={() => handleRemoveContact(contact.id)}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </div>
                </div>

                {/* Fingerprint verification */}
                {showFingerprint === contact.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="mt-3 pt-3 border-t border-cosmic-border"
                  >
                    <p className="text-xs text-cosmic-muted mb-2">
                      Compare this fingerprint with your contact in person:
                    </p>
                    <code className="block bg-cosmic-surface p-2 rounded text-xs font-mono break-all">
                      {contact.fingerprintFormatted || contact.fingerprint}
                    </code>
                    <button
                      onClick={() => handleToggleVerified(contact.id, contact.verified)}
                      className={`mt-2 text-xs px-2 py-1 rounded ${
                        contact.verified
                          ? 'bg-red-900/30 text-red-400'
                          : 'bg-green-900/30 text-green-400'
                      }`}
                    >
                      {contact.verified ? 'Mark as Unverified' : 'Mark as Verified'}
                    </button>
                  </motion.div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </motion.div>
  );
}
