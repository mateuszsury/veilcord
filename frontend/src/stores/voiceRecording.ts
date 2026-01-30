/**
 * Voice recording store - manages voice message recording state.
 *
 * Handles:
 * - Starting/stopping voice recording
 * - Tracking recording duration in real-time
 * - Recording cancellation
 * - Integration with backend API
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';

interface VoiceRecordingState {
  // Recording state
  isRecording: boolean;
  duration: number; // in seconds
  recordingPath: string | null;
  error: string | null;

  // Actions
  startRecording: () => Promise<boolean>;
  stopRecording: () => Promise<{ id: string; duration: number; path: string } | null>;
  cancelRecording: () => Promise<void>;
  updateDuration: (duration: number) => void;
  reset: () => void;
}

// Duration update interval handle
let durationInterval: ReturnType<typeof setInterval> | null = null;

export const useVoiceRecording = create<VoiceRecordingState>((set, get) => ({
  isRecording: false,
  duration: 0,
  recordingPath: null,
  error: null,

  startRecording: async () => {
    try {
      set({ error: null });

      const result = await api.call((a) => a.start_voice_recording());

      if (result.error) {
        set({ error: result.error });
        return false;
      }

      set({
        isRecording: true,
        duration: 0,
        recordingPath: result.recordingPath || null,
      });

      // Start duration polling
      if (durationInterval) {
        clearInterval(durationInterval);
      }

      durationInterval = setInterval(async () => {
        if (!get().isRecording) {
          if (durationInterval) {
            clearInterval(durationInterval);
            durationInterval = null;
          }
          return;
        }

        try {
          const duration = await api.call((a) => a.get_recording_duration());
          set({ duration });
        } catch {
          // Ignore duration fetch errors
        }
      }, 100);

      return true;
    } catch (error) {
      set({ error: String(error) });
      return false;
    }
  },

  stopRecording: async () => {
    // Stop duration polling
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }

    try {
      const result = await api.call((a) => a.stop_voice_recording());

      set({
        isRecording: false,
        recordingPath: null,
      });

      if (result.error) {
        set({ error: result.error });
        return null;
      }

      if (result.id && result.duration !== undefined && result.path) {
        return {
          id: result.id,
          duration: result.duration,
          path: result.path,
        };
      }

      return null;
    } catch (error) {
      set({ isRecording: false, error: String(error) });
      return null;
    }
  },

  cancelRecording: async () => {
    // Stop duration polling
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }

    try {
      await api.call((a) => a.cancel_voice_recording());
    } catch {
      // Ignore cancellation errors
    }

    set({
      isRecording: false,
      duration: 0,
      recordingPath: null,
      error: null,
    });
  },

  updateDuration: (duration: number) => {
    set({ duration });
  },

  reset: () => {
    // Stop duration polling
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }

    set({
      isRecording: false,
      duration: 0,
      recordingPath: null,
      error: null,
    });
  },
}));
