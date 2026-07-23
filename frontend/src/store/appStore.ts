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
  StudentRegistration,
  LabView,
} from '@/types';

interface AppStore extends AppState {
  // Student registration
  student: StudentRegistration | null;
  setStudent: (student: StudentRegistration | null) => void;
  labView: LabView;
  setLabView: (view: LabView) => void;
  // Actions
  reset: () => void;
  completeModule: (moduleId: string) => void;
  // Called once on app mount to fix any stale persisted state
  rehydrate: () => void;
}

const initialState = {
  session: null,
  currentBiometricToken: null,
  knowledgePayload: null,
  isCapturingBiometrics: false,
  currentModuleIndex: 0,
  wsConnected: false,
  error: null,
  student: null,
  labView: 'register' as LabView,
};

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Student registration
        setStudent: (student: StudentRegistration | null) => set({ student }),
        setLabView: (labView: LabView) => set({ labView }),

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
            if (!state.session || !state.knowledgePayload) return state;

            const completedModules = [
              ...state.session.completed_modules,
              moduleId,
            ];

            // Don't go beyond the last module
            const totalModules = state.knowledgePayload.teaching_modules.length;
            const nextIndex = Math.min(
              state.currentModuleIndex + 1,
              totalModules - 1
            );

            return {
              session: {
                ...state.session,
                completed_modules: completedModules,
              },
              currentModuleIndex: nextIndex,
            };
          }),

        // Reset state
        reset: () => set(initialState),

        // Sanitise persisted state on app load.
        // knowledgePayload and uiComponentTree are never persisted, so if
        // labView is 'learning' after a page refresh there is nothing to show.
        // Drop back to 'topic' (or 'register' if no student) so the UI always
        // has a usable entry point.
        rehydrate: () =>
          set((state) => {
            if (
              state.labView === 'learning' ||
              state.labView === 'complete' ||
              state.labView === 'resources'
            ) {
              return { labView: state.student ? ('topic' as LabView) : ('register' as LabView) };
            }
            return {};
          }),
      }),
      {
        name: 'ephemeral-intent-storage',
        partialize: (state) => ({
          // Persist student registration only — labView is intentionally
          // excluded so the app always starts at a known, safe view.
          student: state.student,
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