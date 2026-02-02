/**
 * Dialog for creating a new group.
 *
 * Allows users to enter a group name and creates the group via API.
 */

import { useState } from 'react';
import { useGroupStore } from '@/stores/groups';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateGroupDialog({ isOpen, onClose }: Props) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const createGroup = useGroupStore((s) => s.createGroup);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await createGroup(name.trim());
      setName('');
      onClose();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setName('');
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-discord-bg-secondary rounded-lg p-6 w-96 max-w-[90vw] border border-discord-bg-tertiary">
        <h2 className="text-xl font-semibold text-discord-text-primary mb-4">Create Group</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm text-discord-text-muted mb-1">Group Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter group name..."
              className="w-full px-3 py-2 bg-discord-bg-tertiary border border-discord-bg-modifier-active rounded text-discord-text-primary placeholder-discord-text-muted focus:outline-none focus:border-accent-red"
              maxLength={100}
              autoFocus
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm mb-4">{error}</p>
          )}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-discord-text-muted hover:text-discord-text-primary transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="px-4 py-2 bg-accent-red hover:bg-accent-red-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
