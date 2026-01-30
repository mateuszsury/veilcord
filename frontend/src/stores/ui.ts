import { create } from 'zustand';

type Panel = 'chat' | 'settings';

interface UIState {
  activePanel: Panel;
  selectedContactId: number | null;
  isSidebarCollapsed: boolean;

  setActivePanel: (panel: Panel) => void;
  setSelectedContact: (id: number | null) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activePanel: 'chat',
  selectedContactId: null,
  isSidebarCollapsed: false,

  setActivePanel: (activePanel) => set({ activePanel }),
  setSelectedContact: (selectedContactId) => set({ selectedContactId }),
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
