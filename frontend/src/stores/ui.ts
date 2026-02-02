import { create } from 'zustand';

type Panel = 'chat' | 'settings';
type Section = 'home' | 'contacts' | 'groups' | 'settings';

interface UIState {
  activePanel: Panel;
  activeSection: Section;
  selectedContactId: number | null;
  selectedGroupId: string | null;
  isSidebarCollapsed: boolean;

  setActivePanel: (panel: Panel) => void;
  setActiveSection: (section: Section) => void;
  setSelectedContact: (id: number | null) => void;
  setSelectedGroup: (id: string | null) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activePanel: 'chat',
  activeSection: 'home',
  selectedContactId: null,
  selectedGroupId: null,
  isSidebarCollapsed: false,

  setActivePanel: (activePanel) => set({ activePanel }),
  setActiveSection: (activeSection) => {
    const activePanel = activeSection === 'settings' ? 'settings' : 'chat';
    set({ activeSection, activePanel });
  },
  // Clear group selection when selecting a contact
  setSelectedContact: (selectedContactId) => set({ selectedContactId, selectedGroupId: null }),
  // Clear contact selection when selecting a group
  setSelectedGroup: (selectedGroupId) => set({ selectedGroupId, selectedContactId: null }),
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
