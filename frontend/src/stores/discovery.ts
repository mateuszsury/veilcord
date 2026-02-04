/**
 * Store for managing user discovery state.
 *
 * Handles the autodiscovery feature where users can opt-in to be
 * visible to other users on the same signaling server.
 */

import { create } from 'zustand';
import type { DiscoveredUser, UserStatus } from '@/lib/pywebview';
import { api } from '@/lib/pywebview';

interface DiscoveryState {
  enabled: boolean;
  users: DiscoveredUser[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setEnabled: (enabled: boolean) => void;
  addUser: (user: DiscoveredUser) => void;
  removeUser: (publicKey: string) => void;
  setUsers: (users: DiscoveredUser[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Async actions
  loadState: () => Promise<void>;
  toggleDiscovery: (enabled: boolean) => Promise<boolean>;
}

export const useDiscoveryStore = create<DiscoveryState>((set) => ({
  enabled: false,
  users: [],
  isLoading: true,
  error: null,

  setEnabled: (enabled) => set({ enabled }),
  addUser: (user) =>
    set((state) => ({
      users: [...state.users.filter((u) => u.publicKey !== user.publicKey), user],
    })),
  removeUser: (publicKey) =>
    set((state) => ({
      users: state.users.filter((u) => u.publicKey !== publicKey),
    })),
  setUsers: (users) => set({ users }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  loadState: async () => {
    try {
      set({ isLoading: true, error: null });
      const [enabled, users] = await Promise.all([
        api.call((a) => a.is_discovery_enabled()),
        api.call((a) => a.get_discovered_users()),
      ]);
      set({
        enabled,
        users,
        isLoading: false,
      });
    } catch (e) {
      set({ error: String(e), isLoading: false });
    }
  },

  toggleDiscovery: async (enabled) => {
    try {
      set({ error: null });
      const result = await api.call((a) => a.set_discovery_enabled(enabled));
      if (result.success) {
        set({ enabled });
        // Clear users when disabling
        if (!enabled) {
          set({ users: [] });
        }
        return true;
      } else {
        set({ error: result.error || 'Failed to change discovery setting' });
        return false;
      }
    } catch (e) {
      set({ error: String(e) });
      return false;
    }
  },
}));

// Set up event listeners for backend events
if (typeof window !== 'undefined') {
  window.addEventListener('veilcord:discovery_user', ((
    e: CustomEvent<{
      action: 'join' | 'leave';
      publicKey: string;
      displayName?: string;
      status?: UserStatus;
    }>
  ) => {
    const { action, publicKey, displayName, status } = e.detail;

    if (action === 'join' && displayName) {
      useDiscoveryStore.getState().addUser({
        publicKey,
        displayName,
        status: status || 'online',
      });
    } else if (action === 'leave') {
      useDiscoveryStore.getState().removeUser(publicKey);
    }
  }) as EventListener);
}
