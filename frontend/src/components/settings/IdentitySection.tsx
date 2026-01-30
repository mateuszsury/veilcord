import { useState } from 'react';
import { motion } from 'framer-motion';
import { useIdentityStore } from '@/stores/identity';
import { api } from '@/lib/pywebview';

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

  if (!identity) {
    return (
      <div className="bg-cosmic-surface rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Identity</h3>
        <p className="text-cosmic-muted mb-4">
          Generate your cryptographic identity to start using DiscordOpus.
        </p>
        <button
          onClick={handleGenerateIdentity}
          className="px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent-hover text-white rounded-md transition-colors"
        >
          Generate Identity
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-cosmic-surface rounded-lg p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Your Identity</h3>

      {/* Display Name */}
      <div className="mb-4">
        <label className="block text-sm text-cosmic-muted mb-1">Display Name</label>
        {isEditingName ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="flex-1 bg-cosmic-bg border border-cosmic-border rounded-md px-3 py-2 text-cosmic-text focus:outline-none focus:border-cosmic-accent"
              placeholder="Enter display name"
              autoFocus
            />
            <button
              onClick={handleSaveName}
              className="px-3 py-2 bg-cosmic-accent hover:bg-cosmic-accent-hover text-white rounded-md"
            >
              Save
            </button>
            <button
              onClick={() => setIsEditingName(false)}
              className="px-3 py-2 bg-cosmic-border hover:bg-cosmic-muted/20 rounded-md"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-cosmic-text">{identity.displayName}</span>
            <button
              onClick={() => {
                setNewName(identity.displayName);
                setIsEditingName(true);
              }}
              className="text-xs text-cosmic-muted hover:text-cosmic-accent"
            >
              Edit
            </button>
          </div>
        )}
      </div>

      {/* Public Key */}
      <div className="mb-4">
        <label className="block text-sm text-cosmic-muted mb-1">Public Key (Share this)</label>
        <div className="flex items-center gap-2">
          <code className="flex-1 bg-cosmic-bg border border-cosmic-border rounded-md px-3 py-2 text-xs font-mono text-cosmic-text overflow-x-auto">
            {identity.publicKey}
          </code>
          <button
            onClick={handleCopyPublicKey}
            className="px-3 py-2 bg-cosmic-border hover:bg-cosmic-muted/20 rounded-md text-sm"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Fingerprint */}
      <div>
        <label className="block text-sm text-cosmic-muted mb-1">Fingerprint (For verification)</label>
        <code className="block bg-cosmic-bg border border-cosmic-border rounded-md px-3 py-2 text-sm font-mono text-cosmic-text">
          {identity.fingerprintFormatted || identity.fingerprint}
        </code>
        <p className="text-xs text-cosmic-muted mt-1">
          Compare this with your contact in person to verify identity
        </p>
      </div>
    </motion.div>
  );
}
