import { create } from 'zustand';
import {
  fetchRides,
  fetchRide,
  acceptRide as acceptRideAPI,
  startRide as startRideAPI,
  completeRide as completeRideAPI,
  cancelRide as cancelRideAPI,
} from '../services/ridesService';
import type { Ride, RidesFilters } from '../services/ridesService';
import { useUIStore } from './uiStore';

interface RidesState {
  rides: Ride[];
  total: number;
  currentRide: Ride | null;
  isLoading: boolean;
  filters: RidesFilters;

  loadRides: () => Promise<void>;
  loadRide: (id: string) => Promise<void>;
  setFilters: (filters: Partial<RidesFilters>) => void;
  acceptRide: (id: string) => Promise<void>;
  startRide: (id: string) => Promise<void>;
  completeRide: (id: string) => Promise<void>;
  cancelRide: (id: string, notes?: string) => Promise<void>;
}

export const useRidesStore = create<RidesState>((set, get) => ({
  rides: [],
  total: 0,
  currentRide: null,
  isLoading: false,
  filters: {
    page: 1,
    page_size: 20,
  },

  loadRides: async () => {
    set({ isLoading: true });
    try {
      const response = await fetchRides(get().filters);
      set({
        rides: response.rides,
        total: response.total,
        isLoading: false,
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to load rides';
      useUIStore.getState().addToast('error', message);
      set({ isLoading: false });
      throw error;
    }
  },

  loadRide: async (id: string) => {
    set({ isLoading: true });
    try {
      const ride = await fetchRide(id);
      set({
        currentRide: ride,
        isLoading: false,
      });
      // Also update in rides array if present
      set((state) => ({
        rides: state.rides.map((r) => (r.id === id ? ride : r)),
      }));
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to load ride';
      useUIStore.getState().addToast('error', message);
      set({ isLoading: false });
      throw error;
    }
  },

  setFilters: (newFilters: Partial<RidesFilters>) => {
    set((state) => ({
      filters: {
        ...state.filters,
        ...newFilters,
        page: newFilters.page || 1, // Reset to page 1 when filters change
      },
    }));
  },

  acceptRide: async (id: string) => {
    try {
      const ride = await acceptRideAPI(id);
      // Update ride in both places
      set((state) => ({
        currentRide: state.currentRide?.id === id ? ride : state.currentRide,
        rides: state.rides.map((r) => (r.id === id ? ride : r)),
      }));
      useUIStore.getState().addToast('success', 'Ride accepted successfully');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to accept ride';
      useUIStore.getState().addToast('error', message);
      throw error;
    }
  },

  startRide: async (id: string) => {
    try {
      const ride = await startRideAPI(id);
      // Update ride in both places
      set((state) => ({
        currentRide: state.currentRide?.id === id ? ride : state.currentRide,
        rides: state.rides.map((r) => (r.id === id ? ride : r)),
      }));
      useUIStore.getState().addToast('success', 'Ride started successfully');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to start ride';
      useUIStore.getState().addToast('error', message);
      throw error;
    }
  },

  completeRide: async (id: string) => {
    try {
      const ride = await completeRideAPI(id);
      // Update ride in both places
      set((state) => ({
        currentRide: state.currentRide?.id === id ? ride : state.currentRide,
        rides: state.rides.map((r) => (r.id === id ? ride : r)),
      }));
      useUIStore.getState().addToast('success', 'Ride completed successfully');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to complete ride';
      useUIStore.getState().addToast('error', message);
      throw error;
    }
  },

  cancelRide: async (id: string, notes?: string) => {
    try {
      const ride = await cancelRideAPI(id, notes);
      // Update ride in both places
      set((state) => ({
        currentRide: state.currentRide?.id === id ? ride : state.currentRide,
        rides: state.rides.map((r) => (r.id === id ? ride : r)),
      }));
      useUIStore.getState().addToast('success', 'Ride cancelled successfully');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to cancel ride';
      useUIStore.getState().addToast('error', message);
      throw error;
    }
  },
}));
