import { create } from 'zustand';
import type { ContactResponse, UserStatus, OpenChatEventPayload } from '@/lib/pywebview';
import { useUIStore } from './ui';

interface ContactsState {
  contacts: ContactResponse[];
  isLoading: boolean;
  error: string | null;

  setContacts: (contacts: ContactResponse[]) => void;
  addContact: (contact: ContactResponse) => void;
  removeContact: (id: number) => void;
  updateContact: (id: number, updates: Partial<ContactResponse>) => void;
  updateContactStatus: (publicKey: string, status: UserStatus) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useContactsStore = create<ContactsState>((set) => ({
  contacts: [],
  isLoading: true,
  error: null,

  setContacts: (contacts) => set({ contacts, isLoading: false, error: null }),

  addContact: (contact) =>
    set((state) => ({
      contacts: [...state.contacts, contact],
    })),

  removeContact: (id) =>
    set((state) => ({
      contacts: state.contacts.filter((c) => c.id !== id),
    })),

  updateContact: (id, updates) =>
    set((state) => ({
      contacts: state.contacts.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
    })),

  // Update contact online status by public key
  updateContactStatus: (publicKey, status) =>
    set((state) => ({
      contacts: state.contacts.map((c) =>
        c.publicKey.includes(publicKey) ? { ...c, onlineStatus: status } : c
      ),
    })),

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
}));

// Set up event listener for presence updates from backend
if (typeof window !== 'undefined') {
  window.addEventListener('veilcord:presence', ((e: CustomEvent) => {
    useContactsStore.getState().updateContactStatus(e.detail.publicKey, e.detail.status);
  }) as EventListener);

  // Listen for notification open chat events
  window.addEventListener('veilcord:open_chat', ((event: CustomEvent<OpenChatEventPayload>) => {
    const { contactId } = event.detail;
    console.log('Notification: opening chat for contact', contactId);
    useUIStore.getState().setSelectedContact(contactId);
  }) as EventListener);
}
