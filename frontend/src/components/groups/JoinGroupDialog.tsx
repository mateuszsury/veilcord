/**
 * Dialog for joining a group via invite code.
 *
 * Accepts discordopus://join/... URLs or raw invite codes.
 */

import { useState } from 'react';
import { useGroupStore } from '@/stores/groups';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function JoinGroupDialog({ isOpen, onClose }: Props) {
  const [inviteCode, setInviteCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const joinGroup = useGroupStore((s) => s.joinGroup);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteCode.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await joinGroup(inviteCode.trim());
      setInviteCode('');
      onClose();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setInviteCode('');
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cosmic-surface rounded-lg p-6 w-96 max-w-[90vw] border border-cosmic-border">
        <h2 className="text-xl font-semibold text-cosmic-text mb-4">Join Group</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm text-cosmic-muted mb-1">Invite Code</label>
            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder="discordopus://join/... or paste code"
              className="w-full px-3 py-2 bg-cosmic-bg border border-cosmic-border rounded text-cosmic-text placeholder-cosmic-muted focus:outline-none focus:border-cosmic-accent font-mono text-sm"
              autoFocus
            />
            <p className="text-xs text-cosmic-muted mt-1">
              Paste the full invite link or just the code
            </p>
          </div>

          {error && (
            <p className="text-red-400 text-sm mb-4">{error}</p>
          )}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-cosmic-muted hover:text-cosmic-text transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !inviteCode.trim()}
              className="px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              {loading ? 'Joining...' : 'Join'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
