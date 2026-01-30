/**
 * Video preview component with inline playback.
 *
 * Shows thumbnail with play button overlay. Clicking loads and plays full video inline.
 */

import { useEffect, useState } from 'react';
import { api } from '../../lib/pywebview';

interface VideoPreviewProps {
  fileId: number;
  filename: string;
  className?: string;
}

export function VideoPreview({ fileId, filename, className = '' }: VideoPreviewProps) {
  const [thumbnail, setThumbnail] = useState<string | null>(null);
  const [videoData, setVideoData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState(false);

  // Load thumbnail on mount
  useEffect(() => {
    let mounted = true;

    const loadThumbnail = async () => {
      try {
        setLoading(true);
        const response = await api.call((api) => api.get_file_preview(fileId));

        if (!mounted) return;

        if (response.error) {
          setError(response.error);
        } else if (response.preview) {
          setThumbnail(`data:${response.mimeType || 'image/jpeg'};base64,${response.preview}`);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load preview');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadThumbnail();

    return () => {
      mounted = false;
    };
  }, [fileId]);

  // Load and play video
  const handlePlayClick = async () => {
    if (videoData) {
      setIsPlaying(true);
      return;
    }

    setLoadingVideo(true);

    try {
      const response = await api.call((api) => api.get_file(String(fileId)));

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        setVideoData(`data:${response.mimeType || 'video/mp4'};base64,${response.data}`);
        setIsPlaying(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load video');
    } finally {
      setLoadingVideo(false);
    }
  };

  if (loading) {
    return (
      <div className={`inline-flex items-center justify-center w-64 h-48 bg-gray-800 rounded ${className}`}>
        <div className="text-gray-400 text-sm">Loading preview...</div>
      </div>
    );
  }

  if (error && !thumbnail) {
    return (
      <div className={`inline-flex items-center justify-center w-64 h-48 bg-gray-800 rounded ${className}`}>
        <div className="text-gray-400 text-sm">
          {error || 'Preview not available'}
        </div>
      </div>
    );
  }

  // Show video player when playing
  if (isPlaying && videoData) {
    return (
      <div className={className}>
        <video
          controls
          autoPlay
          className="max-w-md max-h-96 rounded"
          src={videoData}
        >
          Your browser does not support the video tag.
        </video>
        <div className="mt-2 text-sm text-gray-400">{filename}</div>
      </div>
    );
  }

  // Show thumbnail with play button overlay
  return (
    <div className={`relative inline-block ${className}`}>
      {thumbnail ? (
        <img
          src={thumbnail}
          alt={filename}
          className="max-w-xs max-h-64 rounded"
        />
      ) : (
        <div className="w-64 h-48 bg-gray-800 rounded flex items-center justify-center">
          <div className="text-gray-400 text-sm">Video</div>
        </div>
      )}

      {/* Play button overlay */}
      <button
        className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 hover:bg-opacity-50 transition-all rounded"
        onClick={handlePlayClick}
        disabled={loadingVideo}
      >
        {loadingVideo ? (
          <div className="text-white text-sm">Loading video...</div>
        ) : (
          <svg
            className="w-16 h-16 text-white drop-shadow-lg"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <circle cx="12" cy="12" r="10" fill="rgba(0,0,0,0.6)" />
            <path d="M9 8l7 4-7 4V8z" fill="white" />
          </svg>
        )}
      </button>

      {/* Filename */}
      <div className="mt-2 text-sm text-gray-400">{filename}</div>

      {/* Error message */}
      {error && (
        <div className="mt-1 text-xs text-red-400">{error}</div>
      )}
    </div>
  );
}
