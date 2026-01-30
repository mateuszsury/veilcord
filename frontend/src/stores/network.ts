import { create } from 'zustand';
import type { ConnectionState, UserStatus } from '@/lib/pywebview';
import { api } from '@/lib/pywebview';

interface NetworkState {
  connectionState: ConnectionState;
  userStatus: UserStatus;
  signalingServer: string;
  isLoading: boolean;
  error: string | null;

  // Actions
  setConnectionState: (state: ConnectionState) => void;
  setUserStatus: (status: UserStatus) => void;
  setSignalingServer: (url: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Async actions that call API
  loadInitialState: () => Promise<void>;
  updateUserStatus: (status: UserStatus) => Promise<void>;
  updateSignalingServer: (url: string) => Promise<void>;
}

export const useNetworkStore = create<NetworkState>((set) => ({
  connectionState: 'disconnected',
  userStatus: 'online',
  signalingServer: '',
  isLoading: true,
  error: null,

  setConnectionState: (connectionState) => set({ connectionState }),
  setUserStatus: (userStatus) => set({ userStatus }),
  setSignalingServer: (signalingServer) => set({ signalingServer }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),

  loadInitialState: async () => {
    try {
      set({ isLoading: true, error: null });
      const [state, status, server] = await Promise.all([
        api.call((a) => a.get_connection_state()),
        api.call((a) => a.get_user_status()),
        api.call((a) => a.get_signaling_server()),
      ]);
      set({
        connectionState: state,
        userStatus: status,
        signalingServer: server,
        isLoading: false,
      });
    } catch (e) {
      set({ error: String(e), isLoading: false });
    }
  },

  updateUserStatus: async (status) => {
    try {
      await api.call((a) => a.set_user_status(status));
      set({ userStatus: status });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  updateSignalingServer: async (url) => {
    try {
      await api.call((a) => a.set_signaling_server(url));
      set({ signalingServer: url });
    } catch (e) {
      set({ error: String(e) });
    }
  },
}));

// Set up event listeners for backend events
if (typeof window !== 'undefined') {
  window.addEventListener('discordopus:connection', ((e: CustomEvent) => {
    useNetworkStore.getState().setConnectionState(e.detail.state);
  }) as EventListener);
}
