/**
 * Call store - manages voice call state.
 *
 * Handles:
 * - Tracking current call state (incoming, active, etc.)
 * - Call duration tracking
 * - Mute state
 * - Initiating calls via API
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';
import type { VoiceCallState } from '@/lib/pywebview';

export type CallStateValue = VoiceCallState;

interface CallInfo {
  callId: string;
  contactId: number;
  contactName?: string;
  direction: 'outgoing' | 'incoming';
}

interface CallStoreState {
  // Current call state
  state: CallStateValue;
  callInfo: CallInfo | null;
  muted: boolean;
  duration: number; // seconds

  // Actions
  startCall: (contactId: number, contactName?: string) => Promise<boolean>;
  acceptCall: () => Promise<boolean>;
  rejectCall: () => Promise<boolean>;
  endCall: () => Promise<boolean>;
  toggleMute: () => Promise<void>;

  // Internal actions (called by event listeners)
  setCallState: (state: CallStateValue, contactId?: number, callId?: string) => void;
  setIncomingCall: (callId: string, contactId: number, contactName?: string) => void;
  updateDuration: (duration: number) => void;
  reset: () => void;
}

export const useCall = create<CallStoreState>((set, get) => ({
  state: 'idle',
  callInfo: null,
  muted: false,
  duration: 0,

  startCall: async (contactId: number, contactName?: string) => {
    try {
      const result = await api.call((a) => a.start_call(contactId));
      if (result.callId) {
        set({
          state: 'ringing_outgoing',
          callInfo: {
            callId: result.callId,
            contactId,
            contactName,
            direction: 'outgoing',
          },
          muted: false,
          duration: 0,
        });
        return true;
      }
      console.error('Failed to start call:', result.error);
      return false;
    } catch (error) {
      console.error('Error starting call:', error);
      return false;
    }
  },

  acceptCall: async () => {
    try {
      const result = await api.call((a) => a.accept_call());
      if (result.success) {
        set({ state: 'connecting' });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error accepting call:', error);
      return false;
    }
  },

  rejectCall: async () => {
    try {
      const result = await api.call((a) => a.reject_call());
      set({ state: 'idle', callInfo: null });
      return result.success;
    } catch (error) {
      console.error('Error rejecting call:', error);
      return false;
    }
  },

  endCall: async () => {
    try {
      const result = await api.call((a) => a.end_call());
      set({ state: 'idle', callInfo: null, duration: 0 });
      return result.success;
    } catch (error) {
      console.error('Error ending call:', error);
      return false;
    }
  },

  toggleMute: async () => {
    const newMuted = !get().muted;
    await api.call((a) => a.set_muted(newMuted));
    set({ muted: newMuted });
  },

  setCallState: (state: CallStateValue, contactId?: number, callId?: string) => {
    if (state === 'ended' || state === 'idle') {
      set({ state: 'idle', callInfo: null, duration: 0 });
    } else {
      set((prev) => ({
        state,
        callInfo: prev.callInfo
          ? prev.callInfo
          : contactId && callId
            ? { callId, contactId, direction: 'incoming' }
            : null,
      }));
    }
  },

  setIncomingCall: (callId: string, contactId: number, contactName?: string) => {
    set({
      state: 'ringing_incoming',
      callInfo: {
        callId,
        contactId,
        contactName,
        direction: 'incoming',
      },
      muted: false,
      duration: 0,
    });
  },

  updateDuration: (duration: number) => {
    set({ duration });
  },

  reset: () => {
    set({
      state: 'idle',
      callInfo: null,
      muted: false,
      duration: 0,
    });
  },
}));

// Initialize event listeners when store is created
if (typeof window !== 'undefined') {
  // Listen for call state changes
  window.addEventListener('discordopus:call_state', ((event: CustomEvent) => {
    const { contactId, state } = event.detail;
    useCall.getState().setCallState(state, contactId);
  }) as EventListener);

  // Listen for incoming calls
  window.addEventListener('discordopus:incoming_call', ((event: CustomEvent) => {
    const { callId } = event.detail;
    // For incoming calls, the contactId will be provided by the call_state event
    // or we can look it up by fromKey later. For now, use 0 as placeholder.
    useCall.getState().setIncomingCall(callId, 0, undefined);
  }) as EventListener);

  // Listen for call answered (our outgoing call was accepted)
  window.addEventListener('discordopus:call_answered', (() => {
    useCall.getState().setCallState('connecting');
  }) as EventListener);

  // Listen for call rejected
  window.addEventListener('discordopus:call_rejected', (() => {
    useCall.getState().reset();
  }) as EventListener);

  // Listen for call ended
  window.addEventListener('discordopus:call_ended', (() => {
    useCall.getState().reset();
  }) as EventListener);

  // Listen for remote mute changes
  window.addEventListener('discordopus:remote_mute', ((event: CustomEvent) => {
    // Remote mute is for display purposes - the remote peer muted/unmuted
    // We could track this in the store if we want to show visual indication
    console.log('Remote peer muted:', event.detail.muted);
  }) as EventListener);
}
