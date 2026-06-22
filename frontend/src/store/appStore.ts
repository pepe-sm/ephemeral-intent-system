/**
 * Zustand Store for Application State
 * Centralized state management for the Ephemeral Intent System
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  Session,
  SessionStatus,
  BiometricToken,
  KnowledgePayload,
  AppState,
} from '@/types';

interface AppStore extends AppState {
  // Actions
  reset: () => void;
  completeModule: (moduleId: string) => void;
}

const initialState = {
  session: null,
  currentBiometricToken: null,
  knowledgePayload: null,
  isCapturingBiometrics: false,
  currentModuleIndex: 0,
  wsConnected: false,
  error: null,
};

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Session management
        setSession: (session: Session | null) => set({ session }),
        
        updateSessionStatus: (status: SessionStatus) =>
          set((state) => ({
            session: state.session
              ? { ...state.session, status }
              : null,
          })),

        // Biometric management
        setBiometricToken: (token: BiometricToken | null) =>
          set({ currentBiometricToken: token }),

        // Knowledge management
        setKnowledgePayload: (payload: KnowledgePayload | null) =>
          set({ knowledgePayload: payload }),

        // UI state
        setIsCapturingBiometrics: (capturing: boolean) =>
          set({ isCapturingBiometrics: capturing }),

        setCurrentModuleIndex: (index: number) =>
          set({ currentModuleIndex: index }),

        // WebSocket state
        setWsConnected: (connected: boolean) =>
          set({ wsConnected: connected }),

        // Error handling
        setError: (error: string | null) => set({ error }),

        // Complete a module
        completeModule: (moduleId: string) =>
          set((state) => {
            if (!state.session) return state;

            const completedModules = [
              ...state.session.completed_modules,
              moduleId,
            ];

            return {
              session: {
                ...state.session,
                completed_modules: completedModules,
              },
              currentModuleIndex: state.currentModuleIndex + 1,
            };
          }),

        // Reset state
        reset: () => set(initialState),
      }),
      {
        name: 'ephemeral-intent-storage',
        partialize: (state) => ({
          // Only persist session data, not transient UI state
          session: state.session,
        }),
      }
    ),
    { name: 'EphemeralIntentStore' }
  )
);

// Selectors for optimized re-renders
export const selectSession = (state: AppStore) => state.session;
export const selectBiometricToken = (state: AppStore) => state.currentBiometricToken;
export const selectKnowledgePayload = (state: AppStore) => state.knowledgePayload;
export const selectIsCapturing = (state: AppStore) => state.isCapturingBiometrics;
export const selectCurrentModule = (state: AppStore) => {
  const { knowledgePayload, currentModuleIndex } = state;
  if (!knowledgePayload?.teaching_modules) return null;
  return knowledgePayload.teaching_modules[currentModuleIndex] || null;
};
export const selectWsConnected = (state: AppStore) => state.wsConnected;
export const selectError = (state: AppStore) => state.error;

// Made with Bob for IBM AI Builders Challenge