/**
 * Identity settings section.
 *
 * Displays and manages user's cryptographic identity:
 * - Display name (editable)
 * - Public key (copyable)
 * - Fingerprint (for verification)
 */

import { useState } from 'react';
import { useIdentityStore } from '@/stores/identity';
import { api } from '@/lib/pywebview';
import { Button } from '@/components/ui/Button';
import { Copy, Check, Edit2 } from 'lucide-react';

export function IdentitySection() {
  const identity = useIdentityStore((s) => s.identity);
  const setIdentity = useIdentityStore((s) => s.setIdentity);
  const [isEditingName, setIsEditingName] = useState(false);
  const [newName, setNewName] = useState('');
  const [copied, setCopied] = useState(false);

  const handleCopyPublicKey = async () => {
    if (identity?.publicKey) {
      await navigator.clipboard.writeText(identity.publicKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSaveName = async () => {
    if (newName.trim()) {
      await api.call((a) => a.update_display_name(newName.trim()));
      const updated = await api.call((a) => a.get_identity());
      setIdentity(updated);
      setIsEditingName(false);
    }
  };

  const handleGenerateIdentity = async () => {
    const newIdentity = await api.call((a) => a.generate_identity('Anonymous'));
    setIdentity(newIdentity);
  };

  // No identity yet - show generation prompt
  if (!identity) {
    return (
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary">
          My Account
        </h3>

        <div className="h-px bg-discord-bg-tertiary" />

        <div className="space-y-4">
          <p className="text-sm text-discord-text-muted">
            Generate your cryptographic identity to start using DiscordOpus.
            Your identity is stored locally and never shared with any server.
          </p>
          <Button onClick={handleGenerateIdentity}>
            Generate Identity
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary">
        My Account
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        {/* Display Name */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Display Name
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              This is how you appear to your contacts
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isEditingName ? (
              <>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="
                    bg-discord-bg-tertiary border border-discord-bg-modifier-active
                    rounded-md px-3 py-2 text-discord-text-primary
                    placeholder:text-discord-text-muted
                    focus:ring-2 focus:ring-accent-red focus:border-transparent
                    focus:outline-none
                  "
                  placeholder="Enter display name"
                  autoFocus
                />
                <Button size="sm" onClick={handleSaveName}>
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setIsEditingName(false)}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <span className="text-sm text-discord-text-primary">
                  {identity.displayName}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setNewName(identity.displayName);
                    setIsEditingName(true);
                  }}
                >
                  <Edit2 size={14} />
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Public Key */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <label className="text-sm font-medium text-discord-text-primary">
              Public Key
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Share this with others to let them add you as a contact
            </p>
            <code className="
              block mt-2 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-xs font-mono text-discord-text-primary
              overflow-x-auto whitespace-nowrap
            ">
              {identity.publicKey}
            </code>
          </div>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleCopyPublicKey}
            className="mt-6"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span className="ml-1">{copied ? 'Copied!' : 'Copy'}</span>
          </Button>
        </div>

        {/* Fingerprint */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <label className="text-sm font-medium text-discord-text-primary">
              Fingerprint
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Compare this with your contact in person to verify identity
            </p>
            <code className="
              block mt-2 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-sm font-mono text-discord-text-primary
            ">
              {identity.fingerprintFormatted || identity.fingerprint}
            </code>
          </div>
        </div>
      </div>
    </section>
  );
}
