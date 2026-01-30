import { create } from 'zustand';
import type { IdentityResponse } from '@/lib/pywebview';

interface IdentityState {
  identity: IdentityResponse | null;
  isLoading: boolean;
  error: string | null;

  setIdentity: (identity: IdentityResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clear: () => void;
}

export const useIdentityStore = create<IdentityState>((set) => ({
  identity: null,
  isLoading: true,
  error: null,

  setIdentity: (identity) => set({ identity, isLoading: false, error: null }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  clear: () => set({ identity: null, isLoading: false, error: null }),
}));
