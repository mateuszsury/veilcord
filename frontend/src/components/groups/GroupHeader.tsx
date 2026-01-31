/**
 * Group header component.
 *
 * Displays:
 * - Group avatar and name
 * - Member count
 * - Invite button (admin only)
 * - Leave button
 * - Invite code modal
 */

import { useState } from 'react';
import { useGroupStore } from '@/stores/groups';
import { useIdentityStore } from '@/stores/identity';

interface Props {
  groupId: string;
}

export function GroupHeader({ groupId }: Props) {
  const [showInvite, setShowInvite] = useState(false);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [copying, setCopying] = useState(false);
  const [generating, setGenerating] = useState(false);

  const groups = useGroupStore((s) => s.groups);
  const members = useGroupStore((s) => s.members.get(groupId) || []);
  const generateInvite = useGroupStore((s) => s.generateInvite);
  const leaveGroup = useGroupStore((s) => s.leaveGroup);
  const identity = useIdentityStore((s) => s.identity);

  const group = groups.find((g) => g.id === groupId);
  const isAdmin = group?.creator_public_key === identity?.publicKey;

  if (!group) return null;

  const handleGenerateInvite = async () => {
    setGenerating(true);
    try {
      const code = await generateInvite(groupId);
      setInviteCode(code);
      setShowInvite(true);
    } catch (err) {
      alert(`Failed to generate invite: ${err}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyInvite = async () => {
    if (!inviteCode) return;
    try {
      await navigator.clipboard.writeText(inviteCode);
      setCopying(true);
      setTimeout(() => setCopying(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleLeave = async () => {
    if (confirm('Are you sure you want to leave this group?')) {
      try {
        await leaveGroup(groupId);
      } catch (err) {
        alert(`Failed to leave group: ${err}`);
      }
    }
  };

  return (
    <div className="flex items-center justify-between p-4 border-b border-cosmic-border bg-cosmic-surface/50">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-cosmic-accent flex items-center justify-center text-white font-medium">
          {group.name.charAt(0).toUpperCase()}
        </div>
        <div>
          <h2 className="text-cosmic-text font-semibold">{group.name}</h2>
          <p className="text-sm text-cosmic-muted">{members.length} members</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isAdmin && (
          <button
            onClick={handleGenerateInvite}
            disabled={generating}
            className="px-3 py-1.5 text-sm bg-cosmic-accent hover:bg-cosmic-accent/80 disabled:opacity-50 text-white rounded transition-colors"
          >
            {generating ? 'Generating...' : 'Invite'}
          </button>
        )}

        <button
          onClick={handleLeave}
          className="px-3 py-1.5 text-sm text-cosmic-muted hover:text-red-400 transition-colors"
        >
          Leave
        </button>
      </div>

      {/* Invite modal */}
      {showInvite && inviteCode && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-cosmic-surface rounded-lg p-6 w-[500px] max-w-[90vw] border border-cosmic-border">
            <h3 className="text-lg font-semibold text-cosmic-text mb-4">Invite Link</h3>
            <p className="text-sm text-cosmic-muted mb-3">
              Share this link to invite people to the group:
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={inviteCode}
                readOnly
                className="flex-1 px-3 py-2 bg-cosmic-bg border border-cosmic-border rounded text-cosmic-text font-mono text-sm"
              />
              <button
                onClick={handleCopyInvite}
                className="px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent/80 text-white rounded transition-colors"
              >
                {copying ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-xs text-cosmic-muted mt-2">
              This invite link expires in 7 days.
            </p>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setShowInvite(false)}
                className="text-cosmic-muted hover:text-cosmic-text transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
