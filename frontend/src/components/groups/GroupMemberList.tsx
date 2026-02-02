/**
 * Group member list panel.
 *
 * Displays all members of a group with:
 * - Member avatar and name
 * - Admin badge
 * - Remove button (for admins only)
 */

import { useEffect } from 'react';
import { useGroupStore } from '@/stores/groups';
import { useIdentityStore } from '@/stores/identity';

interface Props {
  groupId: string;
}

export function GroupMemberList({ groupId }: Props) {
  const members = useGroupStore((s) => s.members.get(groupId) || []);
  const loadMembers = useGroupStore((s) => s.loadMembers);
  const removeMember = useGroupStore((s) => s.removeMember);
  const groups = useGroupStore((s) => s.groups);
  const identity = useIdentityStore((s) => s.identity);

  const group = groups.find((g) => g.id === groupId);
  // Check if current user is admin (creator)
  const isAdmin = group?.creator_public_key === identity?.publicKey;

  useEffect(() => {
    loadMembers(groupId);
  }, [groupId, loadMembers]);

  const handleRemove = async (publicKey: string) => {
    if (confirm('Remove this member from the group?')) {
      try {
        await removeMember(groupId, publicKey);
      } catch (err) {
        alert(`Failed to remove member: ${err}`);
      }
    }
  };

  return (
    <div className="p-4 border-l border-discord-bg-tertiary w-64 bg-discord-bg-secondary/50">
      <h3 className="text-sm font-semibold text-discord-text-muted uppercase mb-3">
        Members ({members.length})
      </h3>

      <div className="space-y-2">
        {members.map((member) => (
          <div
            key={member.public_key}
            className="flex items-center justify-between p-2 rounded hover:bg-discord-bg-modifier-hover"
          >
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-accent-red flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                {member.display_name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-discord-text-primary text-sm truncate">{member.display_name}</p>
                {member.is_admin && (
                  <span className="text-xs text-accent-red-text">Admin</span>
                )}
              </div>
            </div>

            {isAdmin && !member.is_admin && member.public_key !== identity?.publicKey && (
              <button
                onClick={() => handleRemove(member.public_key)}
                className="text-discord-text-muted hover:text-red-400 p-1 transition-colors"
                title="Remove member"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}

        {members.length === 0 && (
          <p className="text-sm text-discord-text-muted text-center py-4">
            No members yet
          </p>
        )}
      </div>
    </div>
  );
}
