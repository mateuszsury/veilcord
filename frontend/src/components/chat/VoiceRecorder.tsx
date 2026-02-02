/**
 * Voice message recorder component.
 *
 * Shows recording interface with:
 * - Pulsing red recording indicator
 * - Animated waveform visualization
 * - Duration display (M:SS.s format)
 * - Max duration warning (> 4:30)
 * - Cancel and send buttons
 */

import { useEffect } from 'react';
import { useVoiceRecording } from '@/stores/voiceRecording';
import { api } from '@/lib/pywebview';

interface VoiceRecorderProps {
  contactId: number;
  onSent: () => void;
  onCancel: () => void;
}

// Format duration as M:SS.s
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toFixed(1).padStart(4, '0')}`;
}

// SVG icon paths
const ICONS = {
  x: 'M6 18L18 6M6 6l12 12',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z',
  mic: 'M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z M19 10v2a7 7 0 01-14 0v-2 M12 19v4 M8 23h8',
};

function Icon({ path, className = 'w-5 h-5' }: { path: string; className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
    >
      <path d={path} />
    </svg>
  );
}

// Animated waveform bars
function WaveformVisualization() {
  return (
    <div className="flex items-center gap-0.5 h-8">
      {[...Array(12)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-red-400 rounded-full animate-pulse"
          style={{
            height: `${Math.random() * 60 + 20}%`,
            animationDelay: `${i * 0.1}s`,
            animationDuration: `${0.5 + Math.random() * 0.5}s`,
          }}
        />
      ))}
    </div>
  );
}

export function VoiceRecorder({ contactId, onSent, onCancel }: VoiceRecorderProps) {
  const { isRecording, duration, error, stopRecording, cancelRecording } = useVoiceRecording();

  // Max recording duration is 5 minutes
  const MAX_DURATION = 5 * 60;
  const WARNING_THRESHOLD = 4.5 * 60; // 4:30
  const isNearMax = duration >= WARNING_THRESHOLD;
  const isAtMax = duration >= MAX_DURATION;

  // Auto-stop at max duration
  useEffect(() => {
    if (isAtMax && isRecording) {
      handleSend();
    }
  }, [isAtMax, isRecording]);

  const handleCancel = async () => {
    await cancelRecording();
    onCancel();
  };

  const handleSend = async () => {
    const result = await stopRecording();
    if (result?.path) {
      // Send the recorded file
      try {
        const sendResult = await api.call((a) => a.send_file(contactId, result.path));
        if (sendResult.transferId) {
          onSent();
        } else {
          console.error('Failed to send voice message:', sendResult.error);
        }
      } catch (err) {
        console.error('Failed to send voice message:', err);
      }
    }
    onSent();
  };

  if (!isRecording) {
    return null;
  }

  return (
    <div className="flex items-center gap-3 p-3 bg-discord-bg-secondary rounded-lg border border-discord-bg-tertiary">
      {/* Recording indicator */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75" />
        </div>
        <Icon path={ICONS.mic} className="w-5 h-5 text-red-400" />
      </div>

      {/* Waveform visualization */}
      <div className="flex-1">
        <WaveformVisualization />
      </div>

      {/* Duration display */}
      <div className={`font-mono text-sm ${isNearMax ? 'text-red-400' : 'text-discord-text-primary'}`}>
        {formatDuration(duration)}
        {isNearMax && !isAtMax && (
          <span className="text-xs text-red-400 ml-1">max 5:00</span>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="text-xs text-red-400">{error}</div>
      )}

      {/* Cancel button */}
      <button
        type="button"
        onClick={handleCancel}
        className="p-2 text-discord-text-muted hover:text-discord-text-primary hover:bg-discord-bg-modifier-hover rounded-full transition-colors"
        title="Cancel recording"
      >
        <Icon path={ICONS.x} />
      </button>

      {/* Send button */}
      <button
        type="button"
        onClick={handleSend}
        disabled={duration < 0.5}
        className="p-2 bg-accent-red text-white rounded-full hover:bg-accent-red-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Send voice message"
      >
        <Icon path={ICONS.send} />
      </button>
    </div>
  );
}
