/**
 * GroupList - Group list for the groups section
 *
 * Displays all groups with:
 * - Initial avatar (colored circle with first letter)
 * - Group name
 * - Member count
 * - Selection highlight (red accent when selected)
 *
 * Header includes create/join group buttons.
 * Integrates with groupStore for data and uiStore for selection.
 */

import { useState } from 'react';
import { useGroupStore } from '@/stores/groups';
import { useUIStore } from '@/stores/ui';
import { CreateGroupDialog, JoinGroupDialog } from '@/components/groups';

export function GroupList() {
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);

  const groups = useGroupStore((s) => s.groups);
  const members = useGroupStore((s) => s.members);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const setSelectedGroup = useUIStore((s) => s.setSelectedGroup);
  const setActivePanel = useUIStore((s) => s.setActivePanel);

  const handleGroupClick = (groupId: string) => {
    setSelectedGroup(groupId);
    setActivePanel('chat');
  };

  const getMemberCount = (groupId: string): number => {
    const groupMembers = members.get(groupId);
    return groupMembers?.length ?? 0;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with title and action buttons */}
      <div className="p-4 pb-2">
        <div className="flex items-center justify-between">
          <h2 className="text-xs uppercase text-discord-text-muted tracking-wide font-semibold">
            Groups
          </h2>
          <div className="flex gap-1">
            <button
              onClick={() => setShowJoinGroup(true)}
              className="p-1.5 text-discord-text-muted hover:text-discord-text-primary hover:bg-discord-bg-modifier-hover rounded transition-colors"
              title="Join group"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                />
              </svg>
            </button>
            <button
              onClick={() => setShowCreateGroup(true)}
              className="p-1.5 text-discord-text-muted hover:text-discord-text-primary hover:bg-discord-bg-modifier-hover rounded transition-colors"
              title="Create group"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Group list */}
      <div className="flex-1 overflow-y-auto px-2">
        {groups.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-discord-text-muted text-center px-4">
              No groups yet.
              <br />
              Create or join one!
            </p>
          </div>
        ) : (
          <ul className="space-y-0.5">
            {groups.map((group) => {
              const isSelected = selectedGroupId === group.id;
              const memberCount = getMemberCount(group.id);

              return (
                <li key={group.id}>
                  <button
                    onClick={() => handleGroupClick(group.id)}
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
                    {/* Group initial avatar */}
                    <div className="w-8 h-8 rounded-full bg-accent-red/50 flex items-center justify-center text-sm font-medium text-white flex-shrink-0">
                      {group.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {group.name}
                      </div>
                      <div className="text-xs text-discord-text-muted">
                        {memberCount === 0
                          ? 'Loading...'
                          : `${memberCount} member${memberCount !== 1 ? 's' : ''}`}
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Group Dialogs */}
      <CreateGroupDialog
        isOpen={showCreateGroup}
        onClose={() => setShowCreateGroup(false)}
      />
      <JoinGroupDialog
        isOpen={showJoinGroup}
        onClose={() => setShowJoinGroup(false)}
      />
    </div>
  );
}
