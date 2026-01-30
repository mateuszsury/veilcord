import { create } from 'zustand';
import type { ContactResponse } from '@/lib/pywebview';

interface ContactsState {
  contacts: ContactResponse[];
  isLoading: boolean;
  error: string | null;

  setContacts: (contacts: ContactResponse[]) => void;
  addContact: (contact: ContactResponse) => void;
  removeContact: (id: number) => void;
  updateContact: (id: number, updates: Partial<ContactResponse>) => void;
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

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
}));
