/**
 * Message store - manages message state and API interactions.
 *
 * Handles:
 * - Loading message history from database
 * - Sending new messages via API
 * - Receiving real-time message updates via events
 * - Optimistic updates for sent messages
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';
import type { MessageResponse, MessageEventPayload } from '@/lib/pywebview';

export interface Message {
  id: string;
  sender_id: string; // 'self' for outgoing, public key for incoming
  type: 'text' | 'edit' | 'delete' | 'file';
  body: string;
  timestamp: number;
  edited: boolean;
  reply_to?: string;
  file_id?: number | null;
}

interface MessagesState {
  // Messages by contact ID
  messagesByContact: Record<number, Message[]>;

  // Loading state per contact
  loading: Record<number, boolean>;

  // Whether we have more messages to load (pagination)
  hasMore: Record<number, boolean>;

  // Actions
  loadMessages: (contactId: number, before?: number) => Promise<void>;
  sendMessage: (contactId: number, body: string, replyTo?: string) => Promise<boolean>;
  addMessage: (contactId: number, message: Message) => void;
  updateMessage: (messageId: string, newBody: string) => void;
  deleteMessage: (messageId: string) => void;
  clearMessages: (contactId: number) => void;
}

// Convert MessageResponse from API to local Message format
function toMessage(response: MessageResponse): Message {
  return {
    id: response.id,
    sender_id: response.senderId,
    type: response.type,
    body: response.body || '',
    timestamp: response.timestamp,
    edited: response.edited,
    reply_to: response.replyTo || undefined,
    file_id: response.fileId || undefined,
  };
}

export const useMessages = create<MessagesState>((set, get) => ({
  messagesByContact: {},
  loading: {},
  hasMore: {},

  loadMessages: async (contactId: number, before?: number) => {
    set((state) => ({
      loading: { ...state.loading, [contactId]: true },
    }));

    try {
      const messages = await api.call((a) => a.get_messages(contactId, 50, before));

      set((state) => {
        const existing = before ? state.messagesByContact[contactId] || [] : [];
        // Messages come in desc order (newest first), we want asc for display
        const newMessages = [...messages].reverse().map(toMessage);

        // Merge: new messages go before existing (they're older)
        const merged = before ? [...newMessages, ...existing] : newMessages;

        return {
          messagesByContact: {
            ...state.messagesByContact,
            [contactId]: merged,
          },
          loading: { ...state.loading, [contactId]: false },
          hasMore: { ...state.hasMore, [contactId]: messages.length === 50 },
        };
      });
    } catch (error) {
      console.error('Failed to load messages:', error);
      set((state) => ({
        loading: { ...state.loading, [contactId]: false },
      }));
    }
  },

  sendMessage: async (contactId: number, body: string, replyTo?: string) => {
    try {
      const result = await api.call((a) => a.send_message(contactId, body, replyTo));

      if (result) {
        // Add to local state
        const message: Message = {
          id: result.id,
          sender_id: 'self',
          type: result.type,
          body: result.body || body,
          timestamp: result.timestamp,
          edited: false,
          reply_to: replyTo,
          file_id: result.fileId || undefined,
        };

        get().addMessage(contactId, message);
        return true;
      }

      console.error('Send failed: no result returned');
      return false;
    } catch (error) {
      console.error('Send error:', error);
      return false;
    }
  },

  addMessage: (contactId: number, message: Message) => {
    set((state) => {
      const existing = state.messagesByContact[contactId] || [];
      // Avoid duplicates
      if (existing.some((m) => m.id === message.id)) {
        return state;
      }
      return {
        messagesByContact: {
          ...state.messagesByContact,
          [contactId]: [...existing, message],
        },
      };
    });
  },

  updateMessage: (messageId: string, newBody: string) => {
    set((state) => {
      const updated = { ...state.messagesByContact };
      for (const contactId of Object.keys(updated)) {
        const messages = updated[Number(contactId)];
        if (messages) {
          updated[Number(contactId)] = messages.map((m) =>
            m.id === messageId ? { ...m, body: newBody, edited: true } : m
          );
        }
      }
      return { messagesByContact: updated };
    });
  },

  deleteMessage: (messageId: string) => {
    set((state) => {
      const updated = { ...state.messagesByContact };
      for (const contactId of Object.keys(updated)) {
        const messages = updated[Number(contactId)];
        if (messages) {
          updated[Number(contactId)] = messages.filter(
            (m) => m.id !== messageId
          );
        }
      }
      return { messagesByContact: updated };
    });
  },

  clearMessages: (contactId: number) => {
    set((state) => {
      const { [contactId]: _, ...rest } = state.messagesByContact;
      return { messagesByContact: rest };
    });
  },
}));

// Listen for real-time message events
if (typeof window !== 'undefined') {
  window.addEventListener('veilcord:message', ((event: CustomEvent<MessageEventPayload>) => {
    const { contactId, message } = event.detail;

    if (!contactId || !message) return;

    // Handle different message types
    if ('type' in message) {
      if (message.type === 'edit' && 'targetId' in message && 'newBody' in message) {
        useMessages.getState().updateMessage(message.targetId, message.newBody);
      } else if (message.type === 'delete' && 'targetId' in message) {
        useMessages.getState().deleteMessage(message.targetId);
      } else if ((message.type === 'text' || message.type === 'file') && 'id' in message) {
        // New text or file message
        useMessages.getState().addMessage(contactId, {
          id: message.id,
          sender_id: message.senderId,
          type: message.type,
          body: message.body || '',
          timestamp: message.timestamp,
          edited: message.edited,
          reply_to: message.replyTo || undefined,
          file_id: message.fileId || undefined,
        });
      }
    }
  }) as EventListener);
}
