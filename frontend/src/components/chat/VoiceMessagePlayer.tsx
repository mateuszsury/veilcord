/**
 * Voice message playback component.
 *
 * Displays:
 * - Play/pause button
 * - Clickable progress bar for seeking
 * - Time display (current / total)
 *
 * Loads audio from API as base64 data URL and uses HTML Audio element.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '@/lib/pywebview';

interface VoiceMessagePlayerProps {
  fileId: number;
  filename: string;
  duration?: number; // Optional pre-known duration in seconds
}

// SVG icon paths
const ICONS = {
  play: 'M5 3l14 9-14 9V3z',
  pause: 'M6 4h4v16H6V4zm8 0h4v16h-4V4z',
  loading: 'M12 2v4m0 12v4m-7-7H1m22 0h-4m-2.636-6.364l-2.828 2.828m-5.656 5.656l-2.828 2.828m11.314 0l-2.828-2.828m-5.656-5.656L4.222 6.636',
};

function Icon({ path, className = 'w-5 h-5', spin = false }: { path: string; className?: string; spin?: boolean }) {
  return (
    <svg
      className={`${className} ${spin ? 'animate-spin' : ''}`}
      fill="currentColor"
      stroke="none"
      viewBox="0 0 24 24"
    >
      <path d={path} />
    </svg>
  );
}

// Format duration as M:SS
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function VoiceMessagePlayer({ fileId, filename: _filename, duration: propDuration }: VoiceMessagePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(propDuration || 0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  // Load audio data on first play
  const loadAudio = useCallback(async () => {
    if (audioUrl) return audioUrl;

    setIsLoading(true);
    setError(null);

    try {
      const result = await api.call((a) => a.get_file(String(fileId)));

      if (result.error) {
        setError(result.error);
        setIsLoading(false);
        return null;
      }

      if (!result.data) {
        setError('No audio data');
        setIsLoading(false);
        return null;
      }

      // Create data URL from base64
      const mimeType = result.mimeType || 'audio/ogg';
      const dataUrl = `data:${mimeType};base64,${result.data}`;
      setAudioUrl(dataUrl);
      setIsLoading(false);
      return dataUrl;
    } catch (err) {
      setError(String(err));
      setIsLoading(false);
      return null;
    }
  }, [fileId, audioUrl]);

  // Set up audio element when URL is available
  useEffect(() => {
    if (!audioUrl) return;

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration);
    });

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      setCurrentTime(0);
    });

    audio.addEventListener('error', () => {
      setError('Playback error');
      setIsPlaying(false);
    });

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, [audioUrl]);

  // Handle play/pause
  const togglePlayPause = async () => {
    if (isLoading) return;

    if (!audioUrl) {
      const url = await loadAudio();
      if (!url) return;

      // Give browser time to process data URL
      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.play();
          setIsPlaying(true);
        }
      }, 50);
      return;
    }

    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  // Handle seeking via progress bar click
  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressRef.current || duration === 0) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;

    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="flex items-center gap-2 min-w-[200px] max-w-[280px]">
      {/* Play/Pause button */}
      <button
        type="button"
        onClick={togglePlayPause}
        disabled={isLoading}
        className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full bg-accent-red/20 hover:bg-accent-red/30 text-accent-red-text transition-colors disabled:opacity-50"
        title={isPlaying ? 'Pause' : 'Play'}
      >
        {isLoading ? (
          <Icon path={ICONS.loading} spin />
        ) : isPlaying ? (
          <Icon path={ICONS.pause} />
        ) : (
          <Icon path={ICONS.play} />
        )}
      </button>

      {/* Progress and time */}
      <div className="flex-1 flex flex-col gap-1">
        {/* Progress bar */}
        <div
          ref={progressRef}
          onClick={handleProgressClick}
          className="h-2 bg-discord-bg-tertiary rounded-full cursor-pointer relative overflow-hidden"
        >
          <div
            className="absolute inset-y-0 left-0 bg-accent-red rounded-full transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Time display */}
        <div className="flex justify-between text-xs text-discord-text-muted">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Error indicator */}
      {error && (
        <div className="text-xs text-red-400" title={error}>
          !
        </div>
      )}
    </div>
  );
}
