/**
 * Group messages store - manages group message state and API interactions.
 *
 * Handles:
 * - Sending messages to groups via API
 * - Receiving real-time group messages via events
 * - Optimistic updates for sent messages
 * - Message status tracking (sending, sent, failed)
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';

interface GroupMessageData {
  id: string;
  group_id: string;
  sender_public_key: string;
  sender_name: string;
  body: string;
  timestamp: number;
  status: 'sending' | 'sent' | 'failed';
}

interface GroupMessagesState {
  // Messages by group: group_id -> messages
  messages: Map<string, GroupMessageData[]>;
  loading: boolean;

  // Actions
  sendMessage: (groupId: string, text: string) => Promise<void>;
  handleIncomingMessage: (groupId: string, senderKey: string, messageId: string, body: string, timestamp: number) => void;
  clearMessages: (groupId: string) => void;
}

export const useGroupMessagesStore = create<GroupMessagesState>((set, get) => ({
  messages: new Map(),
  loading: false,

  sendMessage: async (groupId, text) => {
    const messageId = crypto.randomUUID();

    // Optimistic update
    const optimisticMessage: GroupMessageData = {
      id: messageId,
      group_id: groupId,
      sender_public_key: 'self',  // Will be resolved by sender name
      sender_name: 'You',
      body: text,
      timestamp: Date.now(),
      status: 'sending',
    };

    set((state) => {
      const newMessages = new Map(state.messages);
      const current = newMessages.get(groupId) || [];
      newMessages.set(groupId, [...current, optimisticMessage]);
      return { messages: newMessages };
    });

    try {
      await api.call((a) => a.send_group_message(groupId, messageId, text));

      // Update status to sent
      set((state) => {
        const newMessages = new Map(state.messages);
        const current = newMessages.get(groupId) || [];
        const updated = current.map((m) =>
          m.id === messageId ? { ...m, status: 'sent' as const } : m
        );
        newMessages.set(groupId, updated);
        return { messages: newMessages };
      });
    } catch (err) {
      // Mark as failed
      set((state) => {
        const newMessages = new Map(state.messages);
        const current = newMessages.get(groupId) || [];
        const updated = current.map((m) =>
          m.id === messageId ? { ...m, status: 'failed' as const } : m
        );
        newMessages.set(groupId, updated);
        return { messages: newMessages };
      });
      throw err;
    }
  },

  handleIncomingMessage: (groupId, senderKey, messageId, body, timestamp) => {
    // Check if we already have this message (e.g., our own message)
    const existing = get().messages.get(groupId) || [];
    if (existing.some((m) => m.id === messageId)) {
      return;
    }

    const message: GroupMessageData = {
      id: messageId,
      group_id: groupId,
      sender_public_key: senderKey,
      sender_name: senderKey.slice(0, 8) + '...', // Will be resolved by UI
      body,
      timestamp,
      status: 'sent',
    };

    set((state) => {
      const newMessages = new Map(state.messages);
      const current = newMessages.get(groupId) || [];
      newMessages.set(groupId, [...current, message].sort((a, b) => a.timestamp - b.timestamp));
      return { messages: newMessages };
    });
  },

  clearMessages: (groupId) => {
    set((state) => {
      const newMessages = new Map(state.messages);
      newMessages.delete(groupId);
      return { messages: newMessages };
    });
  },
}));

// Event listener for incoming group messages
if (typeof window !== 'undefined') {
  window.addEventListener('veilcord:group_message', ((e: CustomEvent) => {
    const { group_id, sender_public_key, message_id, body, timestamp } = e.detail;
    useGroupMessagesStore.getState().handleIncomingMessage(
      group_id,
      sender_public_key,
      message_id,
      body,
      timestamp
    );
  }) as EventListener);
}
