import { create } from 'zustand';

type Panel = 'chat' | 'settings';

interface UIState {
  activePanel: Panel;
  selectedContactId: number | null;
  selectedGroupId: string | null;
  isSidebarCollapsed: boolean;

  setActivePanel: (panel: Panel) => void;
  setSelectedContact: (id: number | null) => void;
  setSelectedGroup: (id: string | null) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activePanel: 'chat',
  selectedContactId: null,
  selectedGroupId: null,
  isSidebarCollapsed: false,

  setActivePanel: (activePanel) => set({ activePanel }),
  // Clear group selection when selecting a contact
  setSelectedContact: (selectedContactId) => set({ selectedContactId, selectedGroupId: null }),
  // Clear contact selection when selecting a group
  setSelectedGroup: (selectedGroupId) => set({ selectedGroupId, selectedContactId: null }),
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
