/**
 * Groups store - manages group state and API interactions.
 *
 * Handles:
 * - Loading groups from backend
 * - Creating and joining groups
 * - Managing group members
 * - Group call state
 * - Real-time group event updates
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';
import type { Group, GroupMember } from '@/lib/pywebview';

interface GroupState {
  // State
  groups: Group[];
  selectedGroupId: string | null;
  members: Map<string, GroupMember[]>;  // group_id -> members
  loading: boolean;
  error: string | null;

  // Group call state
  activeGroupCall: string | null;  // group_id of active call
  groupCallParticipants: string[];  // public keys of participants

  // Actions
  loadGroups: () => Promise<void>;
  selectGroup: (groupId: string | null) => void;
  createGroup: (name: string) => Promise<Group>;
  joinGroup: (inviteCode: string) => Promise<Group>;
  leaveGroup: (groupId: string) => Promise<void>;
  loadMembers: (groupId: string) => Promise<void>;
  removeMember: (groupId: string, publicKey: string) => Promise<void>;
  generateInvite: (groupId: string) => Promise<string>;

  // Group call actions
  startGroupCall: (groupId: string, callId: string) => Promise<void>;
  joinGroupCall: (groupId: string, callId: string) => Promise<void>;
  leaveGroupCall: (groupId: string) => Promise<void>;
  setGroupCallMuted: (groupId: string, muted: boolean) => Promise<void>;

  // Event handlers (called from event listeners)
  handleGroupCreated: (group: Group) => void;
  handleGroupJoined: (group: Group) => void;
  handleGroupLeft: (groupId: string) => void;
  handleMemberAdded: (groupId: string, member: GroupMember) => void;
  handleMemberRemoved: (groupId: string, publicKey: string) => void;
  handleGroupCallState: (groupId: string, state: string) => void;
}

export const useGroupStore = create<GroupState>((set, get) => ({
  // Initial state
  groups: [],
  selectedGroupId: null,
  members: new Map(),
  loading: false,
  error: null,
  activeGroupCall: null,
  groupCallParticipants: [],

  // Load all groups
  loadGroups: async () => {
    set({ loading: true, error: null });
    try {
      const groups = await api.call((a) => a.get_groups());
      set({ groups: groups || [], loading: false });
    } catch (err) {
      set({ error: String(err), loading: false });
    }
  },

  // Select a group
  selectGroup: (groupId) => {
    set({ selectedGroupId: groupId });
    if (groupId) {
      get().loadMembers(groupId);
    }
  },

  // Create a new group
  createGroup: async (name) => {
    try {
      const group = await api.call((a) => a.create_group(name));
      set((state) => ({ groups: [...state.groups, group] }));
      return group;
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  // Join via invite
  joinGroup: async (inviteCode) => {
    try {
      const group = await api.call((a) => a.join_group(inviteCode));
      set((state) => ({
        groups: state.groups.some(g => g.id === group.id)
          ? state.groups
          : [...state.groups, group]
      }));
      return group;
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  // Leave group
  leaveGroup: async (groupId) => {
    try {
      await api.call((a) => a.leave_group(groupId));
      set((state) => ({
        groups: state.groups.filter(g => g.id !== groupId),
        selectedGroupId: state.selectedGroupId === groupId ? null : state.selectedGroupId
      }));
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  // Load members for a group
  loadMembers: async (groupId) => {
    try {
      const members = await api.call((a) => a.get_group_members(groupId));
      set((state) => {
        const newMembers = new Map(state.members);
        newMembers.set(groupId, members || []);
        return { members: newMembers };
      });
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  },

  // Remove a member
  removeMember: async (groupId, publicKey) => {
    try {
      await api.call((a) => a.remove_group_member(groupId, publicKey));
      set((state) => {
        const newMembers = new Map(state.members);
        const current = newMembers.get(groupId) || [];
        newMembers.set(groupId, current.filter(m => m.public_key !== publicKey));
        return { members: newMembers };
      });
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  // Generate invite code
  generateInvite: async (groupId) => {
    try {
      return await api.call((a) => a.generate_group_invite(groupId));
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  // Group call actions
  startGroupCall: async (groupId, callId) => {
    try {
      await api.call((a) => a.start_group_call(groupId, callId));
      set({ activeGroupCall: groupId });
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  joinGroupCall: async (groupId, callId) => {
    try {
      await api.call((a) => a.join_group_call(groupId, callId));
      set({ activeGroupCall: groupId });
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  leaveGroupCall: async (groupId) => {
    try {
      await api.call((a) => a.leave_group_call(groupId));
      set({ activeGroupCall: null, groupCallParticipants: [] });
    } catch (err) {
      set({ error: String(err) });
      throw err;
    }
  },

  setGroupCallMuted: async (groupId, muted) => {
    try {
      await api.call((a) => a.set_group_call_muted(groupId, muted));
    } catch (err) {
      set({ error: String(err) });
    }
  },

  // Event handlers
  handleGroupCreated: (group) => {
    set((state) => ({
      groups: state.groups.some(g => g.id === group.id)
        ? state.groups
        : [...state.groups, group]
    }));
  },

  handleGroupJoined: (group) => {
    set((state) => ({
      groups: state.groups.some(g => g.id === group.id)
        ? state.groups
        : [...state.groups, group]
    }));
  },

  handleGroupLeft: (groupId) => {
    set((state) => ({
      groups: state.groups.filter(g => g.id !== groupId),
      selectedGroupId: state.selectedGroupId === groupId ? null : state.selectedGroupId
    }));
  },

  handleMemberAdded: (groupId, member) => {
    set((state) => {
      const newMembers = new Map(state.members);
      const current = newMembers.get(groupId) || [];
      if (!current.some(m => m.public_key === member.public_key)) {
        newMembers.set(groupId, [...current, member]);
      }
      return { members: newMembers };
    });
  },

  handleMemberRemoved: (groupId, publicKey) => {
    set((state) => {
      const newMembers = new Map(state.members);
      const current = newMembers.get(groupId) || [];
      newMembers.set(groupId, current.filter(m => m.public_key !== publicKey));
      return { members: newMembers };
    });
  },

  handleGroupCallState: (_groupId, state) => {
    if (state === 'ended') {
      set({ activeGroupCall: null, groupCallParticipants: [] });
    }
  },
}));

// Set up event listeners
if (typeof window !== 'undefined') {
  window.addEventListener('veilcord:group_created', ((e: CustomEvent) => {
    useGroupStore.getState().handleGroupCreated(e.detail.group);
  }) as EventListener);

  window.addEventListener('veilcord:group_joined', ((e: CustomEvent) => {
    useGroupStore.getState().handleGroupJoined(e.detail.group);
  }) as EventListener);

  window.addEventListener('veilcord:group_left', ((e: CustomEvent) => {
    useGroupStore.getState().handleGroupLeft(e.detail.group_id);
  }) as EventListener);

  window.addEventListener('veilcord:group_member_added', ((e: CustomEvent) => {
    useGroupStore.getState().handleMemberAdded(e.detail.group_id, e.detail.member);
  }) as EventListener);

  window.addEventListener('veilcord:group_member_removed', ((e: CustomEvent) => {
    useGroupStore.getState().handleMemberRemoved(e.detail.group_id, e.detail.public_key);
  }) as EventListener);

  window.addEventListener('veilcord:group_call_state', ((e: CustomEvent) => {
    useGroupStore.getState().handleGroupCallState(e.detail.group_id, e.detail.state);
  }) as EventListener);
}
