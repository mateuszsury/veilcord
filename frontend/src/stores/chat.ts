/**
 * Chat store - manages current chat state.
 *
 * Tracks which contact is currently selected and P2P connection state.
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';
import type { P2PConnectionState, P2PStateEventPayload, MessageEventPayload, TypingEventData } from '@/lib/pywebview';

type P2PState = 'disconnected' | 'connecting' | 'connected' | 'failed';

// Map backend P2PConnectionState to simplified P2PState
function mapP2PState(state: P2PConnectionState): P2PState {
  switch (state) {
    case 'connected':
      return 'connected';
    case 'connecting':
    case 'new':
      return 'connecting';
    case 'failed':
      return 'failed';
    case 'disconnected':
    case 'closed':
    default:
      return 'disconnected';
  }
}

interface ChatState {
  // Currently selected contact ID
  activeContactId: number | null;

  // P2P connection states by contact ID
  p2pStates: Record<number, P2PState>;

  // Typing indicators by contact ID
  typingContacts: Set<number>;

  // Actions
  setActiveContact: (contactId: number | null) => void;
  initiateConnection: (contactId: number) => Promise<boolean>;
  setP2PState: (contactId: number, state: P2PState) => void;
  setTyping: (contactId: number, active: boolean) => void;
}

export const useChat = create<ChatState>((set) => ({
  activeContactId: null,
  p2pStates: {},
  typingContacts: new Set(),

  setActiveContact: (contactId: number | null) => {
    set({ activeContactId: contactId });

    // Load messages for new contact
    if (contactId !== null) {
      import('./messages').then(({ useMessages }) => {
        useMessages.getState().loadMessages(contactId);
      });
    }
  },

  initiateConnection: async (contactId: number) => {
    set((state) => ({
      p2pStates: { ...state.p2pStates, [contactId]: 'connecting' },
    }));

    try {
      await api.call((a) => a.initiate_p2p_connection(contactId));
      return true;
    } catch (error) {
      console.error('Connection error:', error);
      set((state) => ({
        p2pStates: { ...state.p2pStates, [contactId]: 'failed' },
      }));
      return false;
    }
  },

  setP2PState: (contactId: number, state: P2PState) => {
    set((s) => ({
      p2pStates: { ...s.p2pStates, [contactId]: state },
    }));
  },

  setTyping: (contactId: number, active: boolean) => {
    set((state) => {
      const newTyping = new Set(state.typingContacts);
      if (active) {
        newTyping.add(contactId);
      } else {
        newTyping.delete(contactId);
      }
      return { typingContacts: newTyping };
    });

    // Auto-clear typing after 5 seconds
    if (active) {
      setTimeout(() => {
        set((state) => {
          const newTyping = new Set(state.typingContacts);
          newTyping.delete(contactId);
          return { typingContacts: newTyping };
        });
      }, 5000);
    }
  },
}));

// Listen for P2P state events
if (typeof window !== 'undefined') {
  window.addEventListener('discordopus:p2p_state', ((event: CustomEvent<P2PStateEventPayload>) => {
    const { contactId, state } = event.detail;
    if (contactId != null) {
      useChat.getState().setP2PState(contactId, mapP2PState(state));
    }
  }) as EventListener);

  window.addEventListener('discordopus:message', ((event: CustomEvent<MessageEventPayload>) => {
    const { contactId, message } = event.detail;
    if (contactId != null && message && 'type' in message && message.type === 'typing') {
      const typingData = message as TypingEventData;
      useChat.getState().setTyping(contactId, typingData.active);
    }
  }) as EventListener);
}
