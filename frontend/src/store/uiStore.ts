import { create } from 'zustand';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface UIState {
  isMobileMenuOpen: boolean;
  toasts: Toast[];
  isGlobalLoading: boolean;

  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
  addToast: (type: Toast['type'], message: string) => void;
  removeToast: (id: string) => void;
  setGlobalLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isMobileMenuOpen: false,
  toasts: [],
  isGlobalLoading: false,

  toggleMobileMenu: () =>
    set((s) => ({ isMobileMenuOpen: !s.isMobileMenuOpen })),
  closeMobileMenu: () => set({ isMobileMenuOpen: false }),

  addToast: (type, message) => {
    const id = Date.now().toString();
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    // Auto-remove after 4 seconds
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  setGlobalLoading: (loading) => set({ isGlobalLoading: loading }),
}));
